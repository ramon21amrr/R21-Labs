"""Transactional PostgreSQL writes for manual matches and revisions."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any, cast

from sqlalchemy import insert, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.operational_data import (
    FutureMatch,
    FutureMatchDraft,
    StatisticRevision,
    StatisticRevisionDraft,
)
from lvfi_api.historical_import import normalized_key
from lvfi_api.persistence.historical_models import (
    competitions,
    match_statistics,
    matches,
    seasons,
    statistic_revisions,
    teams,
)


class SessionProvider:
    def session(self) -> AbstractAsyncContextManager[AsyncSession]: ...


class SqlAlchemyOperationalDataRepository:
    """Keep write transactions isolated from public read and pricing boundaries."""

    def __init__(self, database: SessionProvider) -> None:
        self._database = database

    async def _reference_id(self, session: AsyncSession, table: Any, name: str) -> int:
        key = normalized_key(name)
        existing = await session.scalar(
            select(table.c.id).where(table.c.normalized_name == key)
        )
        if existing is not None:
            return int(existing)
        return int(
            (
                await session.execute(
                    insert(table)
                    .values(display_name=name.strip(), normalized_name=key)
                    .returning(table.c.id)
                )
            ).scalar_one()
        )

    async def _season_id(
        self, session: AsyncSession, competition_id: int, label: str
    ) -> int:
        existing = await session.scalar(
            select(seasons.c.id).where(
                seasons.c.competition_id == competition_id,
                seasons.c.label == label.strip(),
            )
        )
        if existing is not None:
            return int(existing)
        return int(
            (
                await session.execute(
                    insert(seasons)
                    .values(competition_id=competition_id, label=label.strip())
                    .returning(seasons.c.id)
                )
            ).scalar_one()
        )

    async def create_future_match(self, draft: FutureMatchDraft) -> FutureMatch | None:
        try:
            async with self._database.session() as session:
                competition_id = await self._reference_id(
                    session, competitions, draft.competition
                )
                season_id = await self._season_id(session, competition_id, draft.season)
                home_team_id = await self._reference_id(session, teams, draft.home_team)
                away_team_id = await self._reference_id(session, teams, draft.away_team)
                existing = await session.scalar(
                    select(matches.c.id).where(
                        matches.c.season_id == season_id,
                        matches.c.played_on == draft.played_on,
                        matches.c.home_team_id == home_team_id,
                        matches.c.away_team_id == away_team_id,
                    )
                )
                if existing is not None:
                    return None
                row = (
                    (
                        await session.execute(
                            insert(matches)
                            .values(
                                season_id=season_id,
                                played_on=draft.played_on,
                                home_team_id=home_team_id,
                                away_team_id=away_team_id,
                                source_record_id=None,
                            )
                            .returning(matches)
                        )
                    )
                    .mappings()
                    .one()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("operational match write failed") from exc
        return FutureMatch(
            match_id=cast(int, row["id"]),
            played_on=draft.played_on,
            competition=draft.competition.strip(),
            season=draft.season.strip(),
            home_team=draft.home_team.strip(),
            away_team=draft.away_team.strip(),
            actor=draft.actor.strip(),
            created_at=cast(Any, row["created_at"]),
        )

    async def revise_statistic(
        self, draft: StatisticRevisionDraft
    ) -> StatisticRevision | None:
        column = match_statistics.c[draft.statistic_field]
        try:
            async with self._database.session() as session:
                previous = await session.scalar(
                    select(column).where(match_statistics.c.match_id == draft.match_id)
                )
                if previous is None:
                    return None
                row = (
                    (
                        await session.execute(
                            insert(statistic_revisions)
                            .values(
                                match_id=draft.match_id,
                                statistic_field=draft.statistic_field,
                                previous_value=previous,
                                new_value=draft.new_value,
                                availability=draft.availability,
                                source="manual_correction",
                                actor=draft.actor.strip(),
                                reason=draft.reason.strip(),
                            )
                            .returning(statistic_revisions)
                        )
                    )
                    .mappings()
                    .one()
                )
                if draft.availability == "available":
                    await session.execute(
                        update(match_statistics)
                        .where(match_statistics.c.match_id == draft.match_id)
                        .values({draft.statistic_field: draft.new_value})
                    )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "statistic revision write failed"
            ) from exc
        return StatisticRevision(
            revision_id=cast(int, row["id"]),
            match_id=draft.match_id,
            statistic_field=draft.statistic_field,
            previous_value=cast(int, row["previous_value"]),
            availability=cast(Any, row["availability"]),
            new_value=cast(int | None, row["new_value"]),
            actor=cast(str, row["actor"]),
            reason=cast(str, row["reason"]),
            created_at=cast(Any, row["created_at"]),
        )
