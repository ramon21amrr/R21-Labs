"""Versioned contracts for LVFI Method Two adjusted Poisson."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from lvfi_api.domain.statistics import (
    CompetitionReference,
    MethodTwoMetric,
    SeasonScope,
    StatisticsSample,
    StatisticsTarget,
)

METHOD_TWO_NAME: Literal["method_two_adjusted_poisson"] = "method_two_adjusted_poisson"
METHOD_TWO_VERSION: Literal["1.0.0"] = "1.0.0"
METHOD_TWO_CONFIGURATION_SCHEMA_VERSION = 1
METHOD_TWO_EVIDENCE_SCHEMA_VERSION = 1
METHOD_TWO_RESULT_SCHEMA_VERSION = 1
METHOD_TWO_HASH_ALGORITHM: Literal["sha256"] = "sha256"
MethodTwoContext = Literal["venue", "overall"]


@dataclass(frozen=True, slots=True)
class MethodTwoConfiguration:
    """Resolved selectors.  There are intentionally no weights or multipliers."""

    sample_size: Literal[5, 10, 15, 20]
    context: MethodTwoContext
    season_scope: SeasonScope
    previous_season_id: int | None
    metric: MethodTwoMetric


@dataclass(frozen=True, slots=True)
class MethodTwoSeries:
    """One real-observation series and its semantic projection."""

    name: str
    semantic: str
    source_field_projection: str
    sample: StatisticsSample | CompetitionReference


@dataclass(frozen=True, slots=True)
class MethodTwoEvidence:
    """Complete, immutable evidence for calculation or an explicit block."""

    evidence_schema_version: Literal[1]
    target: StatisticsTarget
    configuration: MethodTwoConfiguration
    completed_predicate: Literal["match_statistics.match_id_is_not_null"]
    home_production: MethodTwoSeries
    away_complement: MethodTwoSeries
    away_production: MethodTwoSeries
    home_complement: MethodTwoSeries
    home_production_reference: MethodTwoSeries
    away_complement_reference: MethodTwoSeries
    away_production_reference: MethodTwoSeries
    home_complement_reference: MethodTwoSeries


@dataclass(frozen=True, slots=True)
class MethodTwoResult:
    """No rounding is performed here; display code owns presentation rounding."""

    method: Literal["method_two_adjusted_poisson"]
    method_version: Literal["1.0.0"]
    configuration_schema_version: Literal[1]
    result_schema_version: Literal[1]
    status: Literal["completed", "blocked"]
    evidence: MethodTwoEvidence
    configuration_fingerprint: str
    evidence_fingerprint: str
    result_fingerprint: str
    home_lambda: float | None
    away_lambda: float | None
    total_lambda: float | None
    blocking_reasons: tuple[str, ...]
