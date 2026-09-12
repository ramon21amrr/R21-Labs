"""PostgreSQL persistence for append-only APP-018 report artifacts."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from sqlalchemy import insert, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from lvfi_api.domain.analysis_workflow import AnalysisSnapshot
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.pdf_reports import PdfArtifact
from lvfi_api.persistence.analysis_workflow import _snapshot
from lvfi_api.persistence.historical_models import (
    analysis_pdf_artifacts,
    analysis_workflow_snapshots,
)
from lvfi_api.persistence.historical_queries import SessionProvider


def _artifact(row: RowMapping) -> PdfArtifact:
    return PdfArtifact(
        artifact_id=cast(str, row["artifact_id"]),
        snapshot_id=cast(str, row["snapshot_id"]),
        template_version=cast(str, row["template_version"]),
        sha256=cast(str, row["sha256"]),
        storage_path=cast(str, row["storage_path"]),
        created_at=cast(datetime, row["created_at"]),
    )


class SqlAlchemyPdfReportRepository:
    def __init__(self, database: SessionProvider) -> None:
        self._database = database

    async def snapshot(self, snapshot_id: str) -> AnalysisSnapshot | None:
        try:
            async with self._database.session() as session:
                row = (
                    (
                        await session.execute(
                            select(analysis_workflow_snapshots).where(
                                analysis_workflow_snapshots.c.snapshot_id == snapshot_id
                            )
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("PDF snapshot unavailable") from exc
        return _snapshot(row) if row is not None else None

    async def artifact(
        self, snapshot_id: str, template_version: str
    ) -> PdfArtifact | None:
        try:
            async with self._database.session() as session:
                row = (
                    (
                        await session.execute(
                            select(analysis_pdf_artifacts).where(
                                analysis_pdf_artifacts.c.snapshot_id == snapshot_id,
                                analysis_pdf_artifacts.c.template_version
                                == template_version,
                            )
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("PDF artifact unavailable") from exc
        return _artifact(row) if row is not None else None

    async def create(self, artifact: PdfArtifact) -> PdfArtifact | None:
        try:
            async with self._database.session() as session:
                row = (
                    (
                        await session.execute(
                            insert(analysis_pdf_artifacts)
                            .values(
                                artifact_id=artifact.artifact_id,
                                snapshot_id=artifact.snapshot_id,
                                template_version=artifact.template_version,
                                sha256=artifact.sha256,
                                storage_path=artifact.storage_path,
                            )
                            .returning(analysis_pdf_artifacts)
                        )
                    )
                    .mappings()
                    .one()
                )
        except IntegrityError:
            return None
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("PDF artifact write failed") from exc
        return _artifact(row)

    async def get_artifact(self, artifact_id: str) -> PdfArtifact | None:
        try:
            async with self._database.session() as session:
                row = (
                    (
                        await session.execute(
                            select(analysis_pdf_artifacts).where(
                                analysis_pdf_artifacts.c.artifact_id == artifact_id
                            )
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("PDF artifact unavailable") from exc
        return _artifact(row) if row is not None else None

    async def list_artifacts(self, snapshot_id: str) -> tuple[PdfArtifact, ...]:
        try:
            async with self._database.session() as session:
                rows = (
                    (
                        await session.execute(
                            select(analysis_pdf_artifacts)
                            .where(analysis_pdf_artifacts.c.snapshot_id == snapshot_id)
                            .order_by(
                                analysis_pdf_artifacts.c.created_at.asc(),
                                analysis_pdf_artifacts.c.artifact_id.asc(),
                            )
                        )
                    )
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "PDF artifact history unavailable"
            ) from exc
        return tuple(_artifact(row) for row in rows)
