"""Versioned immutable contracts for post-Method-One market pricing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

MARKET_PRICING_SCHEMA_VERSION = 1
RATE_SNAPSHOT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class FrozenRateSnapshot:
    """Rates produced by a versioned model; this layer never recalculates them."""

    home_rate: float
    away_rate: float
    source_model_version: str
    source_execution_id: str | None
    schema_version: int = RATE_SNAPSHOT_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class RequestedMarket:
    """Transport-neutral market request expressed in exact Engine line units."""

    code: str
    selection: str | None = None
    line_half_units: int | None = None
    line_quarters: int | None = None


@dataclass(frozen=True, slots=True)
class MarketPricingDraft:
    market_pricing_id: str
    match_id: int
    finalized_at: datetime
    correlation_id: str
    idempotency_key: str | None
    rates: FrozenRateSnapshot
    rates_fingerprint: str
    pricing_engine_version: str
    input_fingerprint: str
    result_fingerprint: str
    engine_result_fingerprint: str
    canonical_input: str
    canonical_result: str


@dataclass(frozen=True, slots=True)
class MarketPricing:
    """Append-only audited result with canonical payloads stored as received."""

    market_pricing_id: str
    match_id: int
    created_at: datetime
    finalized_at: datetime
    correlation_id: str
    source_model_version: str
    source_execution_id: str | None
    rate_snapshot_schema_version: int
    rates_fingerprint: str
    pricing_engine_version: str
    schema_version: int
    input_fingerprint: str
    result_fingerprint: str
    engine_result_fingerprint: str
    canonical_input: dict[str, Any]
    canonical_result: dict[str, Any]
