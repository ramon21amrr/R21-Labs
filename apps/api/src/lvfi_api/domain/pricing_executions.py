"""Immutable public contracts for auditable Method One execution records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class PricingExecutionStatus(StrEnum):
    """Terminal, append-only outcomes for one execution attempt."""

    COMPLETED = "completed"
    BLOCKED_SAMPLE_INCOMPLETE = "blocked_sample_incomplete"
    TECHNICAL_FAILURE = "technical_failure"


@dataclass(frozen=True, slots=True)
class PricingExecution:
    """A safe, immutable audit record; canonical payloads are never recomputed."""

    execution_id: str
    match_id: int
    status: PricingExecutionStatus
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


@dataclass(frozen=True, slots=True)
class PricingExecutionDraft:
    """Values assembled before one transactional insert into the audit ledger."""

    execution_id: str
    match_id: int
    status: PricingExecutionStatus
    finalized_at: datetime
    correlation_id: str
    idempotency_key: str | None
    sample_fingerprint: str
    input_fingerprint: str | None
    result_fingerprint: str | None
    pricing_engine_version: str
    distribution_version: str
    method_one_version: str
    schema_version: int
    public_parameters: dict[str, Any]
    canonical_input: str | None
    canonical_result: str | None
    failure_code: str | None
