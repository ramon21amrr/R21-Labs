"""SQLAlchemy Core implementation of historical read-only queries."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol, cast

from sqlalchemy import Select, func, or_, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from lvfi_api.application.historical_queries import HistoricalQueryRepository
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.historical_queries import (
    Match,
    MatchFilters,
    MatchStatistics,
    Page,
    Reference,
    Season,
    StatisticsPeriod,
    TeamStatistics,
)
from lvfi_api.persistence.historical_models import (
    competitions,
    match_statistics,
    matches,
    seasons,
    teams,
)


class SessionProvider(Protocol):
    """Minimal database boundary needed for read-only SQLAlchemy sessions."""

    def session(self) -> AbstractAsyncContextManager[AsyncSession]: ...


home_teams = teams.alias("home_teams")
away_teams = teams.alias("away_teams")


def _reference(row: RowMapping, prefix: str) -> Reference:
    return Reference(
        id=cast(int, row[f"{prefix}_id"]),
        display_name=cast(str, row[f"{prefix}_display_name"]),
        created_at=cast(Any, row[f"{prefix}_created_at"]),
    )


def _season(row: RowMapping) -> Season:
    competition = _reference(row, "competition")
    return Season(
        id=cast(int, row["season_id"]),
        competition=competition,
        label=cast(str, row["season_label"]),
        created_at=cast(Any, row["season_created_at"]),
    )


def _match(row: RowMapping) -> Match:
    return Match(
        id=cast(int, row["match_id"]),
        played_on=cast(Any, row["played_on"]),
        competition=_reference(row, "competition"),
        season=_season(row),
        home_team=_reference(row, "home_team"),
        away_team=_reference(row, "away_team"),
        has_statistics=cast(bool, row["has_statistics"]),
        created_at=cast(Any, row["match_created_at"]),
    )


def _period(row: RowMapping, side: str, period: str) -> StatisticsPeriod:
    return StatisticsPeriod(
        goals=cast(int, row[f"{side}_goals_{period}"]),
        shots=cast(int, row[f"{side}_shots_{period}"]),
        shots_on_target=cast(int, row[f"{side}_shots_on_target_{period}"]),
        corners=cast(int, row[f"{side}_corners_{period}"]),
        fouls=(
            cast(int, row[f"{side}_fouls_full_match"])
            if period == "full_match"
            else None
        ),
        cards=(
            cast(int, row[f"{side}_cards_full_match"])
            if period == "full_match"
            else None
        ),
    )


def _team_statistics(row: RowMapping, side: str) -> TeamStatistics:
    return TeamStatistics(
        first_half=_period(row, side, "first_half"),
        full_match=_period(row, side, "full_match"),
    )


def _match_select() -> Select[Any]:
    return select(
        matches.c.id.label("match_id"),
        matches.c.played_on,
        matches.c.created_at.label("match_created_at"),
        seasons.c.id.label("season_id"),
        seasons.c.label.label("season_label"),
        seasons.c.created_at.label("season_created_at"),
        competitions.c.id.label("competition_id"),
        competitions.c.display_name.label("competition_display_name"),
        competitions.c.created_at.label("competition_created_at"),
        home_teams.c.id.label("home_team_id"),
        home_teams.c.display_name.label("home_team_display_name"),
        home_teams.c.created_at.label("home_team_created_at"),
        away_teams.c.id.label("away_team_id"),
        away_teams.c.display_name.label("away_team_display_name"),
        away_teams.c.created_at.label("away_team_created_at"),
        match_statistics.c.match_id.is_not(None).label("has_statistics"),
    ).select_from(
        matches.join(seasons, matches.c.season_id == seasons.c.id)
        .join(competitions, seasons.c.competition_id == competitions.c.id)
        .join(home_teams, matches.c.home_team_id == home_teams.c.id)
        .join(away_teams, matches.c.away_team_id == away_teams.c.id)
        .outerjoin(match_statistics, match_statistics.c.match_id == matches.c.id)
    )


def _match_conditions(filters: MatchFilters) -> tuple[ColumnElement[bool], ...]:
    conditions: list[ColumnElement[bool]] = []
    if filters.competition_id is not None:
        conditions.append(seasons.c.competition_id == filters.competition_id)
    if filters.season_id is not None:
        conditions.append(matches.c.season_id == filters.season_id)
    if filters.home_team_id is not None:
        conditions.append(matches.c.home_team_id == filters.home_team_id)
    if filters.away_team_id is not None:
        conditions.append(matches.c.away_team_id == filters.away_team_id)
    if filters.team_id is not None:
        conditions.append(
            or_(
                matches.c.home_team_id == filters.team_id,
                matches.c.away_team_id == filters.team_id,
            )
        )
    if filters.date_from is not None:
        conditions.append(matches.c.played_on >= filters.date_from)
    if filters.date_to is not None:
        conditions.append(matches.c.played_on <= filters.date_to)
    return tuple(conditions)


class SqlAlchemyHistoricalQueryRepository(HistoricalQueryRepository):
    """Run bounded, joined read models without exposing persistence records."""

    def __init__(self, database: SessionProvider) -> None:
        self._database = database

    async def _page(
        self, statement: Select[Any], page: int, page_size: int, mapper: Any
    ) -> Page[Any]:
        try:
            async with self._database.session() as session:
                total = cast(
                    int,
                    await session.scalar(
                        select(func.count()).select_from(
                            statement.order_by(None).subquery()
                        )
                    ),
                )
                rows = (
                    (
                        await session.execute(
                            statement.limit(page_size).offset((page - 1) * page_size)
                        )
                    )
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("historical query failed") from exc
        return Page(tuple(mapper(row) for row in rows), page, page_size, total)

    async def list_competitions(self, page: int, page_size: int) -> Page[Reference]:
        statement = select(
            competitions.c.id.label("competition_id"),
            competitions.c.display_name.label("competition_display_name"),
            competitions.c.created_at.label("competition_created_at"),
        ).order_by(competitions.c.display_name, competitions.c.id)
        return await self._page(
            statement, page, page_size, lambda row: _reference(row, "competition")
        )

    async def get_competition(self, competition_id: int) -> Reference | None:
        statement = select(
            competitions.c.id.label("competition_id"),
            competitions.c.display_name.label("competition_display_name"),
            competitions.c.created_at.label("competition_created_at"),
        ).where(competitions.c.id == competition_id)
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("historical query failed") from exc
        return _reference(row, "competition") if row is not None else None

    async def list_seasons(
        self, competition_id: int | None, page: int, page_size: int
    ) -> Page[Season]:
        statement = (
            select(
                seasons.c.id.label("season_id"),
                seasons.c.label.label("season_label"),
                seasons.c.created_at.label("season_created_at"),
                competitions.c.id.label("competition_id"),
                competitions.c.display_name.label("competition_display_name"),
                competitions.c.created_at.label("competition_created_at"),
            )
            .select_from(
                seasons.join(
                    competitions, seasons.c.competition_id == competitions.c.id
                )
            )
            .order_by(competitions.c.display_name, seasons.c.label, seasons.c.id)
        )
        if competition_id is not None:
            statement = statement.where(seasons.c.competition_id == competition_id)
        return await self._page(statement, page, page_size, _season)

    async def get_season(self, season_id: int) -> Season | None:
        statement = (
            select(
                seasons.c.id.label("season_id"),
                seasons.c.label.label("season_label"),
                seasons.c.created_at.label("season_created_at"),
                competitions.c.id.label("competition_id"),
                competitions.c.display_name.label("competition_display_name"),
                competitions.c.created_at.label("competition_created_at"),
            )
            .select_from(
                seasons.join(
                    competitions, seasons.c.competition_id == competitions.c.id
                )
            )
            .where(seasons.c.id == season_id)
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("historical query failed") from exc
        return _season(row) if row is not None else None

    async def list_teams(
        self, name: str | None, page: int, page_size: int
    ) -> Page[Reference]:
        statement = select(
            teams.c.id.label("team_id"),
            teams.c.display_name.label("team_display_name"),
            teams.c.created_at.label("team_created_at"),
        ).order_by(teams.c.display_name, teams.c.id)
        if name is not None:
            statement = statement.where(teams.c.display_name == name)
        return await self._page(
            statement, page, page_size, lambda row: _reference(row, "team")
        )

    async def get_team(self, team_id: int) -> Reference | None:
        statement = select(
            teams.c.id.label("team_id"),
            teams.c.display_name.label("team_display_name"),
            teams.c.created_at.label("team_created_at"),
        ).where(teams.c.id == team_id)
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("historical query failed") from exc
        return _reference(row, "team") if row is not None else None

    async def list_matches(
        self, filters: MatchFilters, page: int, page_size: int
    ) -> Page[Match]:
        conditions = _match_conditions(filters)
        statement = (
            _match_select()
            .where(*conditions)
            .order_by(matches.c.played_on, matches.c.id)
        )
        return await self._page(statement, page, page_size, _match)

    async def get_match(self, match_id: int) -> Match | None:
        statement = _match_select().where(matches.c.id == match_id)
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("historical query failed") from exc
        return _match(row) if row is not None else None

    async def get_statistics(self, match_id: int) -> MatchStatistics | None:
        statement = select(match_statistics).where(
            match_statistics.c.match_id == match_id
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("historical query failed") from exc
        if row is None:
            return None
        return MatchStatistics(
            match_id=match_id,
            home=_team_statistics(row, "home"),
            away=_team_statistics(row, "away"),
        )
