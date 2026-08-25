"""Immutable external market-reference observations and public comparison DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class MarketReferenceObservationDraft:
    observation_id: str
    match_id: int
    market_pricing_id: str
    market_code: str
    selection: str
    model_line_quarters: int | None
    reference_line_quarters: int | None
    reference_value: float
    observed_at: datetime
    correlation_id: str
    idempotency_key: str | None


@dataclass(frozen=True, slots=True)
class MarketReferenceObservation:
    observation_id: str
    match_id: int
    market_pricing_id: str
    market_code: str
    selection: str
    model_line_quarters: int | None
    reference_line_quarters: int | None
    reference_value: float
    observed_at: datetime
    created_at: datetime
    correlation_id: str


@dataclass(frozen=True, slots=True)
class ModelReferenceComparison:
    observation: MarketReferenceObservation
    model_value: float
    line_difference_quarters: int | None
