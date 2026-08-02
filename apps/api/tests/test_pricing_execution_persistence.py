"""Complete unit and HTTP coverage for auditable pricing execution persistence."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.application.pricing_execution_persistence import (
    PricingExecutionPersistenceService,
    _canonical_input,
    _sample_fingerprint,
)
from lvfi_api.domain.errors import (
    MethodOneEngineError,
    PersistenceUnavailableError,
    ResourceNotFoundError,
)
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.pricing_executions import (
    PricingExecution,
    PricingExecutionDraft,
    PricingExecutionStatus,
)
from lvfi_api.infrastructure.pricing_engine import public_method_one
from lvfi_api.main import create_app
from lvfi_api.persistence.pricing_executions import SqlAlchemyPricingExecutionRepository
from lvfi_api.presentation.pricing_execution_routes import get_pricing_execution_service

from .conftest import FakeDatabase
from .test_method_one_execution import TARGET, Provider, sample

NOW = datetime(2026, 8, 2, tzinfo=UTC)


def _record(draft: PricingExecutionDraft) -> PricingExecution:
    return PricingExecution(
        execution_id=draft.execution_id,
        match_id=draft.match_id,
        status=draft.status,
        created_at=draft.finalized_at,
        finalized_at=draft.finalized_at,
        correlation_id=draft.correlation_id,
        sample_fingerprint=draft.sample_fingerprint,
        input_fingerprint=draft.input_fingerprint,
        result_fingerprint=draft.result_fingerprint,
        pricing_engine_version=draft.pricing_engine_version,
        distribution_version=draft.distribution_version,
        method_one_version=draft.method_one_version,
        schema_version=draft.schema_version,
        public_parameters=draft.public_parameters,
        canonical_input=(
            json.loads(draft.canonical_input) if draft.canonical_input else None
        ),
        canonical_result=(
            json.loads(draft.canonical_result) if draft.canonical_result else None
        ),
        failure_code=draft.failure_code,
    )


class MemoryRepository:
    def __init__(self) -> None:
        self.records: dict[str, PricingExecution] = {}
        self.keys: dict[tuple[int, str], PricingExecution] = {}
        self.matches = {TARGET.id}

    async def get(self, execution_id: str) -> PricingExecution | None:
        return self.records.get(execution_id)

    async def get_by_idempotency_key(
        self, match_id: int, idempotency_key: str
    ) -> PricingExecution | None:
        return self.keys.get((match_id, idempotency_key))

    async def create(self, draft: PricingExecutionDraft) -> PricingExecution:
        record = _record(draft)
        self.records[record.execution_id] = record
        if draft.idempotency_key is not None:
            self.keys[(draft.match_id, draft.idempotency_key)] = record
        return record

    async def list_by_match(
        self, match_id: int, page: int, page_size: int
    ) -> Page[PricingExecution] | None:
        if match_id not in self.matches:
            return None
        items = sorted(
            (item for item in self.records.values() if item.match_id == match_id),
            key=lambda item: (item.created_at, item.execution_id),
            reverse=True,
        )
        start = (page - 1) * page_size
        return Page(
            tuple(items[start : start + page_size]), page, page_size, len(items)
        )


class BrokenEngine:
    canonical_bytes = staticmethod(public_method_one.canonical_bytes)
    sha256 = staticmethod(public_method_one.sha256)

    @staticmethod
    def run(value: object) -> object:
        return object()

    @staticmethod
    def serialize(value: object) -> object:
        return object()


class MissingProvider:
    async def get_sample(self, match_id: int) -> object:
        raise ResourceNotFoundError("match")


class BadSerializationEngine:
    canonical_bytes = staticmethod(public_method_one.canonical_bytes)
    sha256 = staticmethod(public_method_one.sha256)
    run = staticmethod(public_method_one.run)

    @staticmethod
    def serialize(value: object) -> object:
        return object()


@pytest.mark.asyncio
async def test_service_records_complete_blocked_failed_and_idempotent_outcomes() -> (
    None
):
    repository = MemoryRepository()
    service = PricingExecutionPersistenceService(Provider(sample()), repository)
    first = await service.execute(TARGET.id, "correlation-a", None)
    second = await service.execute(TARGET.id, "correlation-b", None)
    keyed = await service.execute(TARGET.id, "correlation-c", "retry-1")
    repeated = await service.execute(TARGET.id, "correlation-d", "retry-1")
    assert first.status is PricingExecutionStatus.COMPLETED
    assert first.execution_id != second.execution_id
    assert first.sample_fingerprint == second.sample_fingerprint
    assert first.input_fingerprint == second.input_fingerprint
    assert first.result_fingerprint == second.result_fingerprint
    assert first.canonical_input is not None and first.canonical_result is not None
    assert first.pricing_engine_version == "1.0.1"
    assert first.distribution_version == "1.1.1"
    assert first.method_one_version == "1.0.0"
    assert first.schema_version == 1
    assert keyed.execution_id == repeated.execution_id
    blocked = await PricingExecutionPersistenceService(
        Provider(sample(complete=False)), repository
    ).execute(TARGET.id, "correlation-e", None)
    invalid = await PricingExecutionPersistenceService(
        Provider(
            replace(
                sample(), parameters=replace(sample().parameters, requested_count=9)
            )
        ),
        repository,
    ).execute(TARGET.id, "correlation-f", None)
    failed = await PricingExecutionPersistenceService(
        Provider(sample()),
        repository,
        BrokenEngine(),  # type: ignore[arg-type]
    ).execute(TARGET.id, "correlation-g", None)
    serialization_failed = await PricingExecutionPersistenceService(
        Provider(sample()),
        repository,
        BadSerializationEngine(),  # type: ignore[arg-type]
    ).execute(TARGET.id, "correlation-h", None)
    assert blocked.status is PricingExecutionStatus.BLOCKED_SAMPLE_INCOMPLETE
    assert blocked.failure_code == "method_one_sample_incomplete"
    assert invalid.status is PricingExecutionStatus.TECHNICAL_FAILURE
    assert failed.status is PricingExecutionStatus.TECHNICAL_FAILURE
    assert failed.failure_code == "method_one_execution_failed"
    assert serialization_failed.status is PricingExecutionStatus.TECHNICAL_FAILURE
    assert (await service.get(first.execution_id)).execution_id == first.execution_id
    assert (await service.list_by_match(TARGET.id, 1, 1)).total == 7
    with pytest.raises(ResourceNotFoundError):
        await service.get("missing")
    with pytest.raises(ResourceNotFoundError):
        await service.list_by_match(999, 1, 1)


@pytest.mark.asyncio
async def test_fingerprints_are_deterministic_and_bad_engine_hash_is_typed() -> None:
    source = sample()
    assert _sample_fingerprint(source) == _sample_fingerprint(source)
    request = __import__(
        "lvfi_api.application.method_one_execution",
        fromlist=["build_method_one_request"],
    ).build_method_one_request(source)
    canonical, fingerprint = _canonical_input(request, public_method_one)
    assert canonical.startswith("{") and len(fingerprint) == 64


class _BadHashEngine:
    canonical_bytes = staticmethod(lambda value: object())
    sha256 = staticmethod(lambda value: object())


@pytest.mark.asyncio
async def test_canonical_input_rejects_nonpublic_values() -> None:
    request = __import__(
        "lvfi_api.application.method_one_execution",
        fromlist=["build_method_one_request"],
    ).build_method_one_request(sample())
    with pytest.raises(MethodOneEngineError):
        _canonical_input(request, _BadHashEngine())  # type: ignore[arg-type]


def _row(*, payloads: bool = True) -> dict[str, Any]:
    return {
        "execution_id": "c4f8bf4e-5995-4c01-a85f-403218ce0101",
        "match_id": TARGET.id,
        "status": "completed" if payloads else "technical_failure",
        "created_at": NOW,
        "finalized_at": NOW,
        "correlation_id": "test",
        "idempotency_key": "key",
        "sample_fingerprint": "1" * 64,
        "input_fingerprint": "2" * 64 if payloads else None,
        "result_fingerprint": "3" * 64 if payloads else None,
        "pricing_engine_version": "1.1.1",
        "distribution_version": "1.1.1",
        "method_one_version": "1.0.0",
        "schema_version": 1,
        "public_parameters": {"requested_count": 10},
        "canonical_input": "{}" if payloads else None,
        "canonical_result": "{}" if payloads else None,
        "failure_code": None if payloads else "method_one_execution_failed",
    }


class Result:
    def __init__(
        self, row: dict[str, Any] | None, rows: list[dict[str, Any]] | None = None
    ) -> None:
        self.row = row
        self.rows = rows if rows is not None else ([] if row is None else [row])

    def mappings(self) -> Result:
        return self

    def one_or_none(self) -> dict[str, Any] | None:
        return self.row

    def one(self) -> dict[str, Any]:
        assert self.row is not None
        return self.row

    def all(self) -> list[dict[str, Any]]:
        return self.rows


class Session:
    def __init__(
        self,
        rows: list[dict[str, Any] | None] = (),
        scalars: list[int | None] = (),
        fail: bool = False,
    ) -> None:
        self.rows = list(rows)
        self.scalars = list(scalars)
        self.fail = fail
        self.execute_calls = 0

    async def execute(self, statement: object) -> Result:
        self.execute_calls += 1
        if self.fail:
            raise SQLAlchemyError("synthetic")
        row = self.rows.pop(0) if self.rows else None
        return Result(row)

    async def scalar(self, statement: object) -> int | None:
        if self.fail:
            raise SQLAlchemyError("synthetic")
        return self.scalars.pop(0)


class Database:
    def __init__(self, session: Session) -> None:
        self.value = session

    @asynccontextmanager
    async def session(self) -> Any:
        yield self.value


def _draft() -> PricingExecutionDraft:
    return PricingExecutionDraft(
        execution_id="c4f8bf4e-5995-4c01-a85f-403218ce0101",
        match_id=TARGET.id,
        status=PricingExecutionStatus.COMPLETED,
        finalized_at=NOW,
        correlation_id="test",
        idempotency_key="key",
        sample_fingerprint="1" * 64,
        input_fingerprint="2" * 64,
        result_fingerprint="3" * 64,
        pricing_engine_version="1.1.1",
        distribution_version="1.1.1",
        method_one_version="1.0.0",
        schema_version=1,
        public_parameters={"requested_count": 10},
        canonical_input="{}",
        canonical_result="{}",
        failure_code=None,
    )


@pytest.mark.asyncio
async def test_sqlalchemy_repository_operations() -> None:
    row = _row()
    assert (
        await SqlAlchemyPricingExecutionRepository(Database(Session([row]))).get("x")
    ) is not None  # type: ignore[arg-type]
    assert (
        await SqlAlchemyPricingExecutionRepository(Database(Session([None]))).get("x")
        is None
    )  # type: ignore[arg-type]
    assert (
        await SqlAlchemyPricingExecutionRepository(
            Database(Session([row]))
        ).get_by_idempotency_key(TARGET.id, "key")
        is not None
    )  # type: ignore[arg-type]
    assert (
        await SqlAlchemyPricingExecutionRepository(
            Database(Session([None]))
        ).get_by_idempotency_key(TARGET.id, "key")
        is None
    )  # type: ignore[arg-type]
    assert (
        await SqlAlchemyPricingExecutionRepository(Database(Session([row]))).create(
            _draft()
        )
    ).execution_id == row["execution_id"]  # type: ignore[arg-type]
    assert (
        await SqlAlchemyPricingExecutionRepository(
            Database(Session([None, row]))
        ).create(_draft())
    ).execution_id == row["execution_id"]  # type: ignore[arg-type]
    list_session = Session([row], [TARGET.id, 1])
    page = await SqlAlchemyPricingExecutionRepository(
        Database(list_session)
    ).list_by_match(TARGET.id, 1, 10)  # type: ignore[arg-type]
    assert page is not None and page.total == 1 and list_session.execute_calls == 1
    assert (
        await SqlAlchemyPricingExecutionRepository(
            Database(Session([], [None]))
        ).list_by_match(TARGET.id, 1, 10)
        is None
    )  # type: ignore[arg-type]
    for operation in (
        SqlAlchemyPricingExecutionRepository(Database(Session(fail=True))).get("x"),  # type: ignore[arg-type]
        SqlAlchemyPricingExecutionRepository(
            Database(Session(fail=True))
        ).get_by_idempotency_key(TARGET.id, "x"),  # type: ignore[arg-type]
        SqlAlchemyPricingExecutionRepository(Database(Session(fail=True))).create(
            _draft()
        ),  # type: ignore[arg-type]
        SqlAlchemyPricingExecutionRepository(
            Database(Session(fail=True))
        ).list_by_match(TARGET.id, 1, 1),  # type: ignore[arg-type]
    ):
        with pytest.raises(PersistenceUnavailableError):
            await operation
    assert _row(payloads=False)["canonical_input"] is None


def test_http_resource_openapi_and_sanitized_absence(settings: Any) -> None:
    repository = MemoryRepository()
    app = create_app(settings, FakeDatabase())
    app.state.pricing_execution_service = PricingExecutionPersistenceService(
        Provider(sample()), repository
    )
    with TestClient(app) as client:
        created = client.post(
            f"/matches/{TARGET.id}/method-one/pricing-executions",
            headers={"X-Request-ID": "execution-http", "Idempotency-Key": "http-1"},
        )
        execution_id = created.json()["execution_id"]
        fetched = client.get(f"/pricing-executions/{execution_id}")
        listed = client.get(
            f"/matches/{TARGET.id}/method-one/pricing-executions?page=1&page_size=1"
        )
        paths = client.get("/openapi.json").json()["paths"]
    assert created.status_code == 201
    assert fetched.status_code == listed.status_code == 200
    assert created.headers["X-Request-ID"] == "execution-http"
    assert listed.json()["total"] == 1
    assert "/pricing-executions/{execution_id}" in paths
    assert "source_sha256" not in created.text and "source_line" not in created.text
    with TestClient(create_app(settings, FakeDatabase())) as client:
        assert client.get("/pricing-executions/" + "0" * 36).status_code == 503
    missing_app = create_app(settings, FakeDatabase())
    missing_app.state.pricing_execution_service = PricingExecutionPersistenceService(
        MissingProvider(),
        repository,  # type: ignore[arg-type]
    )
    with TestClient(missing_app) as client:
        assert (
            client.post("/matches/999/method-one/pricing-executions").status_code == 404
        )
        assert client.get("/pricing-executions/" + "0" * 36).status_code == 404
        assert (
            client.get("/matches/999/method-one/pricing-executions").status_code == 404
        )


@pytest.mark.asyncio
async def test_route_dependency_composes_the_real_repository_when_available() -> None:
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                database=Database(Session([_row()])),
                method_one_sample_service=Provider(sample()),
            )
        )
    )
    service = await get_pricing_execution_service(request)  # type: ignore[arg-type]
    assert isinstance(service, PricingExecutionPersistenceService)


@pytest.mark.asyncio
async def test_postgresql_institutional_append_only_trigger() -> None:
    """Exercise the migration trigger against the disposable institutional database."""
    import os

    from sqlalchemy import delete, insert, update
    from sqlalchemy.exc import DBAPIError
    from sqlalchemy.ext.asyncio import create_async_engine

    database_url = os.environ.get("LVFI_DATABASE_URL")
    if database_url is None or "127.0.0.1:55432" not in database_url:
        pytest.skip("requires the isolated Codex PostgreSQL task database")
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as connection:
            from lvfi_api.persistence.historical_models import (
                competitions,
                import_batches,
                matches,
                seasons,
                source_records,
                teams,
            )
            from lvfi_api.persistence.historical_models import (
                pricing_executions as execution_table,
            )

            await connection.execute(
                insert(import_batches).values(
                    id=1,
                    source_filename="synthetic",
                    source_sha256="0" * 64,
                    sheet_name="synthetic",
                    status="completed",
                )
            )
            await connection.execute(
                insert(source_records).values(
                    id=1,
                    batch_id=1,
                    source_line=1,
                    row_sha256="0" * 64,
                    raw_values={},
                    status="accepted",
                )
            )
            await connection.execute(
                insert(competitions).values(
                    id=1, display_name="Synthetic", normalized_name="synthetic"
                )
            )
            await connection.execute(
                insert(seasons).values(id=1, competition_id=1, label="2026")
            )
            await connection.execute(
                insert(teams).values(id=1, display_name="Home", normalized_name="home")
            )
            await connection.execute(
                insert(teams).values(id=2, display_name="Away", normalized_name="away")
            )
            await connection.execute(
                insert(matches).values(
                    id=1,
                    season_id=1,
                    played_on=date(2026, 8, 2),
                    home_team_id=1,
                    away_team_id=2,
                    source_record_id=1,
                )
            )
            await connection.execute(
                insert(execution_table).values(
                    execution_id="c4f8bf4e-5995-4c01-a85f-403218ce0101",
                    match_id=1,
                    status="completed",
                    finalized_at=NOW,
                    correlation_id="postgres",
                    sample_fingerprint="1" * 64,
                    input_fingerprint="2" * 64,
                    result_fingerprint="3" * 64,
                    pricing_engine_version="1.1.1",
                    distribution_version="1.1.1",
                    method_one_version="1.0.0",
                    schema_version=1,
                    public_parameters={},
                    canonical_input="{}",
                    canonical_result="{}",
                )
            )
        with pytest.raises(DBAPIError):
            async with engine.begin() as connection:
                await connection.execute(
                    update(execution_table)
                    .where(
                        execution_table.c.execution_id
                        == "c4f8bf4e-5995-4c01-a85f-403218ce0101"
                    )
                    .values(correlation_id="mutated")
                )
        with pytest.raises(DBAPIError):
            async with engine.begin() as connection:
                await connection.execute(
                    delete(execution_table).where(
                        execution_table.c.execution_id
                        == "c4f8bf4e-5995-4c01-a85f-403218ce0101"
                    )
                )
    finally:
        await engine.dispose()
