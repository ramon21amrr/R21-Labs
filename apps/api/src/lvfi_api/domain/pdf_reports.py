"""Immutable APP-018 PDF artifact contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

PDF_TEMPLATE_VERSION = "lvfi-summary-1"


@dataclass(frozen=True, slots=True)
class PdfArtifact:
    artifact_id: str
    snapshot_id: str
    template_version: str
    sha256: str
    storage_path: str
    created_at: datetime
