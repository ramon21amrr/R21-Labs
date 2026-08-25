"""Build, fingerprint and append immutable theoretical market-pricing snapshots."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from lvfi_api.domain.errors import (
    MarketPricingEngineError,
    MarketPricingValidationError,
    ResourceNotFoundError,
)
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.market_pricings import (
    MARKET_PRICING_SCHEMA_VERSION,
    FrozenRateSnapshot,
    MarketPricing,
    MarketPricingDraft,
    RequestedMarket,
)
from lvfi_api.infrastructure.market_pricing_engine import (
    PublicMarketPricingEngineFacade,
    public_market_pricing_engine,
)


class MarketPricingRepository(Protocol):
    async def get(self, market_pricing_id: str) -> MarketPricing | None: ...
    async def get_by_idempotency_key(
        self, match_id: int, idempotency_key: str
    ) -> MarketPricing | None: ...
    async def create(self, draft: MarketPricingDraft) -> MarketPricing: ...
    async def list_by_match(
        self, match_id: int, page: int, page_size: int
    ) -> Page[MarketPricing] | None: ...


class MarketPricingPersistenceService:
    """Post-Method-One: rates in, public Engine output out, one ledger insert."""

    def __init__(
        self,
        repository: MarketPricingRepository,
        engine: PublicMarketPricingEngineFacade = public_market_pricing_engine,
    ) -> None:
        self._repository = repository
        self._engine = engine

    async def price(
        self,
        match_id: int,
        rates: FrozenRateSnapshot,
        requested_markets: tuple[RequestedMarket, ...],
        correlation_id: str,
        idempotency_key: str | None,
    ) -> MarketPricing:
        if idempotency_key is not None:
            existing = await self._repository.get_by_idempotency_key(
                match_id, idempotency_key
            )
            if existing is not None:
                return existing
        requested_markets = tuple(sorted(requested_markets, key=_market_key))
        _validate(rates, requested_markets)
        canonical_input = _canonical_input(rates, requested_markets)
        input_fingerprint = _sha256(canonical_input)
        rates_fingerprint = _sha256(_canonical_rates(rates))
        priced = self._engine.price(rates.home_rate, rates.away_rate, requested_markets)
        if priced is None:
            raise MarketPricingEngineError()
        engine_result, engine_result_fingerprint, engine_version = priced
        canonical_result = _canonical_result(
            input_fingerprint, engine_result_fingerprint, engine_result
        )
        return await self._repository.create(
            MarketPricingDraft(
                market_pricing_id=str(uuid4()),
                match_id=match_id,
                finalized_at=datetime.now(UTC),
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                rates=rates,
                rates_fingerprint=rates_fingerprint,
                pricing_engine_version=engine_version,
                input_fingerprint=input_fingerprint,
                result_fingerprint=_sha256(canonical_result),
                engine_result_fingerprint=engine_result_fingerprint,
                canonical_input=canonical_input.decode("utf-8"),
                canonical_result=canonical_result.decode("utf-8"),
            )
        )

    async def get(self, market_pricing_id: str) -> MarketPricing:
        value = await self._repository.get(market_pricing_id)
        if value is None:
            raise ResourceNotFoundError("market pricing")
        return value

    async def list_by_match(
        self, match_id: int, page: int, page_size: int
    ) -> Page[MarketPricing]:
        value = await self._repository.list_by_match(match_id, page, page_size)
        if value is None:
            raise ResourceNotFoundError("match")
        return value


def _validate(rates: FrozenRateSnapshot, markets: tuple[RequestedMarket, ...]) -> None:
    if rates.schema_version != 1 or rates.source_model_version != "1.0.0":
        raise MarketPricingValidationError()
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
        for value in (rates.home_rate, rates.away_rate)
    ):
        raise MarketPricingValidationError()
    if (
        not markets
        or len(set(markets)) != len(markets)
        or any(not _valid_market_contract(market) for market in markets)
    ):
        raise MarketPricingValidationError()


def _valid_market_contract(value: RequestedMarket) -> bool:
    empty = (
        value.selection is None
        and value.line_half_units is None
        and value.line_quarters is None
    )
    if value.code in {
        "three_way_result",
        "double_chance",
        "both_teams_to_score",
        "asian_handicap_main_line",
        "asian_total_main_line",
    }:
        return empty
    if value.code == "total_goals":
        return (
            value.selection is None
            and value.line_half_units is not None
            and value.line_quarters is None
        )
    if value.code == "asian_handicap":
        return (
            value.selection in {"home", "away"}
            and value.line_half_units is None
            and value.line_quarters is not None
        )
    if value.code == "asian_total":
        return (
            value.selection in {"over", "under"}
            and value.line_half_units is None
            and value.line_quarters is not None
        )
    return False


def _market_key(value: RequestedMarket) -> tuple[str, int, int, str]:
    return (
        value.code,
        value.line_half_units or 0,
        value.line_quarters or 0,
        value.selection or "",
    )


def _canonical_rates(value: FrozenRateSnapshot) -> bytes:
    return _json_bytes(
        {
            "away_rate": value.away_rate.hex(),
            "home_rate": value.home_rate.hex(),
            "schema_version": value.schema_version,
            "source_execution_id": value.source_execution_id,
            "source_model_version": value.source_model_version,
            "type": "FrozenRateSnapshot",
        }
    )


def _canonical_input(
    rates: FrozenRateSnapshot, markets: tuple[RequestedMarket, ...]
) -> bytes:
    return _json_bytes(
        {
            "markets": [
                {
                    "code": item.code,
                    "line_half_units": item.line_half_units,
                    "line_quarters": item.line_quarters,
                    "selection": item.selection,
                }
                for item in markets
            ],
            "rates": json.loads(_canonical_rates(rates)),
            "schema_version": MARKET_PRICING_SCHEMA_VERSION,
            "type": "MarketPricingInput",
        }
    )


def _canonical_result(
    input_fingerprint: str, engine_result_fingerprint: str, engine_result: bytes
) -> bytes:
    return _json_bytes(
        {
            "engine_result": json.loads(engine_result),
            "engine_result_fingerprint": engine_result_fingerprint,
            "input_fingerprint": input_fingerprint,
            "schema_version": MARKET_PRICING_SCHEMA_VERSION,
            "type": "MarketPricingSnapshot",
        }
    )


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
