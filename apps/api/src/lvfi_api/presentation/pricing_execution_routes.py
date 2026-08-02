"""Public HTTP resource for immutable, auditable Method One executions."""
# ruff: noqa: B008

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, cast

from fastapi import APIRouter, Depends, Header, Path, Query, Request
from pydantic import BaseModel, ConfigDict

from lvfi_api.application.pricing_execution_comparison import (
    PricingExecutionComparison,
    PricingExecutionComparisonService,
)
from lvfi_api.application.pricing_execution_persistence import (
    PricingExecutionPersistenceService,
)
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.pricing_executions import (
    PricingExecution,
    PricingExecutionHistoryFilters,
    PricingExecutionStatus,
)
from lvfi_api.infrastructure.observability import correlation_id
from lvfi_api.persistence.pricing_executions import SqlAlchemyPricingExecutionRepository
from lvfi_api.presentation.historical_routes import get_method_one_sample_service

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100
router = APIRouter(tags=["pricing executions"])


class PricingExecutionResponse(BaseModel):
    """Public projection of one stored execution; no ORM or provenance fields."""

    model_config = ConfigDict(extra="forbid")

    execution_id: str
    match_id: int
    status: Literal["completed", "blocked_sample_incomplete", "technical_failure"]
    created_at: datetime
    finalized_at: datetime
    correlation_id: str
    sample_fingerprint: str
    input_fingerprint: str | None
    result_fingerprint: str | None
    pricing_engine_version: str
    distribution_version: str
    method_one_version: str
    schema_version: int
    public_parameters: dict[str, Any]
    canonical_input: dict[str, Any] | None
    canonical_result: dict[str, Any] | None
    failure_code: str | None

    @classmethod
    def from_contract(cls, value: PricingExecution) -> PricingExecutionResponse:
        return cls(
            execution_id=value.execution_id,
            match_id=value.match_id,
            status=value.status.value,
            created_at=value.created_at,
            finalized_at=value.finalized_at,
            correlation_id=value.correlation_id,
            sample_fingerprint=value.sample_fingerprint,
            input_fingerprint=value.input_fingerprint,
            result_fingerprint=value.result_fingerprint,
            pricing_engine_version=value.pricing_engine_version,
            distribution_version=value.distribution_version,
            method_one_version=value.method_one_version,
            schema_version=value.schema_version,
            public_parameters=value.public_parameters,
            canonical_input=value.canonical_input,
            canonical_result=value.canonical_result,
            failure_code=value.failure_code,
        )


class PricingExecutionPageResponse(BaseModel):
    """Bounded, deterministic descending execution-history page."""

    page: int
    page_size: int
    total: int
    items: list[PricingExecutionResponse]

    @classmethod
    def from_contract(
        cls, value: Page[PricingExecution]
    ) -> PricingExecutionPageResponse:
        return cls(
            page=value.page,
            page_size=value.page_size,
            total=value.total,
            items=[
                PricingExecutionResponse.from_contract(item) for item in value.items
            ],
        )


class PricingExecutionComparisonFieldResponse(BaseModel):
    """Stable public projection of one compared scalar canonical field."""

    path: str
    left: Any
    right: Any
    equal: bool
    delta: int | float | None


class PricingExecutionComparisonResponse(BaseModel):
    """Read-only comparison of two persisted Method 1 execution records."""

    left_execution_id: str
    right_execution_id: str
    match_id: int
    canonical_compatible: bool
    incompatibilities: list[str]
    fields: list[PricingExecutionComparisonFieldResponse]

    @classmethod
    def from_contract(
        cls, value: PricingExecutionComparison
    ) -> PricingExecutionComparisonResponse:
        return cls(
            left_execution_id=value.left_execution_id,
            right_execution_id=value.right_execution_id,
            match_id=value.match_id,
            canonical_compatible=value.canonical_compatible,
            incompatibilities=list(value.incompatibilities),
            fields=[
                PricingExecutionComparisonFieldResponse(
                    path=field.path,
                    left=field.left,
                    right=field.right,
                    equal=field.equal,
                    delta=field.delta,
                )
                for field in value.fields
            ],
        )


async def get_pricing_execution_service(
    request: Request,
) -> PricingExecutionPersistenceService:
    """Compose only the APP-005 sample boundary and append-only repository."""
    injected = getattr(request.app.state, "pricing_execution_service", None)
    if injected is not None:
        return cast(PricingExecutionPersistenceService, injected)
    database = request.app.state.database
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("database query session unavailable")
    return PricingExecutionPersistenceService(
        await get_method_one_sample_service(request),
        SqlAlchemyPricingExecutionRepository(database),
    )


async def get_pricing_execution_comparison_service(
    request: Request,
) -> PricingExecutionComparisonService:
    """Compose the comparison flow with the read-only execution repository."""
    injected = getattr(request.app.state, "pricing_execution_comparison_service", None)
    if injected is not None:
        return cast(PricingExecutionComparisonService, injected)
    database = request.app.state.database
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("database query session unavailable")
    return PricingExecutionComparisonService(
        SqlAlchemyPricingExecutionRepository(database)
    )


@router.post(
    "/matches/{match_id}/method-one/pricing-executions",
    response_model=PricingExecutionResponse,
    status_code=201,
    summary="Persist one Method 1 pricing execution",
    description=(
        "Executes the existing public Method 1 boundary once and atomically appends "
        "its immutable audit record. Reuse Idempotency-Key only to repeat the same "
        "request deliberately; omit it for a distinct intentional execution."
    ),
    responses={404: {"description": "Target match not found."}},
    openapi_extra={
        "responses": {
            "201": {
                "content": {
                    "application/json": {
                        "example": {
                            "execution_id": "c4f8bf4e-5995-4c01-a85f-403218ce0101",
                            "match_id": 101,
                            "status": "completed",
                            "created_at": "2026-08-02T12:00:00Z",
                            "finalized_at": "2026-08-02T12:00:00Z",
                            "correlation_id": "pricing-execution-example",
                            "sample_fingerprint": "1" * 64,
                            "input_fingerprint": "2" * 64,
                            "result_fingerprint": "3" * 64,
                            "pricing_engine_version": "1.0.1",
                            "distribution_version": "1.1.1",
                            "method_one_version": "1.0.0",
                            "schema_version": 1,
                            "public_parameters": {
                                "requested_count": 10,
                                "statistic_periods": ["goals_regulation_time"],
                            },
                            "canonical_input": {"type": "MethodOneRequest"},
                            "canonical_result": {"root_type": "MethodOneFinalResult"},
                            "failure_code": None,
                        }
                    }
                }
            }
        }
    },
)
async def create_pricing_execution(
    match_id: int = Path(ge=1, description="Stable target match identifier."),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        min_length=1,
        max_length=128,
        description="Optional explicit key for safe retry of this match execution.",
    ),
    service: PricingExecutionPersistenceService = Depends(
        get_pricing_execution_service
    ),
) -> PricingExecutionResponse:
    execution = await service.execute(match_id, correlation_id.get(), idempotency_key)
    return PricingExecutionResponse.from_contract(execution)


@router.get(
    "/pricing-executions/{execution_id}",
    response_model=PricingExecutionResponse,
    summary="Get one persisted Method 1 execution",
    description=(
        "Returns stored canonical material only; it never recalculates pricing."
    ),
    responses={404: {"description": "Pricing execution not found."}},
)
async def get_pricing_execution(
    execution_id: str = Path(
        min_length=36, max_length=36, description="Stable execution UUID."
    ),
    service: PricingExecutionPersistenceService = Depends(
        get_pricing_execution_service
    ),
) -> PricingExecutionResponse:
    return PricingExecutionResponse.from_contract(await service.get(execution_id))


@router.get(
    "/matches/{match_id}/method-one/pricing-executions",
    response_model=PricingExecutionPageResponse,
    summary="List persisted Method 1 executions for a match",
    description=(
        "Lists immutable records using exact public filters, stable created_at and "
        "execution_id ordering, and bounded offset pagination."
    ),
    responses={404: {"description": "Target match not found."}},
)
async def list_pricing_executions(
    match_id: int = Path(ge=1, description="Stable target match identifier."),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    status: PricingExecutionStatus | None = Query(default=None),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    pricing_engine_version: str | None = Query(
        default=None, min_length=1, max_length=32
    ),
    method_one_version: str | None = Query(default=None, min_length=1, max_length=32),
    sample_fingerprint: str | None = Query(default=None, min_length=64, max_length=64),
    correlation_id: str | None = Query(default=None, min_length=1, max_length=128),
    order: Literal["created_at_desc", "created_at_asc"] = Query(
        default="created_at_desc"
    ),
    service: PricingExecutionPersistenceService = Depends(
        get_pricing_execution_service
    ),
) -> PricingExecutionPageResponse:
    filters = PricingExecutionHistoryFilters(
        status=status,
        created_from=created_from,
        created_to=created_to,
        pricing_engine_version=pricing_engine_version,
        method_one_version=method_one_version,
        sample_fingerprint=sample_fingerprint,
        correlation_id=correlation_id,
        order=order,
    )
    return PricingExecutionPageResponse.from_contract(
        await service.list_by_match(match_id, page, page_size, filters)
    )


@router.get(
    "/pricing-execution-comparisons",
    response_model=PricingExecutionComparisonResponse,
    summary="Compare two persisted Method 1 executions",
    description=(
        "Compares stored public canonical records only. It never replays or "
        "recalculates the Pricing Engine."
    ),
    responses={
        404: {"description": "Pricing execution not found."},
        422: {"description": "Incompatible comparison request."},
    },
)
async def compare_pricing_executions(
    left_execution_id: str = Query(min_length=36, max_length=36),
    right_execution_id: str = Query(min_length=36, max_length=36),
    service: PricingExecutionComparisonService = Depends(
        get_pricing_execution_comparison_service
    ),
) -> PricingExecutionComparisonResponse:
    return PricingExecutionComparisonResponse.from_contract(
        await service.compare(left_execution_id, right_execution_id)
    )
