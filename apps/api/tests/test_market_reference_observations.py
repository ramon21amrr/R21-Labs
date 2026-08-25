"""APP-011 contracts: immutable external references and deterministic comparisons."""
# ruff: noqa: E501

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.application.market_reference_observations import (
    MarketReferenceObservationService,
    _float_value,
    _quote,
)
from lvfi_api.domain.errors import MarketReferenceValidationError, ResourceNotFoundError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.market_pricings import MarketPricing
from lvfi_api.domain.market_reference_observations import (
    MarketReferenceObservation,
    MarketReferenceObservationDraft,
)
from lvfi_api.main import create_app
from lvfi_api.persistence.market_reference_observations import (
    SqlAlchemyMarketReferenceRepository,
)
from lvfi_api.presentation.market_reference_routes import get_market_reference_service

from .conftest import FakeDatabase

NOW = datetime(2026, 8, 25, 12, tzinfo=UTC)
SNAPSHOT_ID = "c4f8bf4e-5995-4c01-a85f-403218ce0101"


def _fair_odds(selection: str, value: str) -> dict[str, object]:
    return {
        "fields": {
            "selection": {"value": selection},
            "fair_odds": {"fields": {"value": {"value": value}}},
        }
    }


def _snapshot(match_id: int = 101) -> MarketPricing:
    requests = [
        {"code": "asian_handicap", "selection": "home", "line_quarters": -1},
        {"code": "asian_handicap", "selection": "away", "line_quarters": 0},
        {"code": "asian_total", "selection": "over", "line_quarters": 9},
        {"code": "total_goals", "line_half_units": 5, "selection": None},
        {"code": "three_way_result", "selection": None},
    ]
    results = [
        {"fields": {"selection": {"value": "home"}, "fair_odds": {"fields": {"value": {"value": "0x1.0p+1"}}}}},
        {"fields": {"selection": {"value": "away"}, "fair_odds": {"fields": {"value": {"value": "0x1.2p+1"}}}}},
        {"fields": {"selection": {"value": "over"}, "fair_odds": {"fields": {"value": {"value": "0x1.4p+1"}}}}},
        {"fields": {"selections": {"items": [_fair_odds("over", "0x1.8p+0"), _fair_odds("under", "0x1.ap+0")]}}},
        {"fields": {"selections": {"items": [_fair_odds("home", "0x1.cp+0"), _fair_odds("draw", "0x1.0p+1"), _fair_odds("away", "0x1.2p+1")]}}},
    ]
    return MarketPricing(
        market_pricing_id=SNAPSHOT_ID,
        match_id=match_id,
        created_at=NOW,
        finalized_at=NOW,
        correlation_id="snapshot-correlation",
        source_model_version="1.0.0",
        source_execution_id=None,
        rate_snapshot_schema_version=1,
        rates_fingerprint="1" * 64,
        pricing_engine_version="1.0.1",
        schema_version=1,
        input_fingerprint="2" * 64,
        result_fingerprint="3" * 64,
        engine_result_fingerprint="4" * 64,
        canonical_input={"markets": requests},
        canonical_result={"engine_result": {"content": {"fields": {"market_results": {"items": results}}}}},
    )


class MemoryRepository:
    def __init__(self) -> None:
        self.snapshot = _snapshot()
        self.values: dict[str, MarketReferenceObservation] = {}
        self.keys: dict[tuple[int, str], MarketReferenceObservation] = {}
        self.matches = {101}

    async def get_snapshot(self, market_pricing_id: str) -> MarketPricing | None:
        return self.snapshot if market_pricing_id == self.snapshot.market_pricing_id else None

    async def get(self, observation_id: str) -> MarketReferenceObservation | None:
        return self.values.get(observation_id)

    async def get_by_idempotency_key(self, match_id: int, idempotency_key: str) -> MarketReferenceObservation | None:
        return self.keys.get((match_id, idempotency_key))

    async def create(self, draft: MarketReferenceObservationDraft) -> MarketReferenceObservation:
        value = MarketReferenceObservation(
            **{name: getattr(draft, name) for name in MarketReferenceObservation.__dataclass_fields__ if name != "created_at"},
            created_at=NOW,
        )
        self.values[value.observation_id] = value
        if draft.idempotency_key is not None:
            self.keys[(draft.match_id, draft.idempotency_key)] = value
        return value

    async def list_by_match_snapshot(self, match_id: int, market_pricing_id: str, page: int, page_size: int) -> Page[MarketReferenceObservation] | None:
        if match_id not in self.matches:
            return None
        items = sorted(
            (item for item in self.values.values() if item.match_id == match_id and item.market_pricing_id == market_pricing_id),
            key=lambda item: (item.observed_at, item.observation_id),
            reverse=True,
        )
        return Page(tuple(items[(page - 1) * page_size : page * page_size]), page, page_size, len(items))


class MissingSnapshotRepository(MemoryRepository):
    async def get_snapshot(self, market_pricing_id: str) -> MarketPricing | None:
        return None


async def _create(service: MarketReferenceObservationService, **overrides: object) -> MarketReferenceObservation:
    values: dict[str, object] = {
        "match_id": 101,
        "market_pricing_id": SNAPSHOT_ID,
        "market_code": "asian_handicap",
        "selection": "home",
        "model_line_quarters": -1,
        "reference_line_quarters": 0,
        "reference_value": 2.05,
        "observed_at": NOW,
        "correlation_id": "reference-correlation",
        "idempotency_key": None,
    }
    values.update(overrides)
    return await service.create(**values)  # type: ignore[arg-type]


def _observation_row() -> dict[str, object]:
    return {
        "observation_id": "c4f8bf4e-5995-4c01-a85f-403218ce0301",
        "match_id": 101,
        "market_pricing_id": SNAPSHOT_ID,
        "market_code": "asian_handicap",
        "selection": "home",
        "model_line_quarters": -1,
        "reference_line_quarters": 0,
        "reference_value": 2.05,
        "observed_at": NOW,
        "created_at": NOW,
        "correlation_id": "row-correlation",
    }


def _snapshot_row() -> dict[str, object]:
    value = _snapshot()
    return {
        "market_pricing_id": value.market_pricing_id, "match_id": value.match_id,
        "created_at": NOW, "finalized_at": NOW, "correlation_id": "snapshot",
        "source_model_version": "1.0.0", "source_execution_id": None,
        "rate_snapshot_schema_version": 1, "rates_fingerprint": "1" * 64,
        "pricing_engine_version": "1.0.1", "schema_version": 1,
        "input_fingerprint": "2" * 64, "result_fingerprint": "3" * 64,
        "engine_result_fingerprint": "4" * 64,
        "canonical_input": json.dumps(value.canonical_input),
        "canonical_result": json.dumps(value.canonical_result),
    }


class Result:
    def __init__(self, row: dict[str, object] | None, rows: list[dict[str, object]] | None = None) -> None:
        self.row = row
        self.rows = rows if rows is not None else ([] if row is None else [row])

    def mappings(self) -> "Result": return self
    def one_or_none(self) -> dict[str, object] | None: return self.row
    def one(self) -> dict[str, object]:
        assert self.row is not None
        return self.row
    def all(self) -> list[dict[str, object]]: return self.rows


class Session:
    def __init__(self, rows: list[dict[str, object] | None] = [], scalars: list[int | None] = [], fail: bool = False) -> None:
        self.rows, self.scalars, self.fail = list(rows), list(scalars), fail

    async def execute(self, statement: object) -> Result:
        if self.fail: raise SQLAlchemyError("synthetic")
        return Result(self.rows.pop(0) if self.rows else None)

    async def scalar(self, statement: object) -> int | None:
        if self.fail: raise SQLAlchemyError("synthetic")
        return self.scalars.pop(0)


class Database:
    def __init__(self, session: Session) -> None: self.value = session
    @asynccontextmanager
    async def session(self) -> Any: yield self.value


@pytest.mark.asyncio
async def test_asian_and_total_line_comparisons_preserve_orientation_and_quarters() -> None:
    service = MarketReferenceObservationService(MemoryRepository())
    handicap = await _create(service, reference_line_quarters=-2)
    assert (await service.compare(handicap.observation_id)).line_difference_quarters == -1
    zero = await _create(service, selection="away", model_line_quarters=0, reference_line_quarters=0)
    assert (await service.compare(zero.observation_id)).line_difference_quarters == 0
    total = await _create(
        service,
        market_code="total_goals",
        selection="over",
        model_line_quarters=10,
        reference_line_quarters=13,
    )
    comparison = await service.compare(total.observation_id)
    assert comparison.model_value == 1.5 and comparison.line_difference_quarters == 3
    asian_total = await _create(
        service,
        market_code="asian_total",
        selection="over",
        model_line_quarters=9,
        reference_line_quarters=10,
    )
    assert (await service.compare(asian_total.observation_id)).model_value == 2.5


@pytest.mark.asyncio
async def test_non_line_markets_are_side_by_side_and_invalid_links_are_rejected() -> None:
    service = MarketReferenceObservationService(MemoryRepository())
    three_way = await _create(
        service,
        market_code="three_way_result",
        selection="draw",
        model_line_quarters=None,
        reference_line_quarters=None,
    )
    comparison = await service.compare(three_way.observation_id)
    assert comparison.model_value == 2 and comparison.line_difference_quarters is None
    for overrides in (
        {"market_pricing_id": "missing"},
        {"match_id": 404},
        {"selection": "wrong"},
        {"reference_line_quarters": None},
        {"reference_value": 0},
        {"observed_at": NOW.replace(tzinfo=None)},
    ):
        with pytest.raises((MarketReferenceValidationError, ResourceNotFoundError)):
            await _create(service, **overrides)


@pytest.mark.asyncio
async def test_history_is_append_only_idempotent_and_deterministically_paged() -> None:
    repository = MemoryRepository()
    service = MarketReferenceObservationService(repository)
    first = await _create(service, idempotency_key="retry", observed_at=NOW)
    repeated = await _create(service, idempotency_key="retry", observed_at=NOW + timedelta(hours=1))
    later = await _create(service, observed_at=NOW + timedelta(hours=2))
    assert first.observation_id == repeated.observation_id
    assert first.reference_line_quarters == 0
    page = await service.list_by_match_snapshot(101, SNAPSHOT_ID, 1, 1)
    assert page.total == 2 and page.items == (later,)
    with pytest.raises(ResourceNotFoundError):
        await service.get("missing")
    with pytest.raises(ResourceNotFoundError):
        await service.list_by_match_snapshot(404, SNAPSHOT_ID, 1, 1)


def test_http_contract_is_sanitized_correlated_and_documented(settings: object) -> None:
    repository = MemoryRepository()
    app = create_app(settings, FakeDatabase())  # type: ignore[arg-type]
    app.state.market_reference_service = MarketReferenceObservationService(repository)
    body = {
        "market_pricing_id": SNAPSHOT_ID,
        "market_code": "asian_handicap",
        "selection": "home",
        "model_line_quarters": -1,
        "reference_line_quarters": 0,
        "reference_value": 2.05,
        "observed_at": NOW.isoformat(),
    }
    with TestClient(app) as client:
        created = client.post("/matches/101/market-references", json=body, headers={"X-Request-ID": "reference-http", "Idempotency-Key": "http-retry"})
        observation_id = created.json()["observation_id"]
        repeated = client.post("/matches/101/market-references", json=body, headers={"Idempotency-Key": "http-retry"})
        comparison = client.get(f"/market-references/{observation_id}/comparison")
        fetched = client.get(f"/market-references/{observation_id}")
        history = client.get(f"/matches/101/market-pricings/{SNAPSHOT_ID}/market-references")
        invalid = client.post("/matches/101/market-references", json={**body, "selection": "wrong"})
        paths = client.get("/openapi.json").json()["paths"]
    assert created.status_code == 201 and created.headers["X-Request-ID"] == "reference-http"
    assert repeated.json()["observation_id"] == observation_id
    assert comparison.json()["line_difference_quarters"] == 1
    assert fetched.json()["observation_id"] == observation_id
    assert history.json()["total"] == 1
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "invalid_request"
    assert invalid.json()["message"] == "invalid request parameter"
    assert invalid.json()["correlation_id"]
    assert "/matches/{match_id}/market-references" in paths
    assert "/market-references/{observation_id}/comparison" in paths


@pytest.mark.asyncio
async def test_repository_uses_single_set_based_operations_and_sanitizes_failures() -> None:
    row = _observation_row()
    snapshot = _snapshot_row()
    assert await SqlAlchemyMarketReferenceRepository(Database(Session([snapshot]))).get_snapshot(SNAPSHOT_ID)
    assert await SqlAlchemyMarketReferenceRepository(Database(Session([None]))).get_snapshot(SNAPSHOT_ID) is None
    assert await SqlAlchemyMarketReferenceRepository(Database(Session([row]))).get("x")
    assert await SqlAlchemyMarketReferenceRepository(Database(Session([None]))).get("x") is None
    assert await SqlAlchemyMarketReferenceRepository(Database(Session([row]))).get_by_idempotency_key(101, "x")
    assert await SqlAlchemyMarketReferenceRepository(Database(Session([None]))).get_by_idempotency_key(101, "x") is None
    draft = (await _create(MarketReferenceObservationService(MemoryRepository())))
    source = MarketReferenceObservationDraft(
        observation_id=draft.observation_id, match_id=draft.match_id, market_pricing_id=draft.market_pricing_id,
        market_code=draft.market_code, selection=draft.selection, model_line_quarters=draft.model_line_quarters,
        reference_line_quarters=draft.reference_line_quarters, reference_value=draft.reference_value,
        observed_at=draft.observed_at, correlation_id=draft.correlation_id, idempotency_key="x",
    )
    assert await SqlAlchemyMarketReferenceRepository(Database(Session([row]))).create(source)
    assert await SqlAlchemyMarketReferenceRepository(Database(Session([None, row]))).create(source)
    repository = SqlAlchemyMarketReferenceRepository(Database(Session([row], [101, 1])))
    assert (await repository.list_by_match_snapshot(101, SNAPSHOT_ID, 1, 10)).total == 1  # type: ignore[union-attr]
    assert await SqlAlchemyMarketReferenceRepository(Database(Session([], [None]))).list_by_match_snapshot(404, SNAPSHOT_ID, 1, 10) is None
    failing = SqlAlchemyMarketReferenceRepository(Database(Session(fail=True)))
    for operation in (failing.get_snapshot(SNAPSHOT_ID), failing.get("x"), failing.get_by_idempotency_key(101, "x"), failing.create(source), failing.list_by_match_snapshot(101, SNAPSHOT_ID, 1, 10)):
        with pytest.raises(Exception, match="market reference"):
            await operation


@pytest.mark.asyncio
async def test_defensive_snapshot_decoding_and_route_dependency_branches() -> None:
    repository = MemoryRepository()
    service = MarketReferenceObservationService(repository)
    created = await _create(service)
    repository.snapshot = replace(_snapshot(), canonical_result={})
    with pytest.raises(MarketReferenceValidationError): await service.compare(created.observation_id)
    repository.snapshot = replace(_snapshot(), canonical_input={})
    with pytest.raises(MarketReferenceValidationError): await service.compare(created.observation_id)
    missing = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(database=object())))
    with pytest.raises(Exception, match="database query"): await get_market_reference_service(missing)  # type: ignore[arg-type]
    available = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(database=Database(Session()))))
    assert isinstance(await get_market_reference_service(available), MarketReferenceObservationService)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_snapshot_decoder_rejects_every_noncanonical_shape() -> None:
    value = _snapshot()
    assert _float_value({}) is None
    assert _quote(replace(value, canonical_input={}), "asian_handicap", "home", -1) is None
    assert _quote(replace(value, canonical_result={"engine_result": {}}), "asian_handicap", "home", -1) is None
    malformed = replace(value, canonical_result={"engine_result": {"content": {"fields": {"market_results": {"items": []}}}}})
    assert _quote(malformed, "asian_handicap", "home", -1) is None
    bad_result = replace(value, canonical_result={"engine_result": {"content": {"fields": {"market_results": {"items": [None] * 5}}}}})
    assert _quote(bad_result, "asian_handicap", "home", -1) is None
    no_odds = replace(value, canonical_result={"engine_result": {"content": {"fields": {"market_results": {"items": [{"fields": {"selection": {"value": "home"}, "fair_odds": {}}}] + value.canonical_result["engine_result"]["content"]["fields"]["market_results"]["items"][1:]}}}}})
    assert _quote(no_odds, "asian_handicap", "home", -1) is None
    no_selections = replace(value, canonical_result={"engine_result": {"content": {"fields": {"market_results": {"items": value.canonical_result["engine_result"]["content"]["fields"]["market_results"]["items"][:3] + [{"fields": {"selections": {}}}] + value.canonical_result["engine_result"]["content"]["fields"]["market_results"]["items"][4:]}}}}})
    assert _quote(no_selections, "total_goals", "over", 10) is None
    exhausted = replace(value, canonical_result={"engine_result": {"content": {"fields": {"market_results": {"items": value.canonical_result["engine_result"]["content"]["fields"]["market_results"]["items"][:3] + [{"fields": {"selections": {"items": [_fair_odds("over", "not-a-float"), _fair_odds("under", "0x1.0p+0")]}}}] + value.canonical_result["engine_result"]["content"]["fields"]["market_results"]["items"][4:]}}}}})
    assert _quote(exhausted, "total_goals", "over", 10) is None
    repository = MissingSnapshotRepository()
    repository.values["saved"] = MarketReferenceObservation("saved", 101, SNAPSHOT_ID, "asian_handicap", "home", -1, 0, 2, NOW, NOW, "x")
    with pytest.raises(ResourceNotFoundError): await MarketReferenceObservationService(repository).compare("saved")
