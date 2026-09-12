"""Generate one deterministic, append-only PDF projection per approved snapshot."""

from __future__ import annotations

from asyncio import Lock
from hashlib import sha256
from html import escape
from pathlib import Path
from subprocess import run
from typing import Protocol
from uuid import uuid4

from lvfi_api.domain.analysis_workflow import AnalysisSnapshot
from lvfi_api.domain.errors import PersistenceUnavailableError, ResourceNotFoundError
from lvfi_api.domain.pdf_reports import PDF_TEMPLATE_VERSION, PdfArtifact


class PdfReportRepository(Protocol):
    async def snapshot(self, snapshot_id: str) -> AnalysisSnapshot | None: ...

    async def artifact(
        self, snapshot_id: str, template_version: str
    ) -> PdfArtifact | None: ...

    async def create(self, artifact: PdfArtifact) -> PdfArtifact | None: ...

    async def get_artifact(self, artifact_id: str) -> PdfArtifact | None: ...

    async def list_artifacts(self, snapshot_id: str) -> tuple[PdfArtifact, ...]: ...


class PdfRenderer(Protocol):
    def render(self, snapshot: AnalysisSnapshot) -> bytes: ...


class PlaywrightPdfRenderer:
    """Invoke the pinned local Playwright renderer, never a browser client."""

    def __init__(self, script: Path) -> None:
        self._script = script.resolve()

    def render(self, snapshot: AnalysisSnapshot) -> bytes:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory(prefix="lvfi-pdf-") as temporary:
            root = Path(temporary)
            source, target = root / "report.html", root / "report.pdf"
            source.write_text(report_html(snapshot), encoding="utf-8", newline="\n")
            completed = run(
                ["node", str(self._script), str(source), str(target)],
                check=False,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=60,
            )
            if completed.returncode != 0 or not target.is_file():
                raise OSError(
                    "Playwright PDF rendering failed: "
                    + (completed.stderr or "").strip()[-1200:]
                )
            value = target.read_bytes()
        if not value.startswith(b"%PDF-"):
            raise OSError("Playwright did not produce a PDF")
        return value


def _section(title: str, value: object) -> str:
    return f"<section><h2>{escape(title)}</h2><pre>{escape(str(value))}</pre></section>"


def report_html(snapshot: AnalysisSnapshot) -> str:
    """Build a stable A4 HTML document solely from frozen snapshot fields."""
    payload = snapshot.payload
    analysis = payload.get("analysis", {})
    execution = payload.get("pricing_execution", {})
    match = analysis.get("match", {}) if isinstance(analysis, dict) else {}
    title = "LVFI · PDF-resumo de análise aprovada"
    home_name = match.get("home_team", {}).get("display_name", "—")
    away_name = match.get("away_team", {}).get("display_name", "—")
    identification = {
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_sha256": snapshot.snapshot_hash,
        "analysis_id": analysis.get("analysis_id")
        if isinstance(analysis, dict)
        else None,
        "partida": f"{home_name} × {away_name}",
        "competição": match.get("competition", {}).get("display_name", "—"),
        "data": match.get("played_on", "—"),
    }
    sections = "".join(
        (
            _section("Identificação", identification),
            _section(
                "Resumo e resultados persistidos", execution.get("canonical_result", {})
            ),
            _section(
                "Metodologia, versões e filtros",
                {
                    "versions": {
                        key: execution.get(key)
                        for key in (
                            "pricing_engine_version",
                            "distribution_version",
                            "method_one_version",
                            "schema_version",
                        )
                    },
                    "parameters": execution.get("public_parameters", {}),
                    "configuration": payload.get("effective_configuration", {}),
                },
            ),
            _section(
                "Amostras e warnings",
                {
                    "sample_match_ids": execution.get("sample_match_ids", []),
                    "warnings": execution.get("warnings", []),
                    "responsável": next(
                        (
                            event.get("actor")
                            for event in reversed(payload.get("events", []))
                            if event.get("event_type") == "approved"
                        ),
                        None,
                    ),
                },
            ),
        )
    )
    styles = (
        "@page{size:A4;margin:16mm}"
        "body{font-family:Arial,sans-serif;color:#18212b;font-size:10pt;line-height:1.35}"
        "h1{font-size:18pt;margin:0 0 4mm}"
        "h2{font-size:12pt;border-bottom:1px solid #73808c;"
        "padding-bottom:2mm;break-after:avoid}"
        "section{break-inside:avoid;margin:0 0 5mm}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7f8;padding:3mm;margin:0}"
        "footer{position:fixed;bottom:0;font-size:8pt;color:#52606d}"
    )
    return (
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><style>"
        + styles
        + "</style></head><body><h1>"
        + escape(title)
        + "</h1><p>Template "
        + PDF_TEMPLATE_VERSION
        + " · conteúdo derivado exclusivamente do snapshot aprovado.</p>"
        + sections
        + "<footer>LVFI · snapshot imutável · "
        + escape(snapshot.snapshot_id)
        + "</footer></body></html>"
    )


class PdfReportService:
    _generation_locks: dict[tuple[str, str], Lock] = {}
    _generation_locks_guard = Lock()

    def __init__(
        self, repository: PdfReportRepository, renderer: PdfRenderer, storage_dir: Path
    ) -> None:
        self._repository = repository
        self._renderer = renderer
        self._storage_dir = storage_dir

    async def generate(self, snapshot_id: str) -> PdfArtifact:
        key = (snapshot_id, PDF_TEMPLATE_VERSION)
        async with self._generation_locks_guard:
            lock = self._generation_locks.setdefault(key, Lock())
        async with lock:
            return await self._generate_once(snapshot_id)

    async def _generate_once(self, snapshot_id: str) -> PdfArtifact:
        snapshot = await self._repository.snapshot(snapshot_id)
        if snapshot is None:
            raise ResourceNotFoundError("approved analysis snapshot")
        existing = await self._repository.artifact(snapshot_id, PDF_TEMPLATE_VERSION)
        if existing is not None:
            return existing
        try:
            content = self._renderer.render(snapshot)
        except OSError as exc:
            raise PersistenceUnavailableError("PDF renderer unavailable") from exc
        artifact_id = str(uuid4())
        relative = Path(snapshot_id) / f"{PDF_TEMPLATE_VERSION}.pdf"
        target = self._storage_dir / relative
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        except OSError as exc:
            raise PersistenceUnavailableError(
                "PDF artifact storage unavailable"
            ) from exc
        artifact = PdfArtifact(
            artifact_id=artifact_id,
            snapshot_id=snapshot_id,
            template_version=PDF_TEMPLATE_VERSION,
            sha256=sha256(content).hexdigest(),
            storage_path=relative.as_posix(),
            created_at=snapshot.created_at,
        )
        created = await self._repository.create(artifact)
        if created is None:
            resolved = await self._repository.artifact(
                snapshot_id, PDF_TEMPLATE_VERSION
            )
            if resolved is not None:
                return resolved
            raise PersistenceUnavailableError("PDF artifact write failed")
        return created

    async def get(self, artifact_id: str) -> PdfArtifact:
        artifact = await self._repository.get_artifact(artifact_id)
        if artifact is None:
            raise ResourceNotFoundError("PDF artifact")
        return artifact

    async def list(self, snapshot_id: str) -> tuple[PdfArtifact, ...]:
        if await self._repository.snapshot(snapshot_id) is None:
            raise ResourceNotFoundError("approved analysis snapshot")
        return await self._repository.list_artifacts(snapshot_id)

    def file_path(self, artifact: PdfArtifact) -> Path:
        path = (self._storage_dir / artifact.storage_path).resolve()
        if self._storage_dir.resolve() not in path.parents or not path.is_file():
            raise ResourceNotFoundError("PDF artifact file")
        if sha256(path.read_bytes()).hexdigest() != artifact.sha256:
            raise PersistenceUnavailableError("PDF artifact integrity check failed")
        return path
