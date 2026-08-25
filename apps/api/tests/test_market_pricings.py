"""Regression coverage for ENG-006's independent, append-only market ledger."""

from __future__ import annotations

import hashlib
import inspect
import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from lvfi_pricing.core import CalculationError, ErrorCode
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.application.market_pricing_persistence import (
    MarketPricingPersistenceService,
)
from lvfi_api.domain.errors import (
    MarketPricingEngineError,
    MarketPricingValidationError,
    PersistenceUnavailableError,
    ResourceNotFoundError,
)
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.market_pricings import (
    FrozenRateSnapshot,
    MarketPricing,
    MarketPricingDraft,
    RequestedMarket,
)
from lvfi_api.infrastructure import market_pricing_engine
from lvfi_api.main import create_app
from lvfi_api.persistence.market_pricings import SqlAlchemyMarketPricingRepository
from lvfi_api.presentation.market_pricing_routes import get_market_pricing_service

from .conftest import FakeDatabase

NOW = datetime(2026, 8, 25, tzinfo=UTC)
RATES = FrozenRateSnapshot(1.75, 0.9, "1.0.0", "c4f8bf4e-5995-4c01-a85f-403218ce0101")
MARKETS = (
    RequestedMarket("three_way_result"),
    RequestedMarket("double_chance"),
    RequestedMarket("both_teams_to_score"),
    RequestedMarket("total_goals", line_half_units=5),
    RequestedMarket("asian_handicap", selection="home", line_quarters=0),
    RequestedMarket("asian_total", selection="over", line_quarters=9),
    RequestedMarket("asian_handicap_main_line"),
    RequestedMarket("asian_total_main_line"),
)


class MemoryRepository:
    def __init__(self) -> None:
        self.values: dict[str, MarketPricing] = {}
        self.keys: dict[tuple[int, str], MarketPricing] = {}
        self.matches = {101}

    async def get(self, market_pricing_id: str) -> MarketPricing | None:
        return self.values.get(market_pricing_id)

    async def get_by_idempotency_key(
        self, match_id: int, idempotency_key: str
    ) -> MarketPricing | None:
        return self.keys.get((match_id, idempotency_key))

    async def create(self, draft: MarketPricingDraft) -> MarketPricing:
        value = MarketPricing(
            market_pricing_id=draft.market_pricing_id,
            match_id=draft.match_id,
            created_at=draft.finalized_at,
            finalized_at=draft.finalized_at,
            correlation_id=draft.correlation_id,
            source_model_version=draft.rates.source_model_version,
            source_execution_id=draft.rates.source_execution_id,
            rate_snapshot_schema_version=draft.rates.schema_version,
            rates_fingerprint=draft.rates_fingerprint,
            pricing_engine_version=draft.pricing_engine_version,
            schema_version=1,
            input_fingerprint=draft.input_fingerprint,
            result_fingerprint=draft.result_fingerprint,
            engine_result_fingerprint=draft.engine_result_fingerprint,
            canonical_input=json.loads(draft.canonical_input),
            canonical_result=json.loads(draft.canonical_result),
        )
        self.values[value.market_pricing_id] = value
        if draft.idempotency_key is not None:
            self.keys[(value.match_id, draft.idempotency_key)] = value
        return value

    async def list_by_match(
        self, match_id: int, page: int, page_size: int
    ) -> Page[MarketPricing] | None:
        if match_id not in self.matches:
            return None
        items = tuple(
            sorted(
                (item for item in self.values.values() if item.match_id == match_id),
                key=lambda item: item.market_pricing_id,
                reverse=True,
            )
        )
        return Page(
            items[(page - 1) * page_size : page * page_size],
            page,
            page_size,
            len(items),
        )


def _values(value: object) -> set[str]:
    if isinstance(value, dict):
        return {item for nested in value.values() for item in _values(nested)}
    if isinstance(value, list):
        return {item for nested in value for item in _values(nested)}
    return {value} if isinstance(value, str) else set()


def _keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            item for nested in value.values() for item in _keys(nested)
        }
    if isinstance(value, list):
        return {item for nested in value for item in _keys(nested)}
    return set()


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

    async def execute(self, statement: object) -> Result:
        if self.fail:
            raise SQLAlchemyError("synthetic")
        return Result(self.rows.pop(0) if self.rows else None)

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


def _draft() -> MarketPricingDraft:
    return MarketPricingDraft(
        market_pricing_id="c4f8bf4e-5995-4c01-a85f-403218ce0102",
        match_id=101,
        finalized_at=NOW,
        correlation_id="test",
        idempotency_key="key",
        rates=RATES,
        rates_fingerprint="1" * 64,
        pricing_engine_version="1.0.1",
        input_fingerprint="2" * 64,
        result_fingerprint="3" * 64,
        engine_result_fingerprint="4" * 64,
        canonical_input="{}",
        canonical_result="{}",
    )


def _row() -> dict[str, Any]:
    return {
        "market_pricing_id": "c4f8bf4e-5995-4c01-a85f-403218ce0102",
        "match_id": 101,
        "created_at": NOW,
        "finalized_at": NOW,
        "correlation_id": "test",
        "idempotency_key": "key",
        "source_model_version": "1.0.0",
        "source_execution_id": RATES.source_execution_id,
        "rate_snapshot_schema_version": 1,
        "rates_fingerprint": "1" * 64,
        "pricing_engine_version": "1.0.1",
        "schema_version": 1,
        "input_fingerprint": "2" * 64,
        "result_fingerprint": "3" * 64,
        "engine_result_fingerprint": "4" * 64,
        "canonical_input": "{}",
        "canonical_result": "{}",
    }


@pytest.mark.asyncio
async def test_market_pricing_is_deterministic_and_preserves_asian_states() -> None:
    repository = MemoryRepository()
    service = MarketPricingPersistenceService(repository)
    first = await service.price(101, RATES, MARKETS, "one", None)
    second = await service.price(101, RATES, tuple(reversed(MARKETS)), "two", None)

    assert first.pricing_engine_version == "1.0.1"
    assert first.schema_version == first.rate_snapshot_schema_version == 1
    assert first.rates_fingerprint == second.rates_fingerprint
    assert first.input_fingerprint == second.input_fingerprint
    assert first.result_fingerprint == second.result_fingerprint
    assert (
        first.result_fingerprint
        == hashlib.sha256(
            json.dumps(
                first.canonical_result,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode()
        ).hexdigest()
    )
    values = _values(first.canonical_result)
    assert {
        "three_way_result",
        "total_goals",
        "asian_handicap",
        "asian_total",
    } <= values
    keys = _keys(first.canonical_result)
    assert {"push", "half_win", "half_loss"} <= keys


@pytest.mark.asyncio
async def test_market_pricing_is_append_only_at_service_level_and_idempotent() -> None:
    repository = MemoryRepository()
    service = MarketPricingPersistenceService(repository)
    first = await service.price(101, RATES, MARKETS, "one", "retry")
    repeated = await service.price(101, RATES, MARKETS, "two", "retry")

    assert first.market_pricing_id == repeated.market_pricing_id
    assert (
        await service.get(first.market_pricing_id)
    ).canonical_result == first.canonical_result
    assert (await service.list_by_match(101, 1, 10)).total == 1
    with pytest.raises(ResourceNotFoundError):
        await service.get("missing")
    with pytest.raises(ResourceNotFoundError):
        await service.list_by_match(404, 1, 10)


@pytest.mark.asyncio
async def test_market_pricing_rejects_invalid_frozen_rates_or_market_contract() -> None:
    service = MarketPricingPersistenceService(MemoryRepository())
    with pytest.raises(MarketPricingValidationError):
        await service.price(
            101, FrozenRateSnapshot(-1, 1, "1.0.0", None), MARKETS, "one", None
        )
    with pytest.raises(MarketPricingValidationError):
        await service.price(
            101,
            RATES,
            (RequestedMarket("asian_total", selection="home", line_quarters=9),),
            "one",
            None,
        )
    with pytest.raises(MarketPricingValidationError):
        await service.price(
            101, FrozenRateSnapshot(1, 1, "2.0.0", None), MARKETS, "one", None
        )
    with pytest.raises(MarketPricingValidationError):
        await service.price(101, RATES, (RequestedMarket("unsupported"),), "one", None)


@pytest.mark.asyncio
async def test_market_pricing_reports_a_public_engine_failure() -> None:
    class BrokenEngine:
        @staticmethod
        def price(*args: object) -> None:
            return None

    with pytest.raises(MarketPricingEngineError):
        await MarketPricingPersistenceService(
            MemoryRepository(),
            BrokenEngine(),  # type: ignore[arg-type]
        ).price(101, RATES, MARKETS, "one", None)


def test_market_pricing_boundary_uses_only_exported_pricing_engine_modules() -> None:
    source = inspect.getsource(market_pricing_engine)
    assert market_pricing_engine.pricing_engine_public_api_is_available() is True
    assert "from lvfi_pricing.engine import" in source
    assert ".contracts import" not in source
    assert ".orchestrator import" not in source


def test_public_engine_adapter_supports_every_engine_market_and_failure_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = market_pricing_engine
    for request in MARKETS:
        assert adapter._engine_request(request) is not None
    assert (
        adapter._engine_request(
            RequestedMarket("asian_total", selection="home", line_quarters=1)
        )
        is None
    )
    assert (
        adapter._engine_request(
            RequestedMarket("asian_handicap", selection="wrong", line_quarters=1)
        )
        is None
    )
    assert adapter._engine_request(RequestedMarket("wrong")) is None
    assert adapter.public_market_pricing_engine.price(1.0, 1.0, MARKETS) is not None
    assert (
        adapter.public_market_pricing_engine.price(
            1.0, 1.0, (RequestedMarket("wrong"),)
        )
        is None
    )
    error = CalculationError(ErrorCode.INVALID_NUMBER, "synthetic", "rate")
    monkeypatch.setattr(adapter.PoissonRate, "create", lambda value: error)
    assert adapter.public_market_pricing_engine.price(1.0, 1.0, MARKETS) is None
    monkeypatch.undo()
    monkeypatch.setattr(adapter.PricingRequest, "create", lambda *args: error)
    assert adapter.public_market_pricing_engine.price(1.0, 1.0, MARKETS) is None
    monkeypatch.undo()
    monkeypatch.setattr(adapter, "run_pricing_engine", lambda request: error)
    assert adapter.public_market_pricing_engine.price(1.0, 1.0, MARKETS) is None
    monkeypatch.undo()
    monkeypatch.setattr(adapter, "serialize_pricing_result", lambda result: error)
    assert adapter.public_market_pricing_engine.price(1.0, 1.0, MARKETS) is None


def test_market_pricing_http_contract_and_historical_execution_routes_remain_available(
    settings: object,
) -> None:
    repository = MemoryRepository()
    app = create_app(settings, FakeDatabase())  # type: ignore[arg-type]
    app.state.market_pricing_service = MarketPricingPersistenceService(repository)
    with TestClient(app) as client:
        created = client.post(
            "/matches/101/market-pricings",
            headers={"X-Request-ID": "market-http", "Idempotency-Key": "market-key"},
            json={
                "home_rate": 1.75,
                "away_rate": 0.9,
                "source_model_version": "1.0.0",
                "source_execution_id": RATES.source_execution_id,
                "requested_markets": [
                    {"code": "three_way_result"},
                    {"code": "total_goals", "line_half_units": 5},
                    {"code": "asian_handicap", "selection": "home", "line_quarters": 0},
                    {"code": "asian_total", "selection": "over", "line_quarters": 9},
                ],
            },
        )
        paths = client.get("/openapi.json").json()["paths"]
        listed = client.get("/matches/101/market-pricings")
        fetched = client.get("/market-pricings/" + created.json()["market_pricing_id"])
        invalid = client.post(
            "/matches/101/market-pricings",
            json={
                "home_rate": -1,
                "away_rate": 1,
                "source_model_version": "1.0.0",
                "requested_markets": [{"code": "three_way_result"}],
            },
        )
    assert created.status_code == 201
    assert created.headers["X-Request-ID"] == "market-http"
    assert (
        listed.status_code == fetched.status_code == 200 and listed.json()["total"] == 1
    )
    assert invalid.status_code == 422 and invalid.json()["code"] == "invalid_request"
    assert "/matches/{match_id}/market-pricings" in paths
    assert "/matches/{match_id}/method-one/pricing-executions" in paths


@pytest.mark.asyncio
async def test_sqlalchemy_market_pricing_repository_operations() -> None:
    row = _row()
    assert await SqlAlchemyMarketPricingRepository(Database(Session([row]))).get("x")
    assert (
        await SqlAlchemyMarketPricingRepository(Database(Session([None]))).get("x")
        is None
    )
    assert await SqlAlchemyMarketPricingRepository(
        Database(Session([row]))
    ).get_by_idempotency_key(101, "key")
    assert (
        await SqlAlchemyMarketPricingRepository(
            Database(Session([None]))
        ).get_by_idempotency_key(101, "key")
        is None
    )
    assert (
        await SqlAlchemyMarketPricingRepository(Database(Session([row]))).create(
            _draft()
        )
    ).market_pricing_id == row["market_pricing_id"]
    assert (
        await SqlAlchemyMarketPricingRepository(Database(Session([None, row]))).create(
            _draft()
        )
    ).market_pricing_id == row["market_pricing_id"]
    assert (
        await SqlAlchemyMarketPricingRepository(
            Database(Session([row], [101, 1]))
        ).list_by_match(101, 1, 10)
    ).total == 1  # type: ignore[union-attr]
    assert (
        await SqlAlchemyMarketPricingRepository(
            Database(Session([], [None]))
        ).list_by_match(404, 1, 10)
        is None
    )
    for operation in (
        SqlAlchemyMarketPricingRepository(Database(Session(fail=True))).get("x"),
        SqlAlchemyMarketPricingRepository(
            Database(Session(fail=True))
        ).get_by_idempotency_key(101, "key"),
        SqlAlchemyMarketPricingRepository(Database(Session(fail=True))).create(
            _draft()
        ),
        SqlAlchemyMarketPricingRepository(Database(Session(fail=True))).list_by_match(
            101, 1, 10
        ),
    ):
        with pytest.raises(PersistenceUnavailableError):
            await operation


@pytest.mark.asyncio
async def test_market_pricing_route_dependency_handles_database_states() -> None:
    unavailable = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(database=object()))
    )
    with pytest.raises(PersistenceUnavailableError):
        await get_market_pricing_service(unavailable)  # type: ignore[arg-type]
    available = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(database=Database(Session())))
    )
    assert isinstance(
        await get_market_pricing_service(available), MarketPricingPersistenceService
    )  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_postgresql_market_pricing_ledger_is_append_only() -> None:
    """Exercise ENG-006's database trigger against the disposable task database."""
    import os
    from datetime import date

    from sqlalchemy import delete, insert, update
    from sqlalchemy.exc import DBAPIError
    from sqlalchemy.ext.asyncio import create_async_engine

    database_url = os.environ.get("LVFI_DATABASE_URL")
    if database_url is None or "127.0.0.1:55432" not in database_url:
        pytest.skip("requires the isolated Codex PostgreSQL task database")
    from lvfi_api.persistence.historical_models import (
        competitions,
        import_batches,
        market_pricings,
        matches,
        seasons,
        source_records,
        teams,
    )

    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                insert(import_batches).values(
                    id=201,
                    source_filename="synthetic-market",
                    source_sha256="0" * 64,
                    sheet_name="synthetic-market",
                    status="completed",
                )
            )
            await connection.execute(
                insert(source_records).values(
                    id=201,
                    batch_id=201,
                    source_line=201,
                    row_sha256="0" * 64,
                    raw_values={},
                    status="accepted",
                )
            )
            await connection.execute(
                insert(competitions).values(
                    id=201,
                    display_name="Market Synthetic",
                    normalized_name="market-synthetic",
                )
            )
            await connection.execute(
                insert(seasons).values(id=201, competition_id=201, label="2026")
            )
            await connection.execute(
                insert(teams).values(
                    id=201,
                    display_name="Market Home",
                    normalized_name="market-home",
                )
            )
            await connection.execute(
                insert(teams).values(
                    id=202,
                    display_name="Market Away",
                    normalized_name="market-away",
                )
            )
            await connection.execute(
                insert(matches).values(
                    id=201,
                    season_id=201,
                    played_on=date(2026, 8, 25),
                    home_team_id=201,
                    away_team_id=202,
                    source_record_id=201,
                )
            )
            await connection.execute(
                insert(market_pricings).values(
                    market_pricing_id="c4f8bf4e-5995-4c01-a85f-403218ce0201",
                    match_id=201,
                    finalized_at=NOW,
                    correlation_id="postgres-market",
                    source_model_version="1.0.0",
                    source_execution_id=None,
                    rate_snapshot_schema_version=1,
                    rates_fingerprint="1" * 64,
                    pricing_engine_version="1.0.1",
                    schema_version=1,
                    input_fingerprint="2" * 64,
                    result_fingerprint="3" * 64,
                    engine_result_fingerprint="4" * 64,
                    canonical_input="{}",
                    canonical_result="{}",
                )
            )
        with pytest.raises(DBAPIError):
            async with engine.begin() as connection:
                await connection.execute(
                    update(market_pricings)
                    .where(
                        market_pricings.c.market_pricing_id
                        == "c4f8bf4e-5995-4c01-a85f-403218ce0201"
                    )
                    .values(correlation_id="mutated")
                )
        with pytest.raises(DBAPIError):
            async with engine.begin() as connection:
                await connection.execute(
                    delete(market_pricings).where(
                        market_pricings.c.market_pricing_id
                        == "c4f8bf4e-5995-4c01-a85f-403218ce0201"
                    )
                )
    finally:
        await engine.dispose()
