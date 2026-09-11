"""Immutable contracts for the APP-015 review, approval and snapshot workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class AnalysisStatus(StrEnum):
    DRAFT = "draft"
    CALCULATED = "calculated"
    APPROVED = "approved"


class AnalysisEventType(StrEnum):
    CALCULATED = "calculated"
    REVIEWED = "reviewed"
    APPROVED = "approved"


@dataclass(frozen=True, slots=True)
class AnalysisEvent:
    event_id: int
    event_type: AnalysisEventType
    execution_id: str | None
    actor: str | None
    reason: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Analysis:
    analysis_id: str
    match_id: int
    status: AnalysisStatus
    created_at: datetime
    events: tuple[AnalysisEvent, ...]


@dataclass(frozen=True, slots=True)
class AnalysisSnapshot:
    snapshot_id: str
    analysis_id: str
    payload: dict[str, Any]
    snapshot_hash: str
    created_at: datetime


def canonical_json(value: object) -> str:
    """Stable JSON bytes used for the immutable snapshot fingerprint."""
    from json import dumps

    return dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def snapshot_hash(value: object) -> str:
    from hashlib import sha256

    return sha256(canonical_json(value).encode("utf-8")).hexdigest()
