"""PostgreSQL repository for the APP-014 immutable configuration ledger."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime
from typing import Any, Protocol, cast

from sqlalchemy import and_, func, insert, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from lvfi_api.domain.configuration import (
    CATALOG_ID,
    ConfigurationCatalog,
    ConfigurationRevision,
    ConfigurationRevisionDraft,
    EffectiveConfiguration,
    catalog_payload,
    configuration_hash,
)
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.persistence.historical_models import (
    competitions,
    configuration_catalogs,
    configuration_revisions,
    matches,
    seasons,
)


class SessionProvider(Protocol):
    def session(self) -> AbstractAsyncContextManager[AsyncSession]: ...


def _revision(row: Any) -> ConfigurationRevision:
    return ConfigurationRevision(
        revision_id=cast(int, row["id"]),
        catalog_id=cast(str, row["catalog_id"]),
        catalog_hash=cast(str, row["catalog_hash"]),
        scope=cast(Any, row["scope"]),
        parameter_code=cast(str, row["parameter_code"]),
        value=row["value"],
        competition_id=cast(int | None, row["competition_id"]),
        match_id=cast(int | None, row["match_id"]),
        actor=cast(str, row["actor"]),
        reason=cast(str, row["reason"]),
        replaces_revision_id=cast(int | None, row["replaces_revision_id"]),
        revision_hash=cast(str, row["revision_hash"]),
        created_at=cast(datetime, row["created_at"]),
    )


def _scope_predicate(draft: ConfigurationRevisionDraft) -> Any:
    if draft.scope == "global":
        return and_(
            configuration_revisions.c.competition_id.is_(None),
            configuration_revisions.c.match_id.is_(None),
        )
    if draft.scope == "competition":
        return configuration_revisions.c.competition_id == draft.competition_id
    return configuration_revisions.c.match_id == draft.match_id


def _chain_key(draft: ConfigurationRevisionDraft) -> str:
    """Identify one append-only chain independently of unrelated revisions."""
    target = "global"
    if draft.scope == "competition":
        target = f"competition:{draft.competition_id}"
    elif draft.scope == "match":
        target = f"match:{draft.match_id}"
    return "|".join((draft.catalog_id, draft.parameter_code, draft.scope, target))


class SqlAlchemyConfigurationRepository:
    """Keep configuration selection independent of every pricing execution path."""

    def __init__(self, database: SessionProvider) -> None:
        self._database = database

    async def get_catalog(self) -> ConfigurationCatalog | None:
        try:
            async with self._database.session() as session:
                row = (
                    await session.execute(
                        select(configuration_catalogs).where(
                            configuration_catalogs.c.catalog_id == CATALOG_ID
                        )
                    )
                ).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "configuration catalog unavailable"
            ) from exc
        if row is None:
            return None
        return ConfigurationCatalog(
            catalog_id=cast(str, row["catalog_id"]),
            schema_version=cast(int, row["schema_version"]),
            payload=cast(dict[str, object], row["payload"]),
            content_hash=cast(str, row["content_hash"]),
            created_at=cast(datetime, row["created_at"]),
        )

    async def create_revision(
        self, draft: ConfigurationRevisionDraft
    ) -> ConfigurationRevision | None:
        try:
            async with self._database.session() as session:
                if draft.scope == "competition":
                    exists = await session.scalar(
                        select(competitions.c.id).where(
                            competitions.c.id == draft.competition_id
                        )
                    )
                elif draft.scope == "match":
                    exists = await session.scalar(
                        select(matches.c.id).where(matches.c.id == draft.match_id)
                    )
                else:
                    exists = 1
                if exists is None:
                    return None
                await session.execute(
                    select(
                        func.pg_advisory_xact_lock(
                            func.hashtextextended(_chain_key(draft), 0)
                        )
                    )
                )
                created_at = datetime.now(UTC)
                previous = await session.scalar(
                    select(configuration_revisions.c.id)
                    .where(
                        configuration_revisions.c.catalog_id == draft.catalog_id,
                        configuration_revisions.c.scope == draft.scope,
                        configuration_revisions.c.parameter_code
                        == draft.parameter_code,
                        _scope_predicate(draft),
                    )
                    .order_by(
                        configuration_revisions.c.created_at.desc(),
                        configuration_revisions.c.id.desc(),
                    )
                    .limit(1)
                    .with_for_update()
                )
                hash_payload = {
                    "catalog_id": draft.catalog_id,
                    "catalog_hash": configuration_hash(catalog_payload()),
                    "scope": draft.scope,
                    "parameter_code": draft.parameter_code,
                    "value": draft.value,
                    "competition_id": draft.competition_id,
                    "match_id": draft.match_id,
                    "actor": draft.actor.strip(),
                    "reason": draft.reason.strip(),
                    "replaces_revision_id": previous,
                    "created_at": created_at.isoformat(),
                }
                payload = {**hash_payload, "created_at": created_at}
                row = (
                    (
                        await session.execute(
                            insert(configuration_revisions)
                            .values(
                                **payload,
                                revision_hash=configuration_hash(hash_payload),
                            )
                            .returning(configuration_revisions)
                        )
                    )
                    .mappings()
                    .one()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "configuration revision write failed"
            ) from exc
        return _revision(row)

    async def get_history(
        self,
        parameter_code: str | None,
        scope: str | None,
        competition_id: int | None,
        match_id: int | None,
    ) -> tuple[ConfigurationRevision, ...]:
        clauses: list[Any] = []
        if parameter_code is not None:
            clauses.append(configuration_revisions.c.parameter_code == parameter_code)
        if scope is not None:
            clauses.append(configuration_revisions.c.scope == scope)
        if competition_id is not None:
            clauses.append(configuration_revisions.c.competition_id == competition_id)
        if match_id is not None:
            clauses.append(configuration_revisions.c.match_id == match_id)
        try:
            async with self._database.session() as session:
                rows = (
                    await session.execute(
                        select(configuration_revisions)
                        .where(*clauses)
                        .order_by(
                            configuration_revisions.c.created_at.desc(),
                            configuration_revisions.c.id.desc(),
                        )
                    )
                ).mappings().all()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "configuration history unavailable"
            ) from exc
        return tuple(_revision(row) for row in rows)

    async def effective(self, match_id: int) -> EffectiveConfiguration | None:
        try:
            async with self._database.session() as session:
                target = (
                    await session.execute(
                        select(matches.c.id, seasons.c.competition_id)
                        .join(seasons, seasons.c.id == matches.c.season_id)
                        .where(matches.c.id == match_id)
                    )
                ).mappings().one_or_none()
                if target is None:
                    return None
                catalog = (
                    await session.execute(
                        select(configuration_catalogs).where(
                            configuration_catalogs.c.catalog_id == CATALOG_ID
                        )
                    )
                ).mappings().one_or_none()
                if catalog is None:
                    return None
                competition_id = cast(int, target["competition_id"])
                rows = (
                    await session.execute(
                        select(configuration_revisions)
                        .where(
                            configuration_revisions.c.catalog_id == CATALOG_ID,
                            or_(
                                configuration_revisions.c.scope == "global",
                                and_(
                                    configuration_revisions.c.scope == "competition",
                                    configuration_revisions.c.competition_id
                                    == competition_id,
                                ),
                                and_(
                                    configuration_revisions.c.scope == "match",
                                    configuration_revisions.c.match_id == match_id,
                                ),
                            ),
                        )
                        .order_by(
                            configuration_revisions.c.parameter_code,
                            configuration_revisions.c.created_at.desc(),
                            configuration_revisions.c.id.desc(),
                        )
                    )
                ).mappings().all()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "effective configuration unavailable"
            ) from exc

        candidates = tuple(_revision(row) for row in rows)
        priority = {"match": 0, "competition": 1, "global": 2}
        selected: list[ConfigurationRevision] = []
        discarded: list[ConfigurationRevision] = []
        seen: set[str] = set()
        for candidate in sorted(
            candidates,
            key=lambda value: (
                value.parameter_code,
                priority[value.scope],
                -value.created_at.timestamp(),
                -value.revision_id,
            ),
        ):
            if candidate.parameter_code in seen:
                discarded.append(candidate)
            else:
                selected.append(candidate)
                seen.add(candidate.parameter_code)
        selected.sort(key=lambda value: value.parameter_code)
        discarded.sort(key=lambda value: value.revision_id)
        values = {item.parameter_code: item.value for item in selected}
        catalog_hash = cast(str, catalog["content_hash"])
        effective_hash = configuration_hash(
            {
                "catalog_id": CATALOG_ID,
                "catalog_hash": catalog_hash,
                "match_id": match_id,
                "competition_id": competition_id,
                "selected_revisions": [
                    {
                        "parameter_code": item.parameter_code,
                        "revision_id": item.revision_id,
                        "catalog_hash": item.catalog_hash,
                        "revision_hash": item.revision_hash,
                        "scope": item.scope,
                        "value": item.value,
                    }
                    for item in selected
                ],
            }
        )
        return EffectiveConfiguration(
            match_id=match_id,
            competition_id=competition_id,
            catalog_id=CATALOG_ID,
            catalog_hash=catalog_hash,
            values=values,
            selected_revisions=tuple(selected),
            discarded_revisions=tuple(discarded),
            effective_hash=effective_hash,
        )
