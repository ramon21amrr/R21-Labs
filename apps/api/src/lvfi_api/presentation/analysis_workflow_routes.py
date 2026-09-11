"""Minimal HTTP surface for APP-015 immutable analysis workflow records."""
# ruff: noqa: B008

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, cast

from fastapi import APIRouter, Depends, Path, Request
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from lvfi_api.application.analysis_workflow import AnalysisWorkflowService
from lvfi_api.domain.analysis_workflow import Analysis, AnalysisEvent, AnalysisSnapshot
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.persistence.analysis_workflow import SqlAlchemyAnalysisWorkflowRepository
from lvfi_api.presentation.local_admin_authentication_routes import (
    require_authenticated_admin,
)

router = APIRouter(tags=["analysis workflow"])


class CalculateAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    execution_id: StrictStr = Field(min_length=36, max_length=36)


class WorkflowDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: StrictStr = Field(min_length=1, max_length=2000)


class AnalysisEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: int
    event_type: Literal["calculated", "reviewed", "approved"]
    execution_id: str | None
    actor: str | None
    reason: str | None
    created_at: datetime

    @classmethod
    def from_contract(cls, value: AnalysisEvent) -> AnalysisEventResponse:
        return cls(
            event_id=value.event_id,
            event_type=value.event_type.value,
            execution_id=value.execution_id,
            actor=value.actor,
            reason=value.reason,
            created_at=value.created_at,
        )


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analysis_id: str
    match_id: int
    status: Literal["draft", "calculated", "approved"]
    created_at: datetime
    events: list[AnalysisEventResponse]

    @classmethod
    def from_contract(cls, value: Analysis) -> AnalysisResponse:
        return cls(
            analysis_id=value.analysis_id,
            match_id=value.match_id,
            status=value.status.value,
            created_at=value.created_at,
            events=[
                AnalysisEventResponse.from_contract(event) for event in value.events
            ],
        )


class AnalysisHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analyses: list[AnalysisResponse]


class AnalysisSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    snapshot_id: str
    analysis_id: str
    payload: dict[str, Any]
    snapshot_hash: str
    created_at: datetime

    @classmethod
    def from_contract(cls, value: AnalysisSnapshot) -> AnalysisSnapshotResponse:
        return cls(
            snapshot_id=value.snapshot_id,
            analysis_id=value.analysis_id,
            payload=value.payload,
            snapshot_hash=value.snapshot_hash,
            created_at=value.created_at,
        )


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analysis: AnalysisResponse
    snapshot: AnalysisSnapshotResponse


async def get_analysis_workflow_service(request: Request) -> AnalysisWorkflowService:
    injected = getattr(request.app.state, "analysis_workflow_service", None)
    if injected is not None:
        return cast(AnalysisWorkflowService, injected)
    database = request.app.state.database
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("analysis workflow database unavailable")
    return AnalysisWorkflowService(SqlAlchemyAnalysisWorkflowRepository(database))


@router.post(
    "/matches/{match_id}/analyses", response_model=AnalysisResponse, status_code=201
)
async def create_analysis(
    match_id: int = Path(ge=1),
    service: AnalysisWorkflowService = Depends(get_analysis_workflow_service),
) -> AnalysisResponse:
    return AnalysisResponse.from_contract(await service.create_draft(match_id))


@router.post("/analyses/{analysis_id}/calculate", response_model=AnalysisResponse)
async def calculate_analysis(
    payload: CalculateAnalysisRequest,
    analysis_id: str = Path(min_length=36, max_length=36),
    service: AnalysisWorkflowService = Depends(get_analysis_workflow_service),
) -> AnalysisResponse:
    return AnalysisResponse.from_contract(
        await service.calculate(analysis_id, payload.execution_id)
    )


@router.post("/analyses/{analysis_id}/reviews", response_model=AnalysisResponse)
async def review_analysis(
    payload: WorkflowDecisionRequest,
    analysis_id: str = Path(min_length=36, max_length=36),
    actor: str = Depends(require_authenticated_admin),
    service: AnalysisWorkflowService = Depends(get_analysis_workflow_service),
) -> AnalysisResponse:
    return AnalysisResponse.from_contract(
        await service.review(analysis_id, actor, payload.reason)
    )


@router.post("/analyses/{analysis_id}/approve", response_model=ApprovalResponse)
async def approve_analysis(
    payload: WorkflowDecisionRequest,
    analysis_id: str = Path(min_length=36, max_length=36),
    actor: str = Depends(require_authenticated_admin),
    service: AnalysisWorkflowService = Depends(get_analysis_workflow_service),
) -> ApprovalResponse:
    analysis, snapshot = await service.approve(
        analysis_id, actor, payload.reason
    )
    return ApprovalResponse(
        analysis=AnalysisResponse.from_contract(analysis),
        snapshot=AnalysisSnapshotResponse.from_contract(snapshot),
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str = Path(min_length=36, max_length=36),
    service: AnalysisWorkflowService = Depends(get_analysis_workflow_service),
) -> AnalysisResponse:
    return AnalysisResponse.from_contract(await service.get(analysis_id))


@router.get("/matches/{match_id}/analyses", response_model=AnalysisHistoryResponse)
async def list_analyses(
    match_id: int = Path(ge=1),
    service: AnalysisWorkflowService = Depends(get_analysis_workflow_service),
) -> AnalysisHistoryResponse:
    return AnalysisHistoryResponse(
        analyses=[
            AnalysisResponse.from_contract(item)
            for item in await service.list_by_match(match_id)
        ]
    )


@router.get("/analyses/{analysis_id}/snapshot", response_model=AnalysisSnapshotResponse)
async def get_analysis_snapshot(
    analysis_id: str = Path(min_length=36, max_length=36),
    service: AnalysisWorkflowService = Depends(get_analysis_workflow_service),
) -> AnalysisSnapshotResponse:
    return AnalysisSnapshotResponse.from_contract(
        await service.snapshot_for_analysis(analysis_id)
    )


@router.get(
    "/analysis-snapshots/{snapshot_id}", response_model=AnalysisSnapshotResponse
)
async def get_snapshot(
    snapshot_id: str = Path(min_length=36, max_length=36),
    service: AnalysisWorkflowService = Depends(get_analysis_workflow_service),
) -> AnalysisSnapshotResponse:
    return AnalysisSnapshotResponse.from_contract(await service.snapshot(snapshot_id))
