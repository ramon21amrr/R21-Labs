"""Immutable contracts for controlled replay of Method One executions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class PricingExecutionReproductionOutcome(StrEnum):
    """Terminal outcomes of one append-only reproduction attempt."""

    EXACT_MATCH = "exact_match"
    MISMATCH = "mismatch"
    INCOMPATIBLE_VERSION = "incompatible_version"
    BLOCKED = "blocked"
    TECHNICAL_FAILURE = "technical_failure"


@dataclass(frozen=True, slots=True)
class PricingExecutionReproduction:
    """Public-safe, immutable record linked to its original execution."""

    reproduction_id: str
    execution_id: str
    outcome: PricingExecutionReproductionOutcome
    created_at: datetime
    finalized_at: datetime
    correlation_id: str
    original_input_fingerprint: str | None
    reproduced_input_fingerprint: str | None
    original_result_fingerprint: str | None
    reproduced_result_fingerprint: str | None
    original_pricing_engine_version: str
    current_pricing_engine_version: str
    original_distribution_version: str
    current_distribution_version: str
    original_method_one_version: str
    current_method_one_version: str
    original_schema_version: int
    current_schema_version: int
    differences: tuple[dict[str, Any], ...]
    failure_code: str | None


@dataclass(frozen=True, slots=True)
class PricingExecutionReproductionDraft:
    """Values fully prepared before the repository inserts one immutable row."""

    reproduction_id: str
    execution_id: str
    outcome: PricingExecutionReproductionOutcome
    finalized_at: datetime
    correlation_id: str
    original_input_fingerprint: str | None
    reproduced_input_fingerprint: str | None
    original_result_fingerprint: str | None
    reproduced_result_fingerprint: str | None
    original_pricing_engine_version: str
    current_pricing_engine_version: str
    original_distribution_version: str
    current_distribution_version: str
    original_method_one_version: str
    current_method_one_version: str
    original_schema_version: int
    current_schema_version: int
    differences: tuple[dict[str, Any], ...]
    failure_code: str | None
