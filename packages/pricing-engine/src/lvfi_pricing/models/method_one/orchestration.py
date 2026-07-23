"""Final deterministic orchestration for the complete Method One flow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from lvfi_pricing.core import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.models.samples import (
    MatchPeriodCode,
    SampleQuality,
    SampleQualityLevel,
    StatisticCode,
)

from .averages import (
    MethodOneContextualAverages,
    calculate_method_one_contextual_averages,
)
from .base_rates import MethodOneBaseRateResult, calculate_method_one_base_rates
from .contracts import (
    METHOD_ONE_MULTIPLIER_CATALOG_VERSION,
    METHOD_ONE_VERSION,
    MethodOneMultiplierCandidate,
    MethodOneMultiplierResolution,
    MethodOneRequest,
)
from .multipliers import (
    MethodOneAdjustedRateResult,
    apply_method_one_multipliers,
    resolve_method_one_multipliers,
)
from .pricing import MethodOnePricingResult, price_method_one


class MethodOnePublicationState(StrEnum):
    """The approved publication disposition for the consolidated quality."""

    BLOCKED = "blocked"
    AUDIT_ONLY = "audit_only"
    CONDITIONAL = "conditional"
    PUBLISHABLE = "publishable"


_PUBLICATION_STATE = {
    SampleQualityLevel.EMPTY: MethodOnePublicationState.BLOCKED,
    SampleQualityLevel.INSUFFICIENT: MethodOnePublicationState.AUDIT_ONLY,
    SampleQualityLevel.PARTIAL: MethodOnePublicationState.CONDITIONAL,
    SampleQualityLevel.ADEQUATE: MethodOnePublicationState.PUBLISHABLE,
}
_SCOPE_ORDER = {"MATCH": 0, "COMPETITION": 1, "GLOBAL": 2}


def _error(message: str, field: str) -> CalculationError:
    return CalculationError(ErrorCode.INCONSISTENT_DATA, message, field)


def _canonical_candidates(
    candidates: tuple[MethodOneMultiplierCandidate, ...],
) -> tuple[MethodOneMultiplierCandidate, ...]:
    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                item.catalog_order,
                item.applies_to.value,
                _SCOPE_ORDER[item.scope.value],
                item.source,
                item.value,
                item.target_match_id or "",
                item.competition_id or "",
            ),
        )
    )


@dataclass(frozen=True, slots=True)
class MethodOneFinalExplanation:
    """Structured, complete audit evidence assembled from each public stage."""

    request: MethodOneRequest
    series_references: tuple[object, ...]
    snapshots: tuple[object, ...]
    contextual_averages: MethodOneContextualAverages
    base_rates: MethodOneBaseRateResult
    multiplier_catalog_version: str
    multiplier_candidates: tuple[MethodOneMultiplierCandidate, ...]
    resolutions: tuple[MethodOneMultiplierResolution, ...]
    adjusted_rates: MethodOneAdjustedRateResult
    pricing: MethodOnePricingResult
    quality: SampleQuality
    publication_state: MethodOnePublicationState
    warnings: tuple[CalculationWarning, ...]
    blockers: tuple[CalculationError, ...]
    method_version: str = METHOD_ONE_VERSION
    explanation_schema_version: int = 1
    orchestration_schema_version: int = 1
    deterministic: bool = True


@dataclass(frozen=True, slots=True)
class MethodOneFinalResult:
    """One immutable, auditable result spanning Method One and Pricing Engine."""

    match_id: str
    competition_id: str
    home_team_id: str
    away_team_id: str
    statistic: StatisticCode
    period: MatchPeriodCode
    request: MethodOneRequest
    multiplier_candidates: tuple[MethodOneMultiplierCandidate, ...]
    contextual_averages: MethodOneContextualAverages
    base_rates: MethodOneBaseRateResult
    resolutions: tuple[MethodOneMultiplierResolution, ...]
    adjusted_rates: MethodOneAdjustedRateResult
    pricing: MethodOnePricingResult
    quality: SampleQuality
    publication_state: MethodOnePublicationState
    warnings: tuple[CalculationWarning, ...]
    blockers: tuple[CalculationError, ...]
    explanation: MethodOneFinalExplanation
    method_version: str = METHOD_ONE_VERSION
    final_result_schema_version: int = 1
    orchestration_schema_version: int = 1
    deterministic: bool = True


def _in_context(
    request: MethodOneRequest,
    averages: MethodOneContextualAverages,
    base_rates: MethodOneBaseRateResult,
    adjusted_rates: MethodOneAdjustedRateResult,
    pricing: MethodOnePricingResult,
) -> bool:
    return not any(
        (
            value.match_id != request.match_id
            or value.competition_id != request.competition_id
            or value.statistic is not request.statistic
            or value.period is not request.period
        )
        for value in (averages, base_rates, adjusted_rates, pricing)
    ) and (
        base_rates.home_team_id == request.home_team_id
        and base_rates.away_team_id == request.away_team_id
        and adjusted_rates.home_team_id == request.home_team_id
        and adjusted_rates.away_team_id == request.away_team_id
        and pricing.adjusted_rates is adjusted_rates
    )


def run_method_one(
    request: MethodOneRequest,
    multiplier_candidates: tuple[MethodOneMultiplierCandidate, ...] = (),
) -> MethodOneFinalResult | CalculationError:
    """Run the approved Method One sequence using only its public stage APIs."""
    if not isinstance(multiplier_candidates, tuple):
        return CalculationError(
            ErrorCode.INVALID_MULTIPLIER,
            "candidates must be an immutable tuple",
            "multiplier_candidates",
        )
    averages = calculate_method_one_contextual_averages(request)
    if isinstance(averages, CalculationError):
        return averages
    base_rates = calculate_method_one_base_rates(averages, request.configuration)
    if isinstance(base_rates, CalculationError):
        return base_rates
    candidates = _canonical_candidates(multiplier_candidates)
    resolutions = resolve_method_one_multipliers(
        candidates,
        match_id=request.match_id,
        competition_id=request.competition_id,
        statistic=request.statistic,
        period=request.period,
    )
    if isinstance(resolutions, CalculationError):
        return resolutions
    adjusted_rates = apply_method_one_multipliers(base_rates, resolutions)
    if isinstance(adjusted_rates, CalculationError):
        return adjusted_rates
    pricing = price_method_one(adjusted_rates)
    if isinstance(pricing, CalculationError):
        return pricing
    if not _in_context(request, averages, base_rates, adjusted_rates, pricing):
        return _error("orchestration hand-off is incoherent", "orchestration")
    state = _PUBLICATION_STATE[adjusted_rates.quality.level]
    explanation = MethodOneFinalExplanation(
        request,
        request.series_references,
        tuple(item.snapshot for item in request.series_references),
        averages,
        base_rates,
        METHOD_ONE_MULTIPLIER_CATALOG_VERSION,
        candidates,
        resolutions,
        adjusted_rates,
        pricing,
        adjusted_rates.quality,
        state,
        adjusted_rates.warnings,
        adjusted_rates.blockers,
    )
    return MethodOneFinalResult(
        request.match_id,
        request.competition_id,
        request.home_team_id,
        request.away_team_id,
        request.statistic,
        request.period,
        request,
        candidates,
        averages,
        base_rates,
        resolutions,
        adjusted_rates,
        pricing,
        adjusted_rates.quality,
        state,
        adjusted_rates.warnings,
        adjusted_rates.blockers,
        explanation,
    )
