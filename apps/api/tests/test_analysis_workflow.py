"""Focused contract tests for APP-015 workflow boundaries and snapshot hashing."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from lvfi_api.application.analysis_workflow import AnalysisWorkflowService
from lvfi_api.domain.analysis_workflow import (
    Analysis,
    AnalysisEvent,
    AnalysisEventType,
    AnalysisSnapshot,
    AnalysisStatus,
    snapshot_hash,
)
from lvfi_api.domain.errors import InvalidQueryError, ResourceNotFoundError
from lvfi_api.main import create_app
from lvfi_api.persistence.analysis_workflow import _sample_match_ids
from lvfi_api.presentation.analysis_workflow_routes import get_analysis_workflow_service

NOW = datetime(2026, 9, 10, tzinfo=UTC)
ANALYSIS_ID = "00000000-0000-4000-8000-000000000001"
EXECUTION_ID = "00000000-0000-4000-8000-000000000002"
SNAPSHOT_ID = "00000000-0000-4000-8000-000000000003"


def _event(kind: AnalysisEventType, event_id: int) -> AnalysisEvent:
    return AnalysisEvent(
        event_id,
        kind,
        EXECUTION_ID if kind is AnalysisEventType.CALCULATED else None,
        "local-admin" if kind is not AnalysisEventType.CALCULATED else None,
        "verified" if kind is not AnalysisEventType.CALCULATED else None,
        NOW,
    )


def _analysis(
    events: tuple[AnalysisEvent, ...] = (), analysis_id: str = ANALYSIS_ID
) -> Analysis:
    status = (
        AnalysisStatus.APPROVED
        if any(event.event_type is AnalysisEventType.APPROVED for event in events)
        else AnalysisStatus.CALCULATED
        if events
        else AnalysisStatus.DRAFT
    )
    return Analysis(analysis_id, 101, status, NOW, events)


class _Repository:
    def __init__(self) -> None:
        self.value = _analysis()
        self.snapshot_value: AnalysisSnapshot | None = None

    async def create_draft(self, analysis_id: str, match_id: int) -> Analysis | None:
        if match_id != 101:
            return None
        self.value = Analysis(analysis_id, match_id, AnalysisStatus.DRAFT, NOW, ())
        return self.value

    async def calculate(self, analysis_id: str, execution_id: str) -> Analysis | None:
        if analysis_id != self.value.analysis_id or execution_id != EXECUTION_ID:
            return None
        if self.value.status is not AnalysisStatus.DRAFT:
            raise InvalidQueryError("state")
        self.value = _analysis(
            (_event(AnalysisEventType.CALCULATED, 1),), self.value.analysis_id
        )
        return self.value

    async def review(
        self, analysis_id: str, actor: str, reason: str
    ) -> Analysis | None:
        if analysis_id != self.value.analysis_id:
            return None
        if self.value.status is not AnalysisStatus.CALCULATED:
            raise InvalidQueryError("state")
        self.value = _analysis(
            self.value.events + (_event(AnalysisEventType.REVIEWED, 2),),
            self.value.analysis_id,
        )
        return self.value

    async def approve(
        self, analysis_id: str, snapshot_id: str, actor: str, reason: str
    ) -> tuple[Analysis, AnalysisSnapshot] | None:
        if analysis_id != self.value.analysis_id:
            return None
        if not any(
            event.event_type is AnalysisEventType.REVIEWED
            for event in self.value.events
        ):
            raise InvalidQueryError("review")
        self.value = _analysis(
            self.value.events + (_event(AnalysisEventType.APPROVED, 3),),
            self.value.analysis_id,
        )
        payload = {"analysis": self.value.analysis_id, "events": 3}
        self.snapshot_value = AnalysisSnapshot(
            snapshot_id, self.value.analysis_id, payload, snapshot_hash(payload), NOW
        )
        return self.value, self.snapshot_value

    async def get(self, analysis_id: str) -> Analysis | None:
        return self.value if analysis_id == self.value.analysis_id else None

    async def list_by_match(self, match_id: int) -> tuple[Analysis, ...] | None:
        return (self.value,) if match_id == 101 else None

    async def get_snapshot_by_analysis(
        self, analysis_id: str
    ) -> AnalysisSnapshot | None:
        return self.snapshot_value if analysis_id == self.value.analysis_id else None

    async def get_snapshot(self, snapshot_id: str) -> AnalysisSnapshot | None:
        return (
            self.snapshot_value
            if self.snapshot_value and snapshot_id == self.snapshot_value.snapshot_id
            else None
        )


@pytest.mark.asyncio
async def test_service_enforces_review_before_approval_and_exposes_history() -> None:
    repository = _Repository()
    service = AnalysisWorkflowService(repository)
    draft = await service.create_draft(101)
    assert draft.status is AnalysisStatus.DRAFT
    calculated = await service.calculate(draft.analysis_id, EXECUTION_ID)
    assert calculated.status is AnalysisStatus.CALCULATED
    with pytest.raises(InvalidQueryError):
        await service.approve(draft.analysis_id, "local-admin", "verified")
    reviewed = await service.review(draft.analysis_id, "local-admin", "verified")
    approved, snapshot = await service.approve(
        reviewed.analysis_id, "local-admin", "approved"
    )
    assert approved.status is AnalysisStatus.APPROVED
    assert await service.get(draft.analysis_id) == approved
    assert await service.list_by_match(101) == (approved,)
    assert await service.snapshot_for_analysis(draft.analysis_id) == snapshot
    assert await service.snapshot(snapshot.snapshot_id) == snapshot
    with pytest.raises(ResourceNotFoundError):
        await service.create_draft(404)
    with pytest.raises(ResourceNotFoundError):
        await service.get("00000000-0000-4000-8000-000000000099")
    with pytest.raises(ResourceNotFoundError):
        await service.calculate(draft.analysis_id, "missing")
    with pytest.raises(InvalidQueryError):
        await service.review(draft.analysis_id, " ", "reason")
    with pytest.raises(InvalidQueryError):
        await service.approve(draft.analysis_id, "actor", " ")
    with pytest.raises(ResourceNotFoundError):
        await service.list_by_match(404)
    with pytest.raises(ResourceNotFoundError):
        await service.snapshot_for_analysis("missing")
    with pytest.raises(ResourceNotFoundError):
        await service.snapshot("missing")


def test_snapshot_hash_is_key_order_independent_and_payload_sensitive() -> None:
    assert snapshot_hash({"b": [2, 1], "a": 1}) == snapshot_hash({"a": 1, "b": [2, 1]})
    assert snapshot_hash({"a": 1}) != snapshot_hash({"a": 2})


def test_snapshot_sample_identifier_projection_normalizes_canonical_strings() -> None:
    canonical_input = {
        "target": {"match_id": "101", "team_id": "99"},
        "references": [{"match_id": "2"}, {"match_id": 3}, {"id": "004"}],
        "ignored": {"id": "not-a-match", "match_id": True},
    }
    assert _sample_match_ids(canonical_input) == [2, 3, 101]


class _MissingRepository:
    async def calculate(self, *_: Any) -> None:
        return None

    async def review(self, *_: Any) -> None:
        return None

    async def approve(self, *_: Any) -> None:
        return None


@pytest.mark.asyncio
async def test_service_reports_missing_transition_targets() -> None:
    service = AnalysisWorkflowService(_MissingRepository())  # type: ignore[arg-type]
    with pytest.raises(ResourceNotFoundError):
        await service.calculate(ANALYSIS_ID, EXECUTION_ID)
    with pytest.raises(ResourceNotFoundError):
        await service.review(ANALYSIS_ID, "actor", "reason")
    with pytest.raises(ResourceNotFoundError):
        await service.approve(ANALYSIS_ID, "actor", "reason")


@pytest.mark.asyncio
async def test_route_service_composition_covers_fallbacks(
    settings: Any, database: Any
) -> None:
    from types import SimpleNamespace

    app = create_app(settings, database)
    with pytest.raises(Exception, match="database unavailable"):
        await get_analysis_workflow_service(SimpleNamespace(app=app))  # type: ignore[arg-type]

    class _SessionDatabase:
        def session(self) -> Any:
            raise AssertionError("not called while composing the service")

    app.state.database = _SessionDatabase()
    assert isinstance(
        await get_analysis_workflow_service(SimpleNamespace(app=app)),
        AnalysisWorkflowService,
    )


def test_routes_execute_minimal_review_approval_workflow(
    settings: Any, database: Any
) -> None:
    app = create_app(settings, database)
    service = AnalysisWorkflowService(_Repository())
    app.state.analysis_workflow_service = service
    with TestClient(app) as client:
        created = client.post("/matches/101/analyses")
        analysis_id = created.json()["analysis_id"]
        calculated = client.post(
            f"/analyses/{analysis_id}/calculate", json={"execution_id": EXECUTION_ID}
        )
        blocked = client.post(
            f"/analyses/{analysis_id}/approve", json={"reason": "missing review"}
        )
        reviewed = client.post(
            f"/analyses/{analysis_id}/reviews", json={"reason": "checked"}
        )
        approved = client.post(
            f"/analyses/{analysis_id}/approve", json={"reason": "approved"}
        )
        snapshot_id = approved.json()["snapshot"]["snapshot_id"]
        history = client.get("/matches/101/analyses")
        snapshot = client.get(f"/analysis-snapshots/{snapshot_id}")
        analysis = client.get(f"/analyses/{analysis_id}")
        own_snapshot = client.get(f"/analyses/{analysis_id}/snapshot")
        invalid = client.post(
            f"/analyses/{analysis_id}/reviews", json={"reason": "late"}
        )
    assert created.status_code == 201 and created.json()["status"] == "draft"
    assert calculated.status_code == 200 and calculated.json()["status"] == "calculated"
    assert blocked.status_code == 422
    assert reviewed.status_code == 200
    assert (
        approved.status_code == 200
        and approved.json()["analysis"]["status"] == "approved"
    )
    assert (
        history.status_code == 200
        and history.json()["analyses"][0]["analysis_id"] == analysis_id
    )
    assert (
        snapshot.status_code == 200
        and snapshot.json()["snapshot_hash"]
        == approved.json()["snapshot"]["snapshot_hash"]
    )
    assert analysis.status_code == 200
    assert own_snapshot.status_code == 200
    assert invalid.status_code == 422
