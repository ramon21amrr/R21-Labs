"""Unit and repository coverage for the APP-014 configuration ledger."""
# ruff: noqa: E501

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import insert, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine

from lvfi_api.application.configuration import ConfigurationService
from lvfi_api.config import Settings
from lvfi_api.domain.configuration import (
    CATALOG_ID,
    ConfigurationCatalog,
    ConfigurationRevision,
    ConfigurationRevisionDraft,
    catalog_payload,
    configuration_hash,
    valid_revision_draft,
)
from lvfi_api.domain.errors import (
    InvalidQueryError,
    PersistenceUnavailableError,
    ResourceNotFoundError,
)
from lvfi_api.infrastructure.database import Database
from lvfi_api.main import create_app
from lvfi_api.persistence.configuration import SqlAlchemyConfigurationRepository
from lvfi_api.persistence.historical_models import (
    competitions,
    configuration_catalogs,
    matches,
    seasons,
    teams,
)
from lvfi_api.presentation.configuration_routes import get_configuration_service

NOW = datetime(2026, 9, 10, tzinfo=UTC)


class _Result:
    def __init__(self, value: dict[str, object] | list[dict[str, object]] | None) -> None:
        self.value = value

    def mappings(self) -> _Result:
        return self

    def one_or_none(self) -> dict[str, object] | None:
        return self.value if isinstance(self.value, dict) else None

    def one(self) -> dict[str, object]:
        assert isinstance(self.value, dict)
        return self.value

    def all(self) -> list[dict[str, object]]:
        return self.value if isinstance(self.value, list) else []


class _Session:
    def __init__(
        self,
        scalars: list[int | None] | None = None,
        results: list[dict[str, object] | list[dict[str, object]] | None] | None = None,
        fail: bool = False,
    ) -> None:
        self.scalars = list(scalars or [])
        self.results = list(results or [])
        self.fail = fail

    async def scalar(self, _: object) -> int | None:
        if self.fail:
            raise SQLAlchemyError("synthetic")
        return self.scalars.pop(0)

    async def execute(self, _: object) -> _Result:
        if self.fail:
            raise SQLAlchemyError("synthetic")
        return _Result(self.results.pop(0) if self.results else None)


class _Database:
    def __init__(self, session: _Session) -> None:
        self.value = session

    @asynccontextmanager
    async def session(self) -> Any:
        yield self.value


def _catalog_row() -> dict[str, object]:
    payload = catalog_payload()
    return {
        "catalog_id": CATALOG_ID,
        "schema_version": 1,
        "payload": payload,
        "content_hash": configuration_hash(payload),
        "created_at": NOW,
    }


def _revision_row(
    revision_id: int = 1,
    scope: str = "global",
    parameter_code: str = "sample_size",
    value: object = 10,
    competition_id: int | None = None,
    match_id: int | None = None,
) -> dict[str, object]:
    return {
        "id": revision_id,
        "catalog_id": CATALOG_ID,
        "catalog_hash": configuration_hash(catalog_payload()),
        "scope": scope,
        "parameter_code": parameter_code,
        "value": value,
        "competition_id": competition_id,
        "match_id": match_id,
        "actor": "local-admin",
        "reason": "verified",
        "replaces_revision_id": None,
        "revision_hash": f"{revision_id:064d}",
        "created_at": NOW,
    }


def _draft(
    scope: str = "global", competition_id: int | None = None, match_id: int | None = None
) -> ConfigurationRevisionDraft:
    return ConfigurationRevisionDraft(
        catalog_id=CATALOG_ID,
        scope=scope,  # type: ignore[arg-type]
        parameter_code="sample_size",
        value=10,
        competition_id=competition_id,
        match_id=match_id,
        actor="local-admin",
        reason="verified",
    )


@pytest.mark.parametrize(
    ("draft", "expected"),
    [
        (_draft(), True),
        (_draft("competition", competition_id=3), True),
        (_draft("match", match_id=7), True),
        (_draft("competition"), False),
        (_draft("match"), False),
        (_draft("global", competition_id=3), False),
        (
            ConfigurationRevisionDraft(
                CATALOG_ID, "global", "sample_size", True, None, None, "actor", "reason"
            ),
            False,
        ),
        (
            ConfigurationRevisionDraft(
                CATALOG_ID, "global", "unknown", 10, None, None, "actor", "reason"
            ),
            False,
        ),
    ],
)
def test_configuration_catalog_hash_and_draft_validation(
    draft: ConfigurationRevisionDraft, expected: bool
) -> None:
    payload = catalog_payload()
    assert configuration_hash(payload) == configuration_hash(payload)
    assert payload["statistical_lines"] == {
        "handicap_line_quarters": list(range(-12, 13)),
        "total_line_quarters": list(range(1, 25)),
    }
    assert valid_revision_draft(draft) is expected


class _MemoryRepository:
    def __init__(self, catalog: ConfigurationCatalog | None = None) -> None:
        self.catalog = catalog
        self.revision = ConfigurationRevision(
            1, CATALOG_ID, configuration_hash(catalog_payload()), "global", "sample_size", 10, None, None,
            "actor", "reason", None, "a" * 64, NOW
        )

    async def get_catalog(self) -> ConfigurationCatalog | None:
        return self.catalog

    async def create_revision(
        self, draft: ConfigurationRevisionDraft
    ) -> ConfigurationRevision | None:
        return self.revision if draft.reason == "verified" else None

    async def get_history(self, *_: object) -> tuple[ConfigurationRevision, ...]:
        return (self.revision,)

    async def effective(self, match_id: int) -> object | None:
        return self.revision if match_id == 1 else None


@pytest.mark.asyncio
async def test_configuration_service_validates_boundaries() -> None:
    catalog = ConfigurationCatalog(CATALOG_ID, 1, catalog_payload(), "b" * 64, NOW)
    service = ConfigurationService(_MemoryRepository(catalog))
    assert await service.get_catalog() == catalog
    assert (await service.create_revision(_draft())).revision_id == 1
    assert await service.get_history(None, None, None, None)
    assert await service.effective(1)
    with pytest.raises(InvalidQueryError):
        await service.create_revision(_draft("competition"))
    with pytest.raises(InvalidQueryError):
        await service.get_history(None, "other", None, None)
    with pytest.raises(InvalidQueryError):
        await service.get_history(None, None, 0, None)
    with pytest.raises(InvalidQueryError):
        await service.get_history(None, None, None, 0)
    with pytest.raises(InvalidQueryError):
        await service.effective(0)
    with pytest.raises(ResourceNotFoundError):
        await ConfigurationService(_MemoryRepository()).get_catalog()
    with pytest.raises(ResourceNotFoundError):
        await service.create_revision(
            ConfigurationRevisionDraft(CATALOG_ID, "global", "sample_size", 10, None, None, "actor", "other")
        )
    with pytest.raises(ResourceNotFoundError):
        await service.effective(2)


@pytest.mark.asyncio
async def test_configuration_repository_reads_writes_history_and_resolves_precedence() -> None:
    catalog = _catalog_row()
    assert (await SqlAlchemyConfigurationRepository(_Database(_Session(results=[catalog]))).get_catalog()).catalog_id == CATALOG_ID  # type: ignore[union-attr]
    assert await SqlAlchemyConfigurationRepository(_Database(_Session(results=[None]))).get_catalog() is None

    created = await SqlAlchemyConfigurationRepository(
        _Database(_Session(scalars=[1], results=[None, _revision_row(2)]))
    ).create_revision(_draft())
    assert created is not None and created.revision_id == 2
    assert await SqlAlchemyConfigurationRepository(
        _Database(_Session(scalars=[None]))
    ).create_revision(_draft("competition", competition_id=3)) is None
    assert await SqlAlchemyConfigurationRepository(
        _Database(_Session(scalars=[1, None], results=[None, _revision_row(3, "competition", competition_id=3)]))
    ).create_revision(_draft("competition", competition_id=3))
    assert await SqlAlchemyConfigurationRepository(
        _Database(_Session(scalars=[1, None], results=[None, _revision_row(4, "match", match_id=7)]))
    ).create_revision(_draft("match", match_id=7))

    history = await SqlAlchemyConfigurationRepository(
        _Database(_Session(results=[[_revision_row(1)]]))
    ).get_history("sample_size", "global", 3, 7)
    assert history[0].parameter_code == "sample_size"

    resolved = await SqlAlchemyConfigurationRepository(
        _Database(
            _Session(
                results=[
                    {"id": 7, "competition_id": 3},
                    catalog,
                    [
                        _revision_row(1, "global", value=5),
                        _revision_row(2, "competition", value=10, competition_id=3),
                        _revision_row(3, "match", value=15, match_id=7),
                    ],
                ]
            )
        )
    ).effective(7)
    assert resolved is not None
    assert resolved.values == {"sample_size": 15}
    assert [value.scope for value in resolved.selected_revisions] == ["match"]
    assert [value.scope for value in resolved.discarded_revisions] == ["global", "competition"]
    assert resolved.effective_hash == (await SqlAlchemyConfigurationRepository(
        _Database(_Session(results=[{"id": 7, "competition_id": 3}, catalog, [_revision_row(3, "match", value=15, match_id=7)]]))
    ).effective(7)).effective_hash  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_configuration_repository_and_dependency_handle_unavailable_states() -> None:
    failing = SqlAlchemyConfigurationRepository(_Database(_Session(fail=True)))
    for operation in (
        failing.get_catalog(), failing.create_revision(_draft()), failing.get_history(None, None, None, None), failing.effective(1)
    ):
        with pytest.raises(PersistenceUnavailableError):
            await operation
    assert await SqlAlchemyConfigurationRepository(
        _Database(_Session(results=[None]))
    ).effective(1) is None
    assert await SqlAlchemyConfigurationRepository(
        _Database(_Session(results=[{"id": 1, "competition_id": 3}, None]))
    ).effective(1) is None
    available = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(database=_Database(_Session()))))
    assert isinstance(await get_configuration_service(available), ConfigurationService)  # type: ignore[arg-type]
    injected = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(configuration_service="injected")))
    assert await get_configuration_service(injected) == "injected"  # type: ignore[arg-type]
    with pytest.raises(PersistenceUnavailableError):
        await get_configuration_service(SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(database=object()))))  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_postgresql_configuration_ledger_is_append_only_and_resolves_precedence() -> None:
    database_url = os.environ.get("LVFI_DATABASE_URL")
    if database_url is None or "127.0.0.1:55432" not in database_url:
        pytest.skip("requires the isolated Codex PostgreSQL task database")

    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                insert(competitions).values(
                    id=1401,
                    display_name="Configuration League",
                    normalized_name="configuration-league",
                )
            )
            await connection.execute(
                insert(seasons).values(id=1401, competition_id=1401, label="2026")
            )
            await connection.execute(
                insert(teams),
                [
                    {"id": 1401, "display_name": "Configuration Home", "normalized_name": "configuration-home"},
                    {"id": 1402, "display_name": "Configuration Away", "normalized_name": "configuration-away"},
                ],
            )
            await connection.execute(
                insert(matches).values(
                    id=1401,
                    season_id=1401,
                    played_on=date(2026, 9, 10),
                    home_team_id=1401,
                    away_team_id=1402,
                )
            )

        settings = Settings(
            environment="test",
            app_name="lvfi-postgresql-configuration-test",
            database_url=database_url,
        )
        database = Database(settings)
        app = create_app(settings, database)
        with TestClient(app) as client:
            catalog = client.get("/configuration-catalogs/lvfi-mvp/1.0.0")
            global_revision = client.post(
                "/administration/configuration-revisions",
                json={"catalog_id": CATALOG_ID, "scope": "global", "parameter_code": "sample_size", "value": 5, "reason": "global baseline"},
            )
            competition_revision = client.post(
                "/administration/configuration-revisions",
                json={"catalog_id": CATALOG_ID, "scope": "competition", "parameter_code": "sample_size", "value": 10, "competition_id": 1401, "reason": "competition baseline"},
            )
            match_revision = client.post(
                "/administration/configuration-revisions",
                json={"catalog_id": CATALOG_ID, "scope": "match", "parameter_code": "sample_size", "value": 15, "match_id": 1401, "reason": "match setting"},
            )
            first = client.get("/matches/1401/configuration/effective")
            second = client.get("/matches/1401/configuration/effective")

        assert catalog.status_code == 200
        assert all(response.status_code == 201 for response in (global_revision, competition_revision, match_revision))
        assert first.json()["values"] == {"sample_size": 15}
        assert first.json()["effective_hash"] == second.json()["effective_hash"]
        assert [item["scope"] for item in first.json()["selected_revisions"]] == ["match"]
        assert {item["scope"] for item in first.json()["discarded_revisions"]} == {"global", "competition"}
        with pytest.raises(SQLAlchemyError, match="append-only"):
            async with engine.begin() as connection:
                await connection.execute(
                    update(configuration_catalogs)
                    .where(configuration_catalogs.c.catalog_id == CATALOG_ID)
                    .values(content_hash="0" * 64)
                )

        concurrent_database = Database(settings)
        await concurrent_database.start()
        try:
            concurrent_repository = SqlAlchemyConfigurationRepository(concurrent_database)
            revisions = await asyncio.gather(
                *(
                    concurrent_repository.create_revision(
                        ConfigurationRevisionDraft(
                            catalog_id=CATALOG_ID,
                            scope="global",
                            parameter_code="venue",
                            value="overall",
                            competition_id=None,
                            match_id=None,
                            actor="local-admin",
                            reason=f"concurrent chain {index}",
                        )
                    )
                    for index in range(8)
                )
            )
            assert all(revision is not None for revision in revisions)
            history = await concurrent_repository.get_history(
                "venue", "global", None, None
            )
            assert len(history) == 8
            assert sum(revision.replaces_revision_id is None for revision in history) == 1
            assert all(
                history[index].replaces_revision_id == history[index + 1].revision_id
                for index in range(len(history) - 1)
            )
        finally:
            await concurrent_database.stop()
    finally:
        await engine.dispose()
