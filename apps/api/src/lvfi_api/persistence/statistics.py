"""Joined PostgreSQL read model for reusable historical statistics samples."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol, cast

from sqlalchemy import Integer, and_, case, func, or_, select
from sqlalchemy import cast as sql_cast
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from lvfi_api.application.statistics import StatisticsSampleRepository
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.statistics import (
    StatisticsCandidate,
    StatisticsSampleRequest,
    StatisticsTarget,
)
from lvfi_api.persistence.historical_models import (
    competitions,
    match_statistics,
    matches,
    seasons,
    statistic_revisions,
    teams,
)


class SessionProvider(Protocol):
    def session(self) -> AbstractAsyncContextManager[AsyncSession]: ...


home_teams = teams.alias("statistics_home_teams")
away_teams = teams.alias("statistics_away_teams")
candidate_seasons = seasons.alias("statistics_candidate_seasons")
candidate_competitions = competitions.alias("statistics_candidate_competitions")


def _target(row: RowMapping) -> StatisticsTarget:
    return StatisticsTarget(
        match_id=cast(int, row["match_id"]),
        played_on=cast(Any, row["played_on"]),
        competition_id=cast(int, row["competition_id"]),
        competition_name=cast(str, row["competition_name"]),
        season_id=cast(int, row["season_id"]),
        season_label=cast(str, row["season_label"]),
        home_team_id=cast(int, row["home_team_id"]),
        home_team_name=cast(str, row["home_team_name"]),
        away_team_id=cast(int, row["away_team_id"]),
        away_team_name=cast(str, row["away_team_name"]),
    )


def _fields(metric: str) -> tuple[str, ...]:
    if metric in {"goals_scored", "goals_conceded", "result_win"}:
        return ("home_goals_full_match", "away_goals_full_match")
    field = {
        "corners": "corners_full_match",
        "shots_on_target": "shots_on_target_full_match",
        "shots": "shots_full_match",
        "cards": "cards_full_match",
        "fouls": "fouls_full_match",
    }[metric]
    return (f"home_{field}", f"away_{field}")


class SqlAlchemyStatisticsSampleRepository(StatisticsSampleRepository):
    """Select the bounded candidate set once, resolving revision values in SQL."""

    def __init__(self, database: SessionProvider) -> None:
        self._database = database

    async def get_target(self, match_id: int) -> StatisticsTarget | None:
        statement = (
            select(
                matches.c.id.label("match_id"),
                matches.c.played_on,
                seasons.c.id.label("season_id"),
                seasons.c.label.label("season_label"),
                competitions.c.id.label("competition_id"),
                competitions.c.display_name.label("competition_name"),
                home_teams.c.id.label("home_team_id"),
                home_teams.c.display_name.label("home_team_name"),
                away_teams.c.id.label("away_team_id"),
                away_teams.c.display_name.label("away_team_name"),
            )
            .select_from(
                matches.join(seasons, matches.c.season_id == seasons.c.id)
                .join(competitions, seasons.c.competition_id == competitions.c.id)
                .join(home_teams, matches.c.home_team_id == home_teams.c.id)
                .join(away_teams, matches.c.away_team_id == away_teams.c.id)
            )
            .where(matches.c.id == match_id)
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("statistics query failed") from exc
        return _target(row) if row is not None else None

    async def get_previous_season_competition(
        self, previous_season_id: int
    ) -> int | None:
        try:
            async with self._database.session() as session:
                value = await session.scalar(
                    select(seasons.c.competition_id).where(
                        seasons.c.id == previous_season_id
                    )
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("statistics query failed") from exc
        return cast(int | None, value)

    async def list_candidates(
        self, target: StatisticsTarget, request: StatisticsSampleRequest
    ) -> tuple[StatisticsCandidate, ...]:
        fields = _fields(request.metric)
        revisions = (
            select(
                statistic_revisions.c.match_id,
                statistic_revisions.c.statistic_field,
                statistic_revisions.c.availability,
                statistic_revisions.c.new_value,
                func.row_number()
                .over(
                    partition_by=(
                        statistic_revisions.c.match_id,
                        statistic_revisions.c.statistic_field,
                    ),
                    order_by=(
                        statistic_revisions.c.created_at.desc(),
                        statistic_revisions.c.id.desc(),
                    ),
                )
                .label("revision_rank"),
            )
            .where(statistic_revisions.c.statistic_field.in_(fields))
            .cte("latest_statistic_revisions")
        )
        revision_aliases = {field: revisions.alias(field) for field in fields}
        from_clause = (
            matches.join(
                candidate_seasons, matches.c.season_id == candidate_seasons.c.id
            )
            .join(
                candidate_competitions,
                candidate_seasons.c.competition_id == candidate_competitions.c.id,
            )
            .join(home_teams, matches.c.home_team_id == home_teams.c.id)
            .join(away_teams, matches.c.away_team_id == away_teams.c.id)
            .outerjoin(match_statistics, match_statistics.c.match_id == matches.c.id)
        )
        for field, revision in revision_aliases.items():
            from_clause = from_clause.outerjoin(
                revision,
                and_(
                    revision.c.match_id == matches.c.id,
                    revision.c.statistic_field == field,
                    revision.c.revision_rank == 1,
                ),
            )

        def value_for(field: str) -> Any:
            revision = revision_aliases[field]
            return case(
                (revision.c.availability == "missing", None),
                (revision.c.availability == "available", revision.c.new_value),
                else_=match_statistics.c[field],
            )

        if request.metric == "result_win":
            home_value = value_for("home_goals_full_match")
            away_value = value_for("away_goals_full_match")
            unavailable = home_value.is_(None) | away_value.is_(None)
            observed_value = case(
                (unavailable, None),
                (
                    matches.c.home_team_id == request.team_id,
                    sql_cast(home_value > away_value, Integer),
                ),
                else_=sql_cast(away_value > home_value, Integer),
            )
            unavailable_reason = case((unavailable, "goals_unavailable"), else_=None)
        else:
            home_field, away_field = fields
            own_value = case(
                (matches.c.home_team_id == request.team_id, value_for(home_field)),
                else_=value_for(away_field),
            )
            observed_value = own_value
            unavailable_reason = case(
                (own_value.is_(None), "statistic_unavailable"), else_=None
            )

        conditions = [
            or_(
                matches.c.played_on < target.played_on,
                and_(
                    matches.c.played_on == target.played_on,
                    matches.c.id < target.match_id,
                ),
            ),
            or_(
                matches.c.home_team_id == request.team_id,
                matches.c.away_team_id == request.team_id,
            ),
        ]
        if request.venue == "home":
            conditions.append(matches.c.home_team_id == request.team_id)
        elif request.venue == "away":
            conditions.append(matches.c.away_team_id == request.team_id)
        if request.competition_scope == "target_competition":
            conditions.append(
                candidate_seasons.c.competition_id == target.competition_id
            )
        if request.season_scope == "current":
            conditions.append(candidate_seasons.c.label == target.season_label)
        else:
            previous_label = (
                select(seasons.c.label)
                .where(seasons.c.id == request.previous_season_id)
                .scalar_subquery()
            )
            conditions.append(
                candidate_seasons.c.label.in_((target.season_label, previous_label))
            )
        statement = (
            select(
                matches.c.id.label("match_id"),
                matches.c.played_on,
                candidate_competitions.c.id.label("competition_id"),
                candidate_competitions.c.display_name.label("competition_name"),
                candidate_seasons.c.id.label("season_id"),
                candidate_seasons.c.label.label("season_label"),
                home_teams.c.id.label("home_team_id"),
                home_teams.c.display_name.label("home_team_name"),
                away_teams.c.id.label("away_team_id"),
                away_teams.c.display_name.label("away_team_name"),
                case(
                    (matches.c.home_team_id == request.team_id, "home"), else_="away"
                ).label("venue"),
                observed_value.label("value"),
                unavailable_reason.label("unavailable_reason"),
            )
            .select_from(from_clause)
            .where(*conditions)
            .order_by(matches.c.played_on.desc(), matches.c.id.asc())
            .limit(request.sample_size)
        )
        try:
            async with self._database.session() as session:
                rows = (await session.execute(statement)).mappings().all()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("statistics query failed") from exc
        return tuple(
            StatisticsCandidate(
                match_id=cast(int, row["match_id"]),
                played_on=cast(Any, row["played_on"]),
                competition_id=cast(int, row["competition_id"]),
                competition_name=cast(str, row["competition_name"]),
                season_id=cast(int, row["season_id"]),
                season_label=cast(str, row["season_label"]),
                home_team_id=cast(int, row["home_team_id"]),
                home_team_name=cast(str, row["home_team_name"]),
                away_team_id=cast(int, row["away_team_id"]),
                away_team_name=cast(str, row["away_team_name"]),
                venue=cast(Any, row["venue"]),
                value=cast(int | None, row["value"]),
                unavailable_reason=cast(str | None, row["unavailable_reason"]),
            )
            for row in rows
        )
