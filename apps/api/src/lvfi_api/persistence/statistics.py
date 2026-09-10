"""Joined PostgreSQL read model for reusable historical statistics samples."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from dataclasses import replace
from typing import Any, Protocol, cast

from sqlalchemy import Integer, and_, case, func, or_, select
from sqlalchemy import cast as sql_cast
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from lvfi_api.application.statistics import StatisticsSampleRepository
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.statistics import (
    CompetitionReference,
    CompetitionReferenceRequest,
    MethodTwoSampleRequest,
    StatisticsCandidate,
    StatisticsSampleRequest,
    StatisticsTarget,
    UnavailableValue,
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


def _selection_conditions(
    target: StatisticsTarget,
    *,
    team_id: int | None,
    venue: str,
    competition_scope: str,
    season_scope: str,
    previous_season_id: int | None,
) -> list[Any]:
    """The sole APP-013 historical game selector shared by public and M2 reads."""
    conditions: list[Any] = [
        or_(
            matches.c.played_on < target.played_on,
            and_(
                matches.c.played_on == target.played_on,
                matches.c.id < target.match_id,
            ),
        )
    ]
    if team_id is not None:
        conditions.append(
            or_(matches.c.home_team_id == team_id, matches.c.away_team_id == team_id)
        )
        if venue == "home":
            conditions.append(matches.c.home_team_id == team_id)
        elif venue == "away":
            conditions.append(matches.c.away_team_id == team_id)
    if competition_scope == "target_competition":
        conditions.append(candidate_seasons.c.competition_id == target.competition_id)
    if season_scope == "current":
        conditions.append(candidate_seasons.c.label == target.season_label)
    else:
        previous_label = (
            select(seasons.c.label)
            .where(seasons.c.id == previous_season_id)
            .scalar_subquery()
        )
        conditions.append(
            candidate_seasons.c.label.in_((target.season_label, previous_label))
        )
    return conditions


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

    async def list_method_two_candidates(
        self, target: StatisticsTarget, request: MethodTwoSampleRequest
    ) -> tuple[StatisticsCandidate, ...]:
        """Select one completed, revision-resolved APP-013 series for M2."""
        production, complement = await self.list_method_two_candidate_pair(
            target,
            request,
        )
        return production if request.component == "production" else complement

    async def list_method_two_candidate_pair(
        self, target: StatisticsTarget, request: MethodTwoSampleRequest
    ) -> tuple[tuple[StatisticsCandidate, ...], tuple[StatisticsCandidate, ...]]:
        """Derive both real components after one shared APP-013 match selection."""
        rows = await self._method_two_rows(
            target,
            request.sample_size,
            request.venue,
            request.season_scope,
            request.previous_season_id,
            request.metric,
            request.team_id,
        )
        return (
            tuple(
                self._method_two_candidate(row, request.team_id, "production")
                for row in rows
            ),
            tuple(
                self._method_two_candidate(row, request.team_id, "complement")
                for row in rows
            ),
        )

    async def get_competition_reference(
        self, target: StatisticsTarget, request: CompetitionReferenceRequest
    ) -> CompetitionReference:
        """Select the bounded completed-match competition universe for M2."""
        production, complement = await self.get_competition_reference_pair(
            target,
            request,
        )
        return production if request.component == "production" else complement

    async def get_competition_reference_pair(
        self, target: StatisticsTarget, request: CompetitionReferenceRequest
    ) -> tuple[CompetitionReference, CompetitionReference]:
        """Derive both reference components after one shared APP-013 selection."""
        rows = await self._method_two_rows(
            target,
            request.sample_size,
            request.venue,
            request.season_scope,
            request.previous_season_id,
            request.metric,
            None,
        )
        return (
            self._competition_reference_from_rows(
                target, replace(request, component="production"), rows
            ),
            self._competition_reference_from_rows(
                target, replace(request, component="complement"), rows
            ),
        )

    def _competition_reference_from_rows(
        self,
        target: StatisticsTarget,
        request: CompetitionReferenceRequest,
        rows: tuple[RowMapping, ...],
    ) -> CompetitionReference:
        candidates: list[StatisticsCandidate] = []
        for row in rows:
            sides = (request.venue,) if request.venue != "overall" else ("home", "away")
            for side in sides:
                team_id = cast(int, row[f"{side}_team_id"])
                candidates.append(
                    self._method_two_candidate(row, team_id, request.component)
                )
        candidate_items = tuple(candidates)
        valid_values = tuple(
            item.value for item in candidate_items if item.value is not None
        )
        unavailable = tuple(
            UnavailableValue(item.match_id, item.unavailable_reason or "unavailable")
            for item in candidate_items
            if item.value is None
        )
        used_match_ids = tuple(
            dict.fromkeys(
                item.match_id for item in candidate_items if item.value is not None
            )
        )
        warnings: list[str] = []
        if not rows:
            warnings.append("no_candidate_matches")
        if len(rows) < request.sample_size:
            warnings.append("sample_partial")
        if unavailable:
            warnings.append("unavailable_values")
        if not valid_values:
            warnings.append("no_available_values")
        if 0 < len(valid_values) < 5:
            warnings.append("low_available_observations")
        return CompetitionReference(
            target=target,
            request=request,
            ordering="played_on_desc_match_id_asc",
            completed_predicate="match_statistics.match_id_is_not_null",
            actual_match_count=len(rows),
            candidate_match_ids=tuple(cast(int, row["match_id"]) for row in rows),
            candidates=candidate_items,
            used_match_ids=used_match_ids,
            valid_values=valid_values,
            unavailable_values=unavailable,
            available_count=len(valid_values),
            mean=sum(valid_values) / len(valid_values) if valid_values else None,
            warnings=tuple(warnings),
        )

    async def _method_two_rows(
        self,
        target: StatisticsTarget,
        sample_size: int,
        venue: str,
        season_scope: str,
        previous_season_id: int | None,
        metric: str,
        team_id: int | None,
    ) -> tuple[RowMapping, ...]:
        """One canonical M2 selector: cutoff, order, revisions and completion."""
        home_field, away_field = _fields(metric)
        fields = (home_field, away_field)
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
            .cte("method_two_latest_statistic_revisions")
        )
        revisions_by_field = {field: revisions.alias(field) for field in fields}
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
            .join(match_statistics, match_statistics.c.match_id == matches.c.id)
        )
        for field, revision in revisions_by_field.items():
            from_clause = from_clause.outerjoin(
                revision,
                and_(
                    revision.c.match_id == matches.c.id,
                    revision.c.statistic_field == field,
                    revision.c.revision_rank == 1,
                ),
            )

        def value_for(field: str) -> Any:
            revision = revisions_by_field[field]
            return case(
                (revision.c.availability == "missing", None),
                (revision.c.availability == "available", revision.c.new_value),
                else_=match_statistics.c[field],
            )

        conditions = _selection_conditions(
            target,
            team_id=team_id,
            venue=venue,
            competition_scope="target_competition",
            season_scope=season_scope,
            previous_season_id=previous_season_id,
        )
        conditions.append(match_statistics.c.match_id.is_not(None))
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
                value_for(home_field).label("home_value"),
                value_for(away_field).label("away_value"),
            )
            .select_from(from_clause)
            .where(*conditions)
            .order_by(matches.c.played_on.desc(), matches.c.id.asc())
            .limit(sample_size)
        )
        try:
            async with self._database.session() as session:
                return tuple((await session.execute(statement)).mappings().all())
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("statistics query failed") from exc

    @staticmethod
    def _method_two_candidate(
        row: RowMapping, team_id: int, component: str
    ) -> StatisticsCandidate:
        is_home = cast(int, row["home_team_id"]) == team_id
        own_side = "home" if is_home else "away"
        value_side = (
            own_side if component == "production" else ("away" if is_home else "home")
        )
        value = cast(int | None, row[f"{value_side}_value"])
        return StatisticsCandidate(
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
            venue=cast(Any, own_side),
            value=value,
            unavailable_reason="statistic_unavailable" if value is None else None,
        )

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
            if request.metric == "goals_conceded":
                own_value = case(
                    (matches.c.home_team_id == request.team_id, value_for(away_field)),
                    else_=value_for(home_field),
                )
            else:
                own_value = case(
                    (matches.c.home_team_id == request.team_id, value_for(home_field)),
                    else_=value_for(away_field),
                )
            observed_value = own_value
            unavailable_reason = case(
                (own_value.is_(None), "statistic_unavailable"), else_=None
            )

        conditions = _selection_conditions(
            target,
            team_id=request.team_id,
            venue=request.venue,
            competition_scope=request.competition_scope,
            season_scope=request.season_scope,
            previous_season_id=request.previous_season_id,
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
