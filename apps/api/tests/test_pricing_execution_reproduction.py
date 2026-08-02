"""Focused complete coverage for controlled APP-009 reproduction."""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.application.pricing_execution_persistence import (
    PricingExecutionPersistenceService,
)
from lvfi_api.application.pricing_execution_reproduction import (
    PricingExecutionReproductionService,
    _decode,
    _differences,
    decode_canonical_request,
)
from lvfi_api.domain.errors import PersistenceUnavailableError, ResourceNotFoundError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.pricing_execution_reproductions import (
    PricingExecutionReproduction,
    PricingExecutionReproductionDraft,
    PricingExecutionReproductionOutcome,
)
from lvfi_api.domain.pricing_executions import PricingExecution, PricingExecutionStatus
from lvfi_api.infrastructure.pricing_engine import public_method_one
from lvfi_api.main import create_app
from lvfi_api.persistence.pricing_execution_reproductions import (
    SqlAlchemyPricingExecutionReproductionRepository,
)

from .conftest import FakeDatabase
from .test_method_one_execution import TARGET, Provider, sample
from .test_pricing_execution_persistence import MemoryRepository

NOW = datetime(2026, 8, 2, tzinfo=UTC)


class Reproductions:
    def __init__(self) -> None:
        self.records: dict[str, PricingExecutionReproduction] = {}

    async def create(
        self, draft: PricingExecutionReproductionDraft
    ) -> PricingExecutionReproduction:
        record = PricingExecutionReproduction(
            draft.reproduction_id,
            draft.execution_id,
            draft.outcome,
            draft.finalized_at,
            draft.finalized_at,
            draft.correlation_id,
            draft.original_input_fingerprint,
            draft.reproduced_input_fingerprint,
            draft.original_result_fingerprint,
            draft.reproduced_result_fingerprint,
            draft.original_pricing_engine_version,
            draft.current_pricing_engine_version,
            draft.original_distribution_version,
            draft.current_distribution_version,
            draft.original_method_one_version,
            draft.current_method_one_version,
            draft.original_schema_version,
            draft.current_schema_version,
            draft.differences,
            draft.failure_code,
        )
        self.records[record.reproduction_id] = record
        return record

    async def get(self, reproduction_id: str) -> PricingExecutionReproduction | None:
        return self.records.get(reproduction_id)

    async def list_by_execution(
        self, execution_id: str, page: int, page_size: int
    ) -> Page[PricingExecutionReproduction]:
        values = sorted(
            (
                item
                for item in self.records.values()
                if item.execution_id == execution_id
            ),
            key=lambda item: (item.created_at, item.reproduction_id),
            reverse=True,
        )
        start = (page - 1) * page_size
        return Page(
            tuple(values[start : start + page_size]), page, page_size, len(values)
        )


class BrokenEngine:
    canonical_bytes = staticmethod(public_method_one.canonical_bytes)
    sha256 = staticmethod(public_method_one.sha256)
    run = staticmethod(lambda value: object())
    serialize = staticmethod(lambda value: object())


async def _original() -> tuple[MemoryRepository, PricingExecution]:
    origins = MemoryRepository()
    result = await PricingExecutionPersistenceService(
        Provider(sample()), origins
    ).execute(TARGET.id, "origin", None)
    return origins, result


@pytest.mark.asyncio
async def test_reproduction_outcomes_are_immutable_and_do_not_requery_samples() -> None:
    origins, original = await _original()
    reproductions = Reproductions()
    service = PricingExecutionReproductionService(origins, reproductions)
    exact = await service.reproduce(original.execution_id, "exact")
    repeated = await service.reproduce(original.execution_id, "exact-repeat")
    assert exact.outcome is PricingExecutionReproductionOutcome.EXACT_MATCH
    assert repeated.outcome is PricingExecutionReproductionOutcome.EXACT_MATCH
    assert exact.reproduction_id != repeated.reproduction_id
    assert exact.reproduced_input_fingerprint == original.input_fingerprint
    assert exact.reproduced_result_fingerprint == original.result_fingerprint
    assert original == origins.records[original.execution_id]
    mismatch_origin = replace(original, result_fingerprint="0" * 64)
    origins.records[original.execution_id] = mismatch_origin
    mismatch = await service.reproduce(original.execution_id, "mismatch")
    assert mismatch.outcome is PricingExecutionReproductionOutcome.MISMATCH
    assert mismatch.differences == tuple(
        sorted(mismatch.differences, key=lambda x: x["path"])
    )
    incompatible = replace(mismatch_origin, schema_version=2)
    origins.records[original.execution_id] = incompatible
    blocked_version = await service.reproduce(original.execution_id, "version")
    assert (
        blocked_version.outcome
        is PricingExecutionReproductionOutcome.INCOMPATIBLE_VERSION
    )
    assert blocked_version.failure_code == "incompatible_version"
    origins.records[original.execution_id] = replace(
        original,
        status=PricingExecutionStatus.TECHNICAL_FAILURE,
        canonical_input=None,
        canonical_result=None,
        input_fingerprint=None,
        result_fingerprint=None,
        failure_code="method_one_execution_failed",
    )
    blocked = await service.reproduce(original.execution_id, "blocked")
    assert blocked.outcome is PricingExecutionReproductionOutcome.BLOCKED
    origins.records[original.execution_id] = original
    technical = await PricingExecutionReproductionService(
        origins,
        reproductions,
        BrokenEngine(),  # type: ignore[arg-type]
    ).reproduce(original.execution_id, "failure")
    assert technical.outcome is PricingExecutionReproductionOutcome.TECHNICAL_FAILURE
    with pytest.raises(ResourceNotFoundError):
        await service.reproduce("missing", "missing")


@pytest.mark.asyncio
async def test_reproduction_query_contracts_and_http(settings: Any) -> None:
    origins, original = await _original()
    reproductions = Reproductions()
    service = PricingExecutionReproductionService(origins, reproductions)
    created = await service.reproduce(original.execution_id, "correlation-reproduction")
    assert (
        await service.get(created.reproduction_id)
    ).correlation_id == "correlation-reproduction"
    assert (await service.list_by_execution(original.execution_id, 1, 1)).total == 1
    with pytest.raises(ResourceNotFoundError):
        await service.get("missing")
    with pytest.raises(ResourceNotFoundError):
        await service.list_by_execution("missing", 1, 1)
    app = create_app(settings, FakeDatabase())
    app.state.pricing_execution_reproduction_service = service
    with TestClient(app) as client:
        response = client.post(
            f"/pricing-executions/{original.execution_id}/reproductions",
            headers={"X-Request-ID": "http-reproduction"},
        )
        reproduction_id = response.json()["reproduction_id"]
        fetched = client.get(f"/pricing-execution-reproductions/{reproduction_id}")
        listed = client.get(
            f"/pricing-executions/{original.execution_id}/reproductions"
        )
        paths = client.get("/openapi.json").json()["paths"]
    assert (
        response.status_code == 201
        and response.headers["X-Request-ID"] == "http-reproduction"
    )
    assert fetched.status_code == listed.status_code == 200
    assert "/pricing-executions/{execution_id}/reproductions" in paths
    assert "source_line" not in response.text and "stack" not in response.text


def test_canonical_decoder_and_differences_are_strict_and_deterministic() -> None:
    import asyncio

    origins, original = asyncio.run(_original())
    assert origins.records[original.execution_id].canonical_input is not None
    assert decode_canonical_request(original.canonical_input).match_id == str(TARGET.id)
    assert _differences("x", {"b": 2, "a": [1]}, {"b": 3, "a": [1, 2]}) == (
        {"path": "x.a[1]", "original": None, "reproduced": 2},
        {"path": "x.b", "original": 2, "reproduced": 3},
    )
    for invalid in (
        {},
        {"type": "Float", "value": "nope"},
        {"type": "Enum", "enum": "x", "value": "x"},
    ):
        with pytest.raises((ValueError, TypeError)):
            decode_canonical_request(invalid)


class Result:
    def __init__(
        self, row: dict[str, Any] | None, rows: list[dict[str, Any]] | None = None
    ) -> None:
        self.row = row
        self.rows = rows if rows is not None else ([] if row is None else [row])

    def mappings(self) -> Result:
        return self

    def one(self) -> dict[str, Any]:
        assert self.row is not None
        return self.row

    def one_or_none(self) -> dict[str, Any] | None:
        return self.row

    def all(self) -> list[dict[str, Any]]:
        return self.rows


class Session:
    def __init__(
        self,
        rows: list[dict[str, Any] | None] = (),
        scalars: list[int] = (),
        fail: bool = False,
    ) -> None:
        self.rows, self.scalars, self.fail = list(rows), list(scalars), fail

    async def execute(self, statement: object) -> Result:
        if self.fail:
            raise SQLAlchemyError("synthetic")
        return Result(self.rows.pop(0) if self.rows else None)

    async def scalar(self, statement: object) -> int:
        if self.fail:
            raise SQLAlchemyError("synthetic")
        return self.scalars.pop(0)


class Database:
    def __init__(self, session: Session) -> None:
        self.value = session

    @asynccontextmanager
    async def session(self) -> Any:
        yield self.value


def _row() -> dict[str, Any]:
    return {
        "reproduction_id": "c4f8bf4e-5995-4c01-a85f-403218ce0102",
        "execution_id": "c4f8bf4e-5995-4c01-a85f-403218ce0101",
        "outcome": "exact_match",
        "created_at": NOW,
        "finalized_at": NOW,
        "correlation_id": "test",
        "original_input_fingerprint": "1" * 64,
        "reproduced_input_fingerprint": "1" * 64,
        "original_result_fingerprint": "2" * 64,
        "reproduced_result_fingerprint": "2" * 64,
        "original_pricing_engine_version": "1.0.1",
        "current_pricing_engine_version": "1.0.1",
        "original_distribution_version": "1.1.1",
        "current_distribution_version": "1.1.1",
        "original_method_one_version": "1.0.0",
        "current_method_one_version": "1.0.0",
        "original_schema_version": 1,
        "current_schema_version": 1,
        "differences": [],
        "failure_code": None,
    }


@pytest.mark.asyncio
async def test_sqlalchemy_reproduction_repository_success_absence_and_errors() -> None:
    row = _row()
    draft = PricingExecutionReproductionDraft(
        *(row[name] for name in PricingExecutionReproductionDraft.__dataclass_fields__)
    )
    repository = SqlAlchemyPricingExecutionReproductionRepository(
        Database(Session([row]))
    )  # type: ignore[arg-type]
    assert (await repository.create(draft)).reproduction_id == row["reproduction_id"]
    assert (
        await SqlAlchemyPricingExecutionReproductionRepository(
            Database(Session([row]))
        ).get("x")
    ) is not None  # type: ignore[arg-type]
    assert (
        await SqlAlchemyPricingExecutionReproductionRepository(
            Database(Session([None]))
        ).get("x")
        is None
    )  # type: ignore[arg-type]
    page = await SqlAlchemyPricingExecutionReproductionRepository(
        Database(Session([row], [1]))
    ).list_by_execution("x", 1, 10)  # type: ignore[arg-type]
    assert page.total == 1 and page.items[0].reproduction_id == row["reproduction_id"]
    for action in (
        SqlAlchemyPricingExecutionReproductionRepository(
            Database(Session(fail=True))
        ).create(draft),  # type: ignore[arg-type]
        SqlAlchemyPricingExecutionReproductionRepository(
            Database(Session(fail=True))
        ).get("x"),  # type: ignore[arg-type]
        SqlAlchemyPricingExecutionReproductionRepository(
            Database(Session(fail=True))
        ).list_by_execution("x", 1, 1),  # type: ignore[arg-type]
    ):
        with pytest.raises(PersistenceUnavailableError):
            await action


@pytest.mark.asyncio
async def test_reproduction_blocks_bad_input_and_detects_input_fingerprint() -> None:
    origins, original = await _original()
    reproductions = Reproductions()
    origins.records[original.execution_id] = replace(original, canonical_input={})
    invalid = await PricingExecutionReproductionService(
        origins, reproductions
    ).reproduce(original.execution_id, "invalid-input")
    assert invalid.failure_code == "canonical_input_invalid"
    origins.records[original.execution_id] = original

    class DifferentHash:
        canonical_bytes = staticmethod(public_method_one.canonical_bytes)
        sha256 = staticmethod(lambda value: "0" * 64)
        run = staticmethod(public_method_one.run)
        serialize = staticmethod(public_method_one.serialize)

    mismatch = await PricingExecutionReproductionService(
        origins, reproductions, DifferentHash()
    ).reproduce(original.execution_id, "input-mismatch")
    assert mismatch.failure_code == "input_fingerprint_mismatch"


def test_decoder_covers_canonical_envelopes_and_rejects_unsafe_values() -> None:
    assert _decode([{"type": "Float", "value": "0x1.0000000000000p+0"}]) == [1.0]
    assert _decode({"type": "DateTime", "value": "2026-08-02T00:00:00+00:00"}).tzinfo
    assert _decode({"type": "Tuple", "items": [1, 2]}) == (1, 2)
    assert _decode({"type": "Mapping", "items": [["x", 1]]}) == {"x": 1}
    assert (
        _decode({"type": "Enum", "enum": "MatchState", "value": "completed"}).value
        == "completed"
    )
    for value in (
        {"type": "DateTime", "value": "2026-08-02T00:00:00"},
        {"type": "Enum", "enum": "unknown", "value": "x"},
        {"type": "Missing", "fields": {}, "schema_version": 1},
    ):
        with pytest.raises(ValueError):
            _decode(value)


@pytest.mark.asyncio
async def test_reproduction_engine_envelope_failures_and_route_composition() -> None:
    origins, original = await _original()
    reproductions = Reproductions()

    class InvalidInputBoundary:
        canonical_bytes = staticmethod(lambda value: object())
        sha256 = staticmethod(lambda value: object())
        run = staticmethod(public_method_one.run)
        serialize = staticmethod(public_method_one.serialize)

    blocked = await PricingExecutionReproductionService(
        origins, reproductions, InvalidInputBoundary()
    ).reproduce(original.execution_id, "bad-boundary")
    assert blocked.failure_code == "canonical_input_invalid"

    class InvalidResultBoundary:
        canonical_bytes = staticmethod(public_method_one.canonical_bytes)
        sha256 = staticmethod(public_method_one.sha256)
        run = staticmethod(public_method_one.run)
        serialize = staticmethod(lambda value: object())

    failed = await PricingExecutionReproductionService(
        origins, reproductions, InvalidResultBoundary()
    ).reproduce(original.execution_id, "bad-result")
    assert failed.failure_code == "method_one_reproduction_failed"

    from lvfi_api.presentation.pricing_execution_reproduction_routes import (
        get_reproduction_service,
    )

    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(database=Database(Session())))
    )
    assert isinstance(
        await get_reproduction_service(request), PricingExecutionReproductionService
    )
    with pytest.raises(PersistenceUnavailableError):
        await get_reproduction_service(
            SimpleNamespace(
                app=SimpleNamespace(state=SimpleNamespace(database=object()))
            )
        )


def test_decoder_rejects_malformed_known_and_nonstring_type() -> None:
    for value in (
        {"type": "Float", "value": "0x1.0p+0", "extra": 1},
        {"type": None, "fields": {}, "schema_version": 1},
    ):
        with pytest.raises(ValueError):
            _decode(value)


def test_decoder_rejects_nonrequest_root_and_non_dataclass_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="canonical root"):
        decode_canonical_request({"type": "Float", "value": "0x1.0000000000000p+0"})
    import lvfi_api.application.pricing_execution_reproduction as subject

    monkeypatch.setitem(subject._TYPE_REGISTRY, "Synthetic", lambda: object())
    with pytest.raises(ValueError, match="canonical instance"):
        _decode({"type": "Synthetic", "fields": {}, "schema_version": 1})
