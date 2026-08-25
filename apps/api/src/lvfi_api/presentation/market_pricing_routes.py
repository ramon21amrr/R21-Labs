"""Public HTTP contract for immutable post-Method-One market pricing snapshots."""
# ruff: noqa: B008

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, cast

from fastapi import APIRouter, Depends, Header, Path, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from lvfi_api.application.market_pricing_persistence import (
    MarketPricingPersistenceService,
)
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.market_pricings import (
    FrozenRateSnapshot,
    MarketPricing,
    RequestedMarket,
)
from lvfi_api.infrastructure.observability import correlation_id
from lvfi_api.persistence.market_pricings import SqlAlchemyMarketPricingRepository

router = APIRouter(tags=["market pricings"])


class MarketRequestBody(BaseModel):
    """Use Engine's exact integer line units; no application-side line arithmetic."""

    model_config = ConfigDict(extra="forbid")
    code: Literal[
        "three_way_result",
        "double_chance",
        "both_teams_to_score",
        "total_goals",
        "asian_handicap",
        "asian_total",
        "asian_handicap_main_line",
        "asian_total_main_line",
    ]
    selection: Literal["home", "away", "over", "under"] | None = None
    line_half_units: int | None = None
    line_quarters: int | None = None

    def to_contract(self) -> RequestedMarket:
        return RequestedMarket(
            code=self.code,
            selection=self.selection,
            line_half_units=self.line_half_units,
            line_quarters=self.line_quarters,
        )


class MarketPricingCreateRequest(BaseModel):
    """Frozen rates are supplied by an upstream model; this endpoint does not run it."""

    model_config = ConfigDict(extra="forbid")
    home_rate: float
    away_rate: float
    source_model_version: str = Field(min_length=1, max_length=32)
    source_execution_id: str | None = Field(default=None, min_length=36, max_length=36)
    requested_markets: list[MarketRequestBody] = Field(min_length=1, max_length=32)

    def rates(self) -> FrozenRateSnapshot:
        return FrozenRateSnapshot(
            self.home_rate,
            self.away_rate,
            self.source_model_version,
            self.source_execution_id,
        )


class MarketPricingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
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

    @classmethod
    def from_contract(cls, value: MarketPricing) -> MarketPricingResponse:
        return cls(**{name: getattr(value, name) for name in cls.model_fields})


class MarketPricingPageResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[MarketPricingResponse]

    @classmethod
    def from_contract(cls, value: Page[MarketPricing]) -> MarketPricingPageResponse:
        return cls(
            page=value.page,
            page_size=value.page_size,
            total=value.total,
            items=[MarketPricingResponse.from_contract(item) for item in value.items],
        )


async def get_market_pricing_service(
    request: Request,
) -> MarketPricingPersistenceService:
    injected = getattr(request.app.state, "market_pricing_service", None)
    if injected is not None:
        return cast(MarketPricingPersistenceService, injected)
    database = request.app.state.database
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("database query session unavailable")
    return MarketPricingPersistenceService(SqlAlchemyMarketPricingRepository(database))


@router.post(
    "/matches/{match_id}/market-pricings",
    response_model=MarketPricingResponse,
    status_code=201,
    summary="Append one versioned theoretical market-pricing snapshot",
    description=(
        "Accepts already-produced immutable Method 1 rates and invokes only the "
        "public Pricing Engine API. The stored result is canonical Engine output; "
        "it does not rebuild samples or run Method 1. Asian line units are exact: "
        "quarter units for Asian markets and half units for totals."
    ),
)
async def create_market_pricing(
    payload: MarketPricingCreateRequest,
    match_id: int = Path(ge=1),
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key", min_length=1, max_length=128
    ),
    service: MarketPricingPersistenceService = Depends(get_market_pricing_service),
) -> MarketPricingResponse:
    value = await service.price(
        match_id,
        payload.rates(),
        tuple(item.to_contract() for item in payload.requested_markets),
        correlation_id.get(),
        idempotency_key,
    )
    return MarketPricingResponse.from_contract(value)


@router.get(
    "/market-pricings/{market_pricing_id}",
    response_model=MarketPricingResponse,
    summary="Get one immutable market-pricing snapshot",
)
async def get_market_pricing(
    market_pricing_id: str = Path(min_length=36, max_length=36),
    service: MarketPricingPersistenceService = Depends(get_market_pricing_service),
) -> MarketPricingResponse:
    return MarketPricingResponse.from_contract(await service.get(market_pricing_id))


@router.get(
    "/matches/{match_id}/market-pricings",
    response_model=MarketPricingPageResponse,
    summary="List immutable market-pricing snapshots",
)
async def list_market_pricings(
    match_id: int = Path(ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    service: MarketPricingPersistenceService = Depends(get_market_pricing_service),
) -> MarketPricingPageResponse:
    return MarketPricingPageResponse.from_contract(
        await service.list_by_match(match_id, page, page_size)
    )
