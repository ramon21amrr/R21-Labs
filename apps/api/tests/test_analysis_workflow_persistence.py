"""Repository-level APP-015 tests using transactional async-session doubles."""

from __future__ import annotations

from contextlib import asynccontextmanager
from copy import deepcopy
from datetime import UTC, date, datetime
from typing import Any

import pytest
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.application.analysis_workflow import AnalysisWorkflowService
from lvfi_api.domain.analysis_workflow import (
    Analysis,
    AnalysisEvent,
    AnalysisEventType,
    AnalysisSnapshot,
    AnalysisStatus,
    snapshot_hash,
)
from lvfi_api.domain.configuration import CATALOG_ID
from lvfi_api.domain.errors import InvalidQueryError, PersistenceUnavailableError
from lvfi_api.persistence import analysis_workflow as workflow

NOW = datetime(2026, 9, 10, tzinfo=UTC)
ANALYSIS_ID = "00000000-0000-4000-8000-000000000001"
EXECUTION_ID = "00000000-0000-4000-8000-000000000002"

ANALYSIS_ROW: dict[str, Any] = {
    "analysis_id": ANALYSIS_ID,
    "match_id": 101,
    "created_at": NOW,
}
CALCULATED_ROW: dict[str, Any] = {
    "id": 1,
    "analysis_id": ANALYSIS_ID,
    "event_type": "calculated",
    "execution_id": EXECUTION_ID,
    "actor": None,
    "reason": None,
    "created_at": NOW,
}
REVIEWED_ROW = {
    **CALCULATED_ROW,
    "id": 2,
    "event_type": "reviewed",
    "execution_id": None,
    "actor": "reviewer",
    "reason": "checked",
}
APPROVED_ROW = {
    **CALCULATED_ROW,
    "id": 3,
    "event_type": "approved",
    "execution_id": None,
    "actor": "approver",
    "reason": "approved",
}
EXECUTION_ROW: dict[str, Any] = {
    "execution_id": EXECUTION_ID,
    "match_id": 101,
    "status": "completed",
    "created_at": NOW,
    "finalized_at": NOW,
    "correlation_id": "correlation",
    "sample_fingerprint": "a" * 64,
    "input_fingerprint": "b" * 64,
    "result_fingerprint": "c" * 64,
    "pricing_engine_version": "1.0.1",
    "distribution_version": "1.1.1",
    "method_one_version": "1.0.0",
    "schema_version": 1,
    "public_parameters": {"requested_count": 10},
    "canonical_input": (
        '{"fields":{"match_id":"101","series_references":{"items":['
        '{"fields":{"snapshot":{"fields":{"observations":{"items":['
        '{"fields":{"identity":{"fields":{"match_id":"2"}}}}]}}}}}]}}}'
    ),
    "canonical_result": (
        '{"warnings":["source warning"],"root_type":"MethodOneFinalResult"}'
    ),
    "failure_code": None,
}


class _Result:
    def __init__(self, value: Any = None) -> None:
        self.value = value

    def mappings(self) -> _Result:
        return self

    def one_or_none(self) -> Any:
        return self.value

    def one(self) -> Any:
        assert self.value is not None
        return self.value

    def all(self) -> list[Any]:
        return self.value if isinstance(self.value, list) else []


class _Session:
    def __init__(
        self, results: list[Any] | None = None, scalars: list[Any] | None = None
    ) -> None:
        self.results = list(results or [])
        self.scalars = list(scalars or [])
        self.statements: list[Any] = []
        self.rolled_back = False

    async def execute(self, _: Any) -> _Result:
        self.statements.append(_)
        item = self.results.pop(0) if self.results else None
        if isinstance(item, Exception):
            raise item
        return _Result(item)

    async def scalar(self, _: Any) -> Any:
        item = self.scalars.pop(0) if self.scalars else None
        if isinstance(item, Exception):
            raise item
        return item

    async def rollback(self) -> None:
        self.rolled_back = True


class _Database:
    def __init__(self, session: _Session) -> None:
        self.value = session

    @asynccontextmanager
    async def session(self) -> Any:
        try:
            yield self.value
        except Exception:
            await self.value.rollback()
            raise


def _event(kind: AnalysisEventType, event_id: int) -> AnalysisEvent:
    return AnalysisEvent(
        event_id,
        kind,
        EXECUTION_ID if kind is AnalysisEventType.CALCULATED else None,
        "actor" if kind is not AnalysisEventType.CALCULATED else None,
        "reason" if kind is not AnalysisEventType.CALCULATED else None,
        NOW,
    )


@pytest.mark.asyncio
async def test_repository_creates_calculates_and_reviews_with_state_guards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session(results=[{"match_id": 101, "status": "completed"}, None])
    repository = workflow.SqlAlchemyAnalysisWorkflowRepository(_Database(session))
    monkeypatch.setattr(
        workflow, "_locked_analysis", lambda *_: _return((ANALYSIS_ROW, ()))
    )
    monkeypatch.setattr(
        workflow,
        "_events",
        lambda *_: _return((_event(AnalysisEventType.CALCULATED, 1),)),
    )
    calculated = await repository.calculate(ANALYSIS_ID, EXECUTION_ID)
    assert calculated is not None and calculated.status is AnalysisStatus.CALCULATED
    monkeypatch.setattr(
        workflow,
        "_locked_analysis",
        lambda *_: _return((ANALYSIS_ROW, (_event(AnalysisEventType.CALCULATED, 1),))),
    )
    reviewed = await repository.review(ANALYSIS_ID, "actor", "reason")
    assert (
        reviewed is not None
        and reviewed.events[0].event_type is AnalysisEventType.CALCULATED
    )
    monkeypatch.setattr(
        workflow,
        "_locked_analysis",
        lambda *_: _return((ANALYSIS_ROW, (_event(AnalysisEventType.APPROVED, 3),))),
    )
    with pytest.raises(InvalidQueryError):
        await repository.review(ANALYSIS_ID, "actor", "reason")


@pytest.mark.asyncio
async def test_repository_helpers_cover_draft_absence_and_database_errors() -> None:
    session = _Session(results=[[CALCULATED_ROW], None, ANALYSIS_ROW, [CALCULATED_ROW]])
    assert await workflow._events(session, ANALYSIS_ID) == (
        _event(AnalysisEventType.CALCULATED, 1),
    )
    locked = await workflow._locked_analysis(session, ANALYSIS_ID)
    assert locked is not None and locked[0]["analysis_id"] == ANALYSIS_ID
    assert (
        await workflow._locked_analysis(_Session(results=[None, None]), ANALYSIS_ID)
        is None
    )
    created = await workflow.SqlAlchemyAnalysisWorkflowRepository(
        _Database(_Session(results=[ANALYSIS_ROW], scalars=[101]))
    ).create_draft(ANALYSIS_ID, 101)
    assert created is not None and created.status is AnalysisStatus.DRAFT
    missing = await workflow.SqlAlchemyAnalysisWorkflowRepository(
        _Database(_Session(scalars=[None]))
    ).create_draft(ANALYSIS_ID, 404)
    assert missing is None
    with pytest.raises(PersistenceUnavailableError):
        await workflow.SqlAlchemyAnalysisWorkflowRepository(
            _Database(_Session(scalars=[SQLAlchemyError("unavailable")]))
        ).create_draft(ANALYSIS_ID, 101)


@pytest.mark.asyncio
async def test_repository_transition_absence_invalid_execution_and_database_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = workflow.SqlAlchemyAnalysisWorkflowRepository(_Database(_Session()))
    monkeypatch.setattr(workflow, "_locked_analysis", lambda *_: _return(None))
    assert await repository.calculate(ANALYSIS_ID, EXECUTION_ID) is None
    assert await repository.review(ANALYSIS_ID, "actor", "reason") is None
    monkeypatch.setattr(
        workflow,
        "_locked_analysis",
        lambda *_: _return((ANALYSIS_ROW, ())),
    )
    repository._database.value.results = [{"match_id": 102, "status": "completed"}]
    assert await repository.calculate(ANALYSIS_ID, EXECUTION_ID) is None
    repository._database.value.results = [
        {"match_id": 101, "status": "technical_failure"}
    ]
    with pytest.raises(InvalidQueryError):
        await repository.calculate(ANALYSIS_ID, EXECUTION_ID)
    monkeypatch.setattr(
        workflow,
        "_locked_analysis",
        lambda *_: _return((ANALYSIS_ROW, (_event(AnalysisEventType.APPROVED, 3),))),
    )
    with pytest.raises(InvalidQueryError):
        await repository.calculate(ANALYSIS_ID, EXECUTION_ID)
    broken = workflow.SqlAlchemyAnalysisWorkflowRepository(
        _Database(_Session(results=[SQLAlchemyError("unavailable")]))
    )
    monkeypatch.setattr(
        workflow,
        "_locked_analysis",
        lambda *_: _return((ANALYSIS_ROW, ())),
    )
    with pytest.raises(PersistenceUnavailableError):
        await broken.calculate(ANALYSIS_ID, EXECUTION_ID)
    review_broken = workflow.SqlAlchemyAnalysisWorkflowRepository(
        _Database(_Session(results=[SQLAlchemyError("unavailable")]))
    )
    monkeypatch.setattr(
        workflow,
        "_locked_analysis",
        lambda *_: _return((ANALYSIS_ROW, (_event(AnalysisEventType.CALCULATED, 1),))),
    )
    with pytest.raises(PersistenceUnavailableError):
        await review_broken.review(ANALYSIS_ID, "actor", "reason")

    approval = workflow.SqlAlchemyAnalysisWorkflowRepository(_Database(_Session()))
    monkeypatch.setattr(workflow, "_locked_analysis", lambda *_: _return(None))
    assert await approval.approve(ANALYSIS_ID, "snapshot", "actor", "reason") is None
    monkeypatch.setattr(
        workflow,
        "_locked_analysis",
        lambda *_: _return((ANALYSIS_ROW, (_event(AnalysisEventType.APPROVED, 3),))),
    )
    with pytest.raises(InvalidQueryError):
        await approval.approve(ANALYSIS_ID, "snapshot", "actor", "reason")
    monkeypatch.setattr(
        workflow,
        "_locked_analysis",
        lambda *_: _return((ANALYSIS_ROW, (_event(AnalysisEventType.CALCULATED, 1),))),
    )
    with pytest.raises(InvalidQueryError):
        await approval.approve(ANALYSIS_ID, "snapshot", "actor", "reason")


@pytest.mark.asyncio
async def test_repository_approve_success_and_read_projections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot_row = {
        "snapshot_id": "snapshot",
        "analysis_id": ANALYSIS_ID,
        "payload": {"frozen": True},
        "snapshot_hash": "f" * 64,
        "created_at": NOW,
    }
    events = (
        _event(AnalysisEventType.CALCULATED, 1),
        _event(AnalysisEventType.REVIEWED, 2),
    )
    session = _Session(results=[EXECUTION_ROW, None, snapshot_row])
    repository = workflow.SqlAlchemyAnalysisWorkflowRepository(_Database(session))
    monkeypatch.setattr(
        workflow, "_locked_analysis", lambda *_: _return((ANALYSIS_ROW, events))
    )
    monkeypatch.setattr(
        workflow,
        "_events",
        lambda *_: _return(events + (_event(AnalysisEventType.APPROVED, 3),)),
    )
    monkeypatch.setattr(
        repository, "_snapshot_payload", lambda *_: _return({"frozen": True})
    )
    approved = await repository.approve(ANALYSIS_ID, "snapshot", "actor", "reason")
    assert approved is not None and approved[0].status is AnalysisStatus.APPROVED
    assert approved[1].snapshot_hash == "f" * 64
    monkeypatch.undo()

    reader = workflow.SqlAlchemyAnalysisWorkflowRepository(
        _Database(_Session(results=[ANALYSIS_ROW, [CALCULATED_ROW]]))
    )
    assert (await reader.get(ANALYSIS_ID)).status is AnalysisStatus.CALCULATED  # type: ignore[union-attr]
    assert await reader.get("missing") is None
    with pytest.raises(PersistenceUnavailableError):
        await workflow.SqlAlchemyAnalysisWorkflowRepository(
            _Database(_Session(results=[SQLAlchemyError("unavailable")]))
        ).get(ANALYSIS_ID)


@pytest.mark.asyncio
async def test_repository_list_and_snapshot_reads_include_missing_and_errors() -> None:
    snapshot_row = {
        "snapshot_id": "snapshot",
        "analysis_id": ANALYSIS_ID,
        "payload": {"frozen": True},
        "snapshot_hash": "f" * 64,
        "created_at": NOW,
    }
    listed = workflow.SqlAlchemyAnalysisWorkflowRepository(
        _Database(_Session(results=[[ANALYSIS_ROW], [CALCULATED_ROW]], scalars=[101]))
    )
    assert await listed.list_by_match(101) is not None
    assert (
        await workflow.SqlAlchemyAnalysisWorkflowRepository(
            _Database(_Session(scalars=[None]))
        ).list_by_match(404)
        is None
    )
    with pytest.raises(PersistenceUnavailableError):
        await workflow.SqlAlchemyAnalysisWorkflowRepository(
            _Database(_Session(scalars=[SQLAlchemyError("unavailable")]))
        ).list_by_match(101)
    snapshots = workflow.SqlAlchemyAnalysisWorkflowRepository(
        _Database(_Session(results=[snapshot_row, None]))
    )
    assert await snapshots.get_snapshot_by_analysis(ANALYSIS_ID) is not None
    assert await snapshots.get_snapshot("missing") is None
    with pytest.raises(PersistenceUnavailableError):
        await workflow.SqlAlchemyAnalysisWorkflowRepository(
            _Database(_Session(results=[SQLAlchemyError("unavailable")]))
        ).get_snapshot("snapshot")


@pytest.mark.asyncio
async def test_approval_rolls_back_when_snapshot_insert_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session(
        results=[EXECUTION_ROW, None, SQLAlchemyError("snapshot failure")]
    )
    repository = workflow.SqlAlchemyAnalysisWorkflowRepository(_Database(session))
    events = (
        _event(AnalysisEventType.CALCULATED, 1),
        _event(AnalysisEventType.REVIEWED, 2),
    )
    monkeypatch.setattr(
        workflow, "_locked_analysis", lambda *_: _return((ANALYSIS_ROW, events))
    )
    monkeypatch.setattr(
        workflow,
        "_events",
        lambda *_: _return(events + (_event(AnalysisEventType.APPROVED, 3),)),
    )
    monkeypatch.setattr(
        repository, "_snapshot_payload", lambda *_: _return({"frozen": True})
    )
    with pytest.raises(PersistenceUnavailableError):
        await repository.approve(ANALYSIS_ID, "snapshot", "actor", "reason")
    assert session.rolled_back is True


@pytest.mark.asyncio
async def test_snapshot_payload_freezes_execution_and_sample_ids() -> None:
    match_row = {
        "id": 101,
        "played_on": date(2026, 9, 10),
        "season_id": 4,
        "season_label": "2026",
        "competition_id": 3,
        "competition_name": "League",
        "home_team_id": 8,
        "home_team_name": "Home",
        "away_team_id": 9,
        "away_team_name": "Away",
    }
    catalog = {
        "catalog_id": "lvfi-mvp@1.0.0",
        "schema_version": 1,
        "payload": {"catalog": True},
        "content_hash": "d" * 64,
        "created_at": NOW,
    }
    revision = {
        "id": 4,
        "catalog_id": "lvfi-mvp@1.0.0",
        "catalog_hash": "d" * 64,
        "scope": "match",
        "parameter_code": "sample_size",
        "value": 10,
        "competition_id": None,
        "match_id": 101,
        "actor": "admin",
        "reason": "set",
        "replaces_revision_id": None,
        "revision_hash": "e" * 64,
        "created_at": NOW,
    }
    session = _Session([match_row, catalog, [revision]])
    repository = workflow.SqlAlchemyAnalysisWorkflowRepository(_Database(session))
    payload = await repository._snapshot_payload(
        repository._database.value,
        ANALYSIS_ROW,
        EXECUTION_ROW,
        (
            _event(AnalysisEventType.CALCULATED, 1),
            _event(AnalysisEventType.REVIEWED, 2),
            _event(AnalysisEventType.APPROVED, 3),
        ),
    )
    assert payload["pricing_execution"]["sample_match_ids"] == [2, 101]
    assert payload["pricing_execution"]["warnings"] == ["source warning"]
    compiled_parameters = [
        statement.compile().params for statement in session.statements
    ]
    assert any(CATALOG_ID in values.values() for values in compiled_parameters)
    assert payload["effective_configuration"]["catalog"]["catalog_id"] == CATALOG_ID
    frozen = deepcopy(payload)
    EXECUTION_ROW["public_parameters"]["requested_count"] = 20
    revision["value"] = 20
    assert payload == frozen
    EXECUTION_ROW["public_parameters"]["requested_count"] = 10


@pytest.mark.asyncio
async def test_effective_configuration_isolated_to_authorized_catalog() -> None:
    selected_catalog = {
        "catalog_id": CATALOG_ID,
        "schema_version": 1,
        "payload": {"catalog": "authorized"},
        "content_hash": "d" * 64,
        "created_at": NOW,
    }
    selected_revision = {
        "id": 8,
        "catalog_id": CATALOG_ID,
        "catalog_hash": "d" * 64,
        "scope": "global",
        "parameter_code": "sample_size",
        "value": 10,
        "competition_id": None,
        "match_id": None,
        "actor": "admin",
        "reason": "authorized",
        "replaces_revision_id": None,
        "revision_hash": "e" * 64,
        "created_at": NOW,
    }
    discarded_revision = {
        **selected_revision,
        "id": 7,
        "scope": "competition",
        "competition_id": 3,
    }
    other_catalog = {
        **selected_catalog,
        "catalog_id": "other@1",
        "payload": {"catalog": "other"},
    }
    other_revision = {**selected_revision, "catalog_id": "other@1", "value": 20}

    class _CatalogSession:
        async def execute(self, statement: Any) -> _Result:
            parameters = statement.compile().params
            rendered = str(statement)
            if "configuration_catalogs" in rendered:
                assert CATALOG_ID in parameters.values()
                assert other_catalog["catalog_id"] != CATALOG_ID
                return _Result(selected_catalog)
            assert "configuration_revisions" in rendered
            assert CATALOG_ID in parameters.values()
            assert other_revision["catalog_id"] != CATALOG_ID
            return _Result([selected_revision, discarded_revision])

    repository = workflow.SqlAlchemyAnalysisWorkflowRepository(_Database(_Session()))
    value = await repository._effective_configuration(
        _CatalogSession(), {"match_id": 101, "competition": {"id": 3}}
    )
    assert value["catalog"]["payload"] == {"catalog": "authorized"}
    assert value["values"] == {"sample_size": 10}
    assert value["discarded_revisions"][0]["revision_id"] == 8


class _FrozenSnapshotRepository:
    def __init__(self) -> None:
        self.source = {
            "configuration": {"sample_size": 10},
            "execution": {"result": "x"},
        }
        self.value = Analysis(
            ANALYSIS_ID,
            101,
            AnalysisStatus.CALCULATED,
            NOW,
            (
                _event(AnalysisEventType.CALCULATED, 1),
                _event(AnalysisEventType.REVIEWED, 2),
            ),
        )
        self.snapshot_value: AnalysisSnapshot | None = None

    async def approve(
        self, _: str, snapshot_id: str, __: str, ___: str
    ) -> tuple[Analysis, AnalysisSnapshot]:
        payload = deepcopy(self.source)
        self.snapshot_value = AnalysisSnapshot(
            snapshot_id, ANALYSIS_ID, payload, snapshot_hash(payload), NOW
        )
        return self.value, self.snapshot_value

    async def get_snapshot_by_analysis(self, _: str) -> AnalysisSnapshot | None:
        return self.snapshot_value


@pytest.mark.asyncio
async def test_service_returns_snapshot_unchanged_after_mutable_source_changes() -> (
    None
):
    repository = _FrozenSnapshotRepository()
    service = AnalysisWorkflowService(repository)  # type: ignore[arg-type]
    _, snapshot = await service.approve(ANALYSIS_ID, "actor", "reason")
    repository.source["configuration"]["sample_size"] = 20
    repository.source["execution"]["result"] = "later"
    loaded = await service.snapshot_for_analysis(ANALYSIS_ID)
    assert loaded == snapshot
    assert loaded.payload == {
        "configuration": {"sample_size": 10},
        "execution": {"result": "x"},
    }


async def _return(value: Any) -> Any:
    return value
