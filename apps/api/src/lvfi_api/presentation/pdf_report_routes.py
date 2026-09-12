"""Protected HTTP contract for approved-snapshot PDF artifacts."""
# ruff: noqa: B008

from __future__ import annotations

from datetime import datetime
from typing import cast

from fastapi import APIRouter, Depends, Path, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict

from lvfi_api.application.pdf_reports import PdfReportService, PlaywrightPdfRenderer
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.pdf_reports import PdfArtifact
from lvfi_api.persistence.pdf_reports import SqlAlchemyPdfReportRepository

router = APIRouter(tags=["PDF reports"])


class PdfArtifactResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artifact_id: str
    snapshot_id: str
    template_version: str
    sha256: str
    created_at: datetime

    @classmethod
    def from_contract(cls, value: PdfArtifact) -> PdfArtifactResponse:
        return cls(**{key: getattr(value, key) for key in cls.model_fields})


class PdfArtifactHistoryResponse(BaseModel):
    artifacts: list[PdfArtifactResponse]


async def get_pdf_report_service(request: Request) -> PdfReportService:
    injected = getattr(request.app.state, "pdf_report_service", None)
    if injected is not None:
        return cast(PdfReportService, injected)
    database = request.app.state.database
    settings = request.app.state.settings
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("PDF report database unavailable")
    if settings.pdf_storage_dir is None:
        raise PersistenceUnavailableError("PDF artifact storage is not configured")
    return PdfReportService(
        SqlAlchemyPdfReportRepository(database),
        PlaywrightPdfRenderer(settings.pdf_renderer_script),
        settings.pdf_storage_dir,
    )


@router.post(
    "/analysis-snapshots/{snapshot_id}/pdfs",
    response_model=PdfArtifactResponse,
    status_code=201,
)
async def create_pdf(
    snapshot_id: str = Path(min_length=36, max_length=36),
    service: PdfReportService = Depends(get_pdf_report_service),
) -> PdfArtifactResponse:
    return PdfArtifactResponse.from_contract(await service.generate(snapshot_id))


@router.get(
    "/analysis-snapshots/{snapshot_id}/pdfs", response_model=PdfArtifactHistoryResponse
)
async def list_pdfs(
    snapshot_id: str = Path(min_length=36, max_length=36),
    service: PdfReportService = Depends(get_pdf_report_service),
) -> PdfArtifactHistoryResponse:
    return PdfArtifactHistoryResponse(
        artifacts=[
            PdfArtifactResponse.from_contract(value)
            for value in await service.list(snapshot_id)
        ]
    )


@router.get("/analysis-pdfs/{artifact_id}/download")
async def download_pdf(
    artifact_id: str = Path(min_length=36, max_length=36),
    service: PdfReportService = Depends(get_pdf_report_service),
) -> FileResponse:
    artifact = await service.get(artifact_id)
    return FileResponse(
        service.file_path(artifact),
        media_type="application/pdf",
        filename=f"lvfi-{artifact.snapshot_id}.pdf",
    )
