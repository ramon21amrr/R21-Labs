"""Public contracts for append-only external market references and comparisons."""
# ruff: noqa: B008

from __future__ import annotations

from datetime import datetime
from typing import Literal, cast

from fastapi import APIRouter, Depends, Header, Path, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from lvfi_api.application.market_reference_observations import (
    MarketReferenceObservationService,
)
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.market_reference_observations import (
    MarketReferenceObservation,
    ModelReferenceComparison,
)
from lvfi_api.infrastructure.observability import correlation_id
from lvfi_api.persistence.market_reference_observations import (
    SqlAlchemyMarketReferenceRepository,
)

router = APIRouter(tags=["market references"])


class MarketReferenceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    market_pricing_id: str = Field(min_length=36, max_length=36)
    market_code: Literal[
        "three_way_result",
        "double_chance",
        "both_teams_to_score",
        "total_goals",
        "asian_handicap",
        "asian_total",
    ]
    selection: str = Field(pattern=r"^[a-z_]+$", min_length=2, max_length=64)
    model_line_quarters: int | None = None
    reference_line_quarters: int | None = None
    reference_value: float = Field(gt=0)
    observed_at: datetime


class MarketReferenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
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

    @classmethod
    def from_contract(
        cls, value: MarketReferenceObservation
    ) -> MarketReferenceResponse:
        return cls(**{name: getattr(value, name) for name in cls.model_fields})


class MarketReferencePageResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[MarketReferenceResponse]

    @classmethod
    def from_contract(
        cls, value: Page[MarketReferenceObservation]
    ) -> MarketReferencePageResponse:
        return cls(
            page=value.page,
            page_size=value.page_size,
            total=value.total,
            items=[MarketReferenceResponse.from_contract(item) for item in value.items],
        )


class ModelReferenceComparisonResponse(BaseModel):
    observation: MarketReferenceResponse
    model_value: float
    line_difference_quarters: int | None

    @classmethod
    def from_contract(
        cls, value: ModelReferenceComparison
    ) -> ModelReferenceComparisonResponse:
        return cls(
            observation=MarketReferenceResponse.from_contract(value.observation),
            model_value=value.model_value,
            line_difference_quarters=value.line_difference_quarters,
        )


async def get_market_reference_service(
    request: Request,
) -> MarketReferenceObservationService:
    injected = getattr(request.app.state, "market_reference_service", None)
    if injected is not None:
        return cast(MarketReferenceObservationService, injected)
    database = request.app.state.database
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("database query session unavailable")
    repository = SqlAlchemyMarketReferenceRepository(database)
    return MarketReferenceObservationService(repository)


@router.post(
    "/matches/{match_id}/market-references",
    response_model=MarketReferenceResponse,
    status_code=201,
    summary="Append one manual external market reference",
    openapi_extra={
        "responses": {
            "201": {
                "content": {
                    "application/json": {
                        "example": {
                            "observation_id": "c4f8bf4e-5995-4c01-a85f-403218ce0301",
                            "match_id": 101,
                            "market_pricing_id": "c4f8bf4e-5995-4c01-a85f-403218ce0101",
                            "market_code": "asian_handicap",
                            "selection": "home",
                            "model_line_quarters": -1,
                            "reference_line_quarters": 0,
                            "reference_value": 2.05,
                            "observed_at": "2026-08-25T12:00:00Z",
                            "correlation_id": "reference-example",
                        }
                    }
                }
            }
        }
    },
)
async def create_market_reference(
    payload: MarketReferenceCreateRequest,
    match_id: int = Path(ge=1),
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key", min_length=1, max_length=128
    ),
    service: MarketReferenceObservationService = Depends(get_market_reference_service),
) -> MarketReferenceResponse:
    value = await service.create(
        match_id=match_id,
        correlation_id=correlation_id.get(),
        idempotency_key=idempotency_key,
        **payload.model_dump(),
    )
    return MarketReferenceResponse.from_contract(value)


@router.get(
    "/market-references/{observation_id}",
    response_model=MarketReferenceResponse,
    summary="Get one immutable market reference",
)
async def get_market_reference(
    observation_id: str = Path(min_length=36, max_length=36),
    service: MarketReferenceObservationService = Depends(get_market_reference_service),
) -> MarketReferenceResponse:
    return MarketReferenceResponse.from_contract(await service.get(observation_id))


@router.get(
    "/matches/{match_id}/market-pricings/{market_pricing_id}/market-references",
    response_model=MarketReferencePageResponse,
    summary="List references for one match and ENG-006 snapshot",
)
async def list_market_references(
    match_id: int = Path(ge=1),
    market_pricing_id: str = Path(min_length=36, max_length=36),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    service: MarketReferenceObservationService = Depends(get_market_reference_service),
) -> MarketReferencePageResponse:
    return MarketReferencePageResponse.from_contract(
        await service.list_by_match_snapshot(
            match_id, market_pricing_id, page, page_size
        )
    )


@router.get(
    "/market-references/{observation_id}/comparison",
    response_model=ModelReferenceComparisonResponse,
    summary="Compare one model market quote with its external reference",
)
async def compare_market_reference(
    observation_id: str = Path(min_length=36, max_length=36),
    service: MarketReferenceObservationService = Depends(get_market_reference_service),
) -> ModelReferenceComparisonResponse:
    return ModelReferenceComparisonResponse.from_contract(
        await service.compare(observation_id)
    )
