from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from lvfi_api.application.pdf_reports import (
    PdfReportService,
    PlaywrightPdfRenderer,
    report_html,
)
from lvfi_api.domain.analysis_workflow import AnalysisSnapshot, snapshot_hash
from lvfi_api.domain.errors import PersistenceUnavailableError, ResourceNotFoundError
from lvfi_api.domain.pdf_reports import PDF_TEMPLATE_VERSION, PdfArtifact
from lvfi_api.main import create_app
from lvfi_api.persistence.pdf_reports import SqlAlchemyPdfReportRepository
from lvfi_api.presentation.pdf_report_routes import get_pdf_report_service

NOW = datetime(2026, 9, 11, tzinfo=UTC)
SNAPSHOT_ID = "00000000-0000-4000-8000-000000000003"


def _snapshot() -> AnalysisSnapshot:
    payload = {
        "analysis": {
            "analysis_id": "analysis",
            "match": {
                "home_team": {"display_name": "Casa"},
                "away_team": {"display_name": "Fora"},
                "competition": {"display_name": "Liga"},
                "played_on": "2026-09-11",
            },
        },
        "pricing_execution": {
            "canonical_result": {"result": 1},
            "sample_match_ids": [1, 2],
            "warnings": ["sample"],
            "method_one_version": "1",
            "pricing_engine_version": "1",
            "distribution_version": "1",
            "schema_version": 1,
            "public_parameters": {},
        },
        "effective_configuration": {},
        "events": [{"event_type": "approved", "actor": "local-admin"}],
    }
    return AnalysisSnapshot(
        SNAPSHOT_ID, "analysis", payload, snapshot_hash(payload), NOW
    )


class Repository:
    def __init__(self) -> None:
        self.value = _snapshot()
        self.artifacts: dict[str, PdfArtifact] = {}

    async def snapshot(self, snapshot_id: str) -> AnalysisSnapshot | None:
        return self.value if snapshot_id == SNAPSHOT_ID else None

    async def artifact(
        self, snapshot_id: str, template_version: str
    ) -> PdfArtifact | None:
        return (
            self.artifacts.get(snapshot_id)
            if template_version == PDF_TEMPLATE_VERSION
            else None
        )

    async def create(self, artifact: PdfArtifact) -> PdfArtifact | None:
        if artifact.snapshot_id in self.artifacts:
            return None
        self.artifacts[artifact.snapshot_id] = artifact
        return artifact

    async def get_artifact(self, artifact_id: str) -> PdfArtifact | None:
        return next(
            (x for x in self.artifacts.values() if x.artifact_id == artifact_id), None
        )

    async def list_artifacts(self, snapshot_id: str) -> tuple[PdfArtifact, ...]:
        return tuple(x for x in self.artifacts.values() if x.snapshot_id == snapshot_id)


class Renderer:
    def render(self, snapshot: AnalysisSnapshot) -> bytes:
        assert snapshot.snapshot_id == SNAPSHOT_ID
        return b"%PDF-1.7\nreport"


@pytest.mark.asyncio
async def test_report_uses_only_frozen_snapshot_and_is_idempotent(
    tmp_path: Path,
) -> None:
    repository = Repository()
    service = PdfReportService(repository, Renderer(), tmp_path)
    artifact = await service.generate(SNAPSHOT_ID)
    assert await service.generate(SNAPSHOT_ID) == artifact
    assert service.file_path(artifact).read_bytes().startswith(b"%PDF-")
    assert await service.list(SNAPSHOT_ID) == (artifact,)
    assert await service.get(artifact.artifact_id) == artifact
    with pytest.raises(ResourceNotFoundError):
        await service.generate("00000000-0000-4000-8000-000000000999")


@pytest.mark.asyncio
async def test_report_refuses_corrupt_artifact(tmp_path: Path) -> None:
    repository = Repository()
    service = PdfReportService(repository, Renderer(), tmp_path)
    artifact = await service.generate(SNAPSHOT_ID)
    (tmp_path / artifact.storage_path).write_bytes(b"corrupt")
    with pytest.raises(Exception, match="integrity"):
        service.file_path(artifact)


def test_html_includes_required_frozen_evidence() -> None:
    value = report_html(_snapshot())
    for required in (
        "Casa × Fora",
        "Resumo e resultados",
        "Amostras e warnings",
        "local-admin",
        PDF_TEMPLATE_VERSION,
    ):
        assert required in value


def test_playwright_generates_a_real_deterministic_nonempty_pdf() -> None:
    root = Path(__file__).parents[3]
    renderer = PlaywrightPdfRenderer(root / "scripts/local/render-lvfi-pdf.mjs")
    value = renderer.render(_snapshot())
    repeated = renderer.render(_snapshot())
    assert value == repeated
    assert value.count(b"/Type /Page\n") == 1
    assert value.startswith(b"%PDF-")
    assert len(value) > 1000


class _Result:
    def __init__(self, value: Any) -> None:
        self.value = value

    def mappings(self) -> _Result:
        return self

    def one_or_none(self) -> Any:
        return self.value

    def one(self) -> Any:
        return self.value

    def all(self) -> list[Any]:
        return self.value if isinstance(self.value, list) else []


class _Session:
    def __init__(self, values: list[Any]) -> None:
        self.values = values

    async def execute(self, _: Any) -> _Result:
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return _Result(value)


class _Database:
    def __init__(self, values: list[Any]) -> None:
        self.values = values

    @asynccontextmanager
    async def session(self) -> Any:
        yield _Session(self.values)


def _row() -> dict[str, Any]:
    return {
        "artifact_id": "00000000-0000-4000-8000-000000000004",
        "snapshot_id": SNAPSHOT_ID,
        "template_version": PDF_TEMPLATE_VERSION,
        "sha256": "a" * 64,
        "storage_path": f"{SNAPSHOT_ID}/{PDF_TEMPLATE_VERSION}.pdf",
        "created_at": NOW,
    }


@pytest.mark.asyncio
async def test_sqlalchemy_pdf_repository_reads_writes_and_maps_errors() -> None:
    snapshot_row = {
        "snapshot_id": SNAPSHOT_ID,
        "analysis_id": "analysis",
        "payload": _snapshot().payload,
        "snapshot_hash": _snapshot().snapshot_hash,
        "created_at": NOW,
    }
    repository = SqlAlchemyPdfReportRepository(
        _Database([snapshot_row, _row(), _row(), _row(), [_row()]])
    )
    assert (await repository.snapshot(SNAPSHOT_ID)) is not None
    assert (await repository.artifact(SNAPSHOT_ID, PDF_TEMPLATE_VERSION)) is not None
    artifact = await repository.create(PdfArtifact(**_row()))
    assert artifact is not None
    assert (await repository.get_artifact(artifact.artifact_id)) == artifact
    assert await repository.list_artifacts(SNAPSHOT_ID) == (artifact,)
    for method, args in (
        ("snapshot", (SNAPSHOT_ID,)),
        ("artifact", (SNAPSHOT_ID, PDF_TEMPLATE_VERSION)),
        ("create", (artifact,)),
        ("get_artifact", (artifact.artifact_id,)),
        ("list_artifacts", (SNAPSHOT_ID,)),
    ):
        broken = SqlAlchemyPdfReportRepository(
            _Database([SQLAlchemyError("unavailable")])
        )
        with pytest.raises(PersistenceUnavailableError):
            await getattr(broken, method)(*args)

    duplicate = SqlAlchemyPdfReportRepository(
        _Database([IntegrityError("duplicate", {}, Exception("duplicate"))])
    )
    assert await duplicate.create(artifact) is None


class _UnavailableRenderer:
    def render(self, _: AnalysisSnapshot) -> bytes:
        raise OSError("renderer unavailable")


class _CountingRenderer:
    def __init__(self) -> None:
        self.calls = 0

    def render(self, _: AnalysisSnapshot) -> bytes:
        self.calls += 1
        return b"%PDF-1.7\nserialized"


class _NoCreateRepository(Repository):
    async def create(self, _: PdfArtifact) -> PdfArtifact | None:
        return None


class _ConcurrentRepository(_NoCreateRepository):
    async def create(self, artifact: PdfArtifact) -> PdfArtifact | None:
        self.artifacts[artifact.snapshot_id] = artifact
        return None


@pytest.mark.asyncio
async def test_service_maps_operational_failures_and_absences(tmp_path: Path) -> None:
    repository = Repository()
    service = PdfReportService(repository, _UnavailableRenderer(), tmp_path)
    with pytest.raises(PersistenceUnavailableError, match="renderer"):
        await service.generate(SNAPSHOT_ID)

    unavailable_storage = tmp_path / "not-a-directory"
    unavailable_storage.write_text("occupied", encoding="utf-8")
    service = PdfReportService(repository, Renderer(), unavailable_storage)
    with pytest.raises(PersistenceUnavailableError, match="storage"):
        await service.generate(SNAPSHOT_ID)

    no_create = PdfReportService(_NoCreateRepository(), Renderer(), tmp_path)
    with pytest.raises(PersistenceUnavailableError, match="write failed"):
        await no_create.generate(SNAPSHOT_ID)
    with pytest.raises(ResourceNotFoundError):
        await no_create.get("00000000-0000-4000-8000-000000000999")
    with pytest.raises(ResourceNotFoundError):
        await no_create.list("00000000-0000-4000-8000-000000000999")

    missing_service = PdfReportService(
        _NoCreateRepository(), Renderer(), tmp_path / "empty-storage"
    )
    missing = PdfArtifact(**_row())
    with pytest.raises(ResourceNotFoundError, match="file"):
        missing_service.file_path(missing)
    outside = PdfArtifact(
        missing.artifact_id,
        missing.snapshot_id,
        missing.template_version,
        missing.sha256,
        "../outside.pdf",
        missing.created_at,
    )
    with pytest.raises(ResourceNotFoundError, match="file"):
        missing_service.file_path(outside)

    concurrent = PdfReportService(_ConcurrentRepository(), Renderer(), tmp_path)
    assert (await concurrent.generate(SNAPSHOT_ID)).snapshot_id == SNAPSHOT_ID


@pytest.mark.asyncio
async def test_generation_serializes_the_same_snapshot(tmp_path: Path) -> None:
    import asyncio

    renderer = _CountingRenderer()
    service = PdfReportService(Repository(), renderer, tmp_path)
    artifacts = await asyncio.gather(
        service.generate(SNAPSHOT_ID), service.generate(SNAPSHOT_ID)
    )
    assert artifacts[0] == artifacts[1]
    assert renderer.calls == 1


@pytest.mark.asyncio
async def test_renderer_rejects_failed_and_non_pdf_browser_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import lvfi_api.application.pdf_reports as reports

    renderer = PlaywrightPdfRenderer(tmp_path / "renderer.mjs")
    monkeypatch.setattr(
        reports,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stderr="not started"),
    )
    with pytest.raises(OSError, match="failed"):
        renderer.render(_snapshot())

    def non_pdf(command: list[str], **_: Any) -> SimpleNamespace:
        Path(command[-1]).write_bytes(b"not-a-pdf")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(reports, "run", non_pdf)
    with pytest.raises(OSError, match="did not produce"):
        renderer.render(_snapshot())


@pytest.mark.asyncio
async def test_route_service_composition_and_http_contract(
    settings: Any, database: Any, tmp_path: Path
) -> None:
    app = create_app(settings, database)
    with pytest.raises(PersistenceUnavailableError, match="database"):
        await get_pdf_report_service(SimpleNamespace(app=app))

    class _SessionDatabase:
        def session(self) -> Any:
            raise AssertionError("not called while composing service")

    app.state.database = _SessionDatabase()
    settings.pdf_storage_dir = None
    with pytest.raises(PersistenceUnavailableError, match="storage"):
        await get_pdf_report_service(SimpleNamespace(app=app))
    settings.pdf_storage_dir = tmp_path
    assert isinstance(
        await get_pdf_report_service(SimpleNamespace(app=app)), PdfReportService
    )

    app.state.database = database
    app.state.pdf_report_service = PdfReportService(Repository(), Renderer(), tmp_path)
    with TestClient(app) as client:
        created = client.post(f"/analysis-snapshots/{SNAPSHOT_ID}/pdfs")
        history = client.get(f"/analysis-snapshots/{SNAPSHOT_ID}/pdfs")
        downloaded = client.get(
            f"/analysis-pdfs/{created.json()['artifact_id']}/download"
        )
    assert created.status_code == 201
    assert history.status_code == 200 and len(history.json()["artifacts"]) == 1
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "application/pdf"
