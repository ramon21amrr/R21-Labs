"""HTTP contract for controlled immutable execution reproductions."""
# ruff: noqa: B008

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, cast

from fastapi import APIRouter, Depends, Path, Query, Request
from pydantic import BaseModel

from lvfi_api.application.pricing_execution_reproduction import (
    PricingExecutionReproductionService,
)
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.pricing_execution_reproductions import PricingExecutionReproduction
from lvfi_api.infrastructure.observability import correlation_id
from lvfi_api.persistence.pricing_execution_reproductions import (
    SqlAlchemyPricingExecutionReproductionRepository,
)
from lvfi_api.persistence.pricing_executions import SqlAlchemyPricingExecutionRepository

router = APIRouter(tags=["pricing execution reproductions"])


class ReproductionResponse(BaseModel):
    reproduction_id: str
    execution_id: str
    outcome: Literal[
        "exact_match",
        "mismatch",
        "incompatible_version",
        "blocked",
        "technical_failure",
    ]
    created_at: datetime
    finalized_at: datetime
    correlation_id: str
    original_input_fingerprint: str | None
    reproduced_input_fingerprint: str | None
    original_result_fingerprint: str | None
    reproduced_result_fingerprint: str | None
    original_pricing_engine_version: str
    current_pricing_engine_version: str
    original_distribution_version: str
    current_distribution_version: str
    original_method_one_version: str
    current_method_one_version: str
    original_schema_version: int
    current_schema_version: int
    differences: list[dict[str, Any]]
    failure_code: str | None

    @classmethod
    def from_contract(cls, value: PricingExecutionReproduction) -> ReproductionResponse:
        return cls(
            **{name: getattr(value, name) for name in cls.model_fields}
            | {"outcome": value.outcome.value, "differences": list(value.differences)}
        )


class ReproductionPageResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[ReproductionResponse]

    @classmethod
    def from_contract(
        cls, value: Page[PricingExecutionReproduction]
    ) -> ReproductionPageResponse:
        return cls(
            page=value.page,
            page_size=value.page_size,
            total=value.total,
            items=[ReproductionResponse.from_contract(item) for item in value.items],
        )


async def get_reproduction_service(
    request: Request,
) -> PricingExecutionReproductionService:
    injected = getattr(
        request.app.state, "pricing_execution_reproduction_service", None
    )
    if injected is not None:
        return cast(PricingExecutionReproductionService, injected)
    database = request.app.state.database
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("database query session unavailable")
    return PricingExecutionReproductionService(
        SqlAlchemyPricingExecutionRepository(database),
        SqlAlchemyPricingExecutionReproductionRepository(database),
    )


@router.post(
    "/pricing-executions/{execution_id}/reproductions",
    response_model=ReproductionResponse,
    status_code=201,
    summary="Reproduce one completed Method 1 execution",
    openapi_extra={
        "responses": {
            "201": {
                "content": {
                    "application/json": {
                        "example": {
                            "reproduction_id": "c4f8bf4e-5995-4c01-a85f-403218ce0102",
                            "execution_id": "c4f8bf4e-5995-4c01-a85f-403218ce0101",
                            "outcome": "exact_match",
                            "correlation_id": "reproduction-example",
                            "original_input_fingerprint": "1" * 64,
                            "reproduced_input_fingerprint": "1" * 64,
                            "original_result_fingerprint": "2" * 64,
                            "reproduced_result_fingerprint": "2" * 64,
                            "differences": [],
                            "failure_code": None,
                        }
                    }
                }
            }
        }
    },
)
async def reproduce_pricing_execution(
    execution_id: str = Path(min_length=36, max_length=36),
    service: PricingExecutionReproductionService = Depends(get_reproduction_service),
) -> ReproductionResponse:
    return ReproductionResponse.from_contract(
        await service.reproduce(execution_id, correlation_id.get())
    )


@router.get(
    "/pricing-execution-reproductions/{reproduction_id}",
    response_model=ReproductionResponse,
    summary="Get one controlled reproduction",
)
async def get_reproduction(
    reproduction_id: str = Path(min_length=36, max_length=36),
    service: PricingExecutionReproductionService = Depends(get_reproduction_service),
) -> ReproductionResponse:
    return ReproductionResponse.from_contract(await service.get(reproduction_id))


@router.get(
    "/pricing-executions/{execution_id}/reproductions",
    response_model=ReproductionPageResponse,
    summary="List controlled reproductions",
)
async def list_reproductions(
    execution_id: str = Path(min_length=36, max_length=36),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    service: PricingExecutionReproductionService = Depends(get_reproduction_service),
) -> ReproductionPageResponse:
    return ReproductionPageResponse.from_contract(
        await service.list_by_execution(execution_id, page, page_size)
    )
