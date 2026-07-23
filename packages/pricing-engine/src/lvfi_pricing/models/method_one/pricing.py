"""Controlled, explicit composition of Method One rates with the Pricing Engine."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from lvfi_pricing.core import (
    CalculationError,
    CalculationWarning,
    ErrorCode,
    NumericPolicy,
)
from lvfi_pricing.domain import PoissonRate
from lvfi_pricing.engine import (
    PricingRequest,
    PricingResult,
    ThreeWayResultRequest,
    run_pricing_engine,
)
from lvfi_pricing.models.samples import MatchPeriodCode, SampleQuality, StatisticCode

from .contracts import (
    METHOD_ONE_MULTIPLIER_CATALOG_VERSION,
    METHOD_ONE_VERSION,
    MethodOneMultiplierResolution,
)
from .multipliers import (
    METHOD_ONE_MULTIPLIER_CATALOG,
    MethodOneAdjustedRateExplanation,
    MethodOneAdjustedRateResult,
)

_SAFE_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_ALLOWED_PERIODS = (MatchPeriodCode.FIRST_HALF, MatchPeriodCode.REGULATION_TIME)


def _error(code: ErrorCode, message: str, field: str) -> CalculationError:
    return CalculationError(code, message, field)


def _valid_rate(value: object, field: str) -> CalculationError | None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        return _error(ErrorCode.INVALID_NUMBER, "invalid adjusted rate", field)
    return None


def _valid_code(value: object) -> bool:
    return isinstance(value, str) and bool(_SAFE_CODE.fullmatch(value))


def _valid_resolutions(
    adjusted_rates: MethodOneAdjustedRateResult,
) -> CalculationError | None:
    expected = tuple(
        entry.key
        for entry in METHOD_ONE_MULTIPLIER_CATALOG.entries
        if entry.statistic is adjusted_rates.statistic
        and entry.period is adjusted_rates.period
    )
    resolutions = adjusted_rates.resolutions
    if (
        not isinstance(resolutions, tuple)
        or any(
            not isinstance(item, MethodOneMultiplierResolution) for item in resolutions
        )
        or tuple(item.key for item in resolutions) != expected
        or any(
            item.match_id != adjusted_rates.match_id
            or item.competition_id != adjusted_rates.competition_id
            or item.catalog_version != METHOD_ONE_MULTIPLIER_CATALOG_VERSION
            or item.resolution_schema_version != 1
            for item in resolutions
        )
    ):
        return _error(
            ErrorCode.INVALID_MULTIPLIER,
            "resolutions do not match adjusted-rate context",
            "resolutions",
        )
    return None


def _validate_adjusted_rates(
    adjusted_rates: object,
) -> MethodOneAdjustedRateResult | CalculationError:
    """Validate the complete T06 hand-off without recalculating either rate."""
    if not isinstance(adjusted_rates, MethodOneAdjustedRateResult):
        return _error(
            ErrorCode.INCONSISTENT_DATA,
            "invalid adjusted-rate result",
            "adjusted_rates",
        )
    if (
        adjusted_rates.method_version != METHOD_ONE_VERSION
        or adjusted_rates.adjusted_rate_schema_version != 1
        or adjusted_rates.deterministic is not True
    ):
        return _error(
            ErrorCode.SCHEMA_VERSION_UNSUPPORTED,
            "unsupported adjusted-rate result schema or version",
            "adjusted_rates",
        )
    if not _valid_code(adjusted_rates.match_id) or not _valid_code(
        adjusted_rates.competition_id
    ):
        return _error(ErrorCode.INCONSISTENT_DATA, "invalid match context", "context")
    if (
        adjusted_rates.statistic is not StatisticCode.GOALS
        or adjusted_rates.period not in _ALLOWED_PERIODS
    ):
        return _error(
            ErrorCode.MODEL_NOT_APPLICABLE,
            "statistic or period is not eligible for Poisson pricing",
            "adjusted_rates",
        )
    if not isinstance(adjusted_rates.quality, SampleQuality):
        return _error(ErrorCode.INCONSISTENT_DATA, "invalid quality", "quality")
    if not isinstance(adjusted_rates.warnings, tuple) or any(
        not isinstance(item, CalculationWarning) for item in adjusted_rates.warnings
    ):
        return _error(ErrorCode.INCONSISTENT_DATA, "invalid warnings", "warnings")
    if not isinstance(adjusted_rates.blockers, tuple) or any(
        not isinstance(item, CalculationError) for item in adjusted_rates.blockers
    ):
        return _error(ErrorCode.INCONSISTENT_DATA, "invalid blockers", "blockers")
    for value, field in (
        (adjusted_rates.home_adjusted_rate, "home_adjusted_rate"),
        (adjusted_rates.away_adjusted_rate, "away_adjusted_rate"),
    ):
        if error := _valid_rate(value, field):
            return error
    explanation = adjusted_rates.explanation
    if (
        not isinstance(explanation, MethodOneAdjustedRateExplanation)
        or explanation.explanation_schema_version != 1
        or explanation.catalog_version != METHOD_ONE_MULTIPLIER_CATALOG_VERSION
        or explanation.deterministic is not True
        or explanation.home_adjusted_rate != adjusted_rates.home_adjusted_rate
        or explanation.away_adjusted_rate != adjusted_rates.away_adjusted_rate
        or explanation.resolutions != adjusted_rates.resolutions
        or explanation.quality != adjusted_rates.quality
        or explanation.warnings != adjusted_rates.warnings
        or explanation.blockers != adjusted_rates.blockers
    ):
        return _error(
            ErrorCode.INCONSISTENT_DATA,
            "adjusted-rate explanation is incoherent",
            "explanation",
        )
    if error := _valid_resolutions(adjusted_rates):
        return error

    if (
        adjusted_rates.quality.calculation_allowed is not True
        or adjusted_rates.blockers
        or adjusted_rates.quality.errors
    ):
        return _error(
            ErrorCode.MODEL_NOT_APPLICABLE,
            "adjusted-rate result is blocked",
            "adjusted_rates",
        )
    return adjusted_rates


@dataclass(frozen=True, slots=True)
class MethodOnePricingExplanation:
    """Immutable audit trail for the explicit Method One engine invocation."""

    home_adjusted_rate: float
    away_adjusted_rate: float
    home_poisson_rate: PoissonRate
    away_poisson_rate: PoissonRate
    pricing_request: PricingRequest
    pricing_engine_version: str
    quality: SampleQuality
    warnings: tuple[CalculationWarning, ...]
    blockers: tuple[CalculationError, ...]
    catalog_version: str = METHOD_ONE_MULTIPLIER_CATALOG_VERSION
    integration_schema_version: int = 1
    engine_called: bool = True
    deterministic: bool = True


@dataclass(frozen=True, slots=True)
class MethodOnePricingResult:
    """Typed envelope retaining both the T06 output and the engine output."""

    match_id: str
    competition_id: str
    statistic: StatisticCode
    period: MatchPeriodCode
    adjusted_rates: MethodOneAdjustedRateResult
    home_poisson_rate: PoissonRate
    away_poisson_rate: PoissonRate
    pricing_request: PricingRequest
    pricing_result: PricingResult
    quality: SampleQuality
    warnings: tuple[CalculationWarning, ...]
    blockers: tuple[CalculationError, ...]
    explanation: MethodOnePricingExplanation
    method_version: str = METHOD_ONE_VERSION
    pricing_engine_version: str = "1.0.0"
    integration_schema_version: int = 1
    deterministic: bool = True


def build_method_one_pricing_request(
    adjusted_rates: MethodOneAdjustedRateResult,
) -> PricingRequest | CalculationError:
    """Build the deterministic, minimal public engine request for eligible rates."""
    valid = _validate_adjusted_rates(adjusted_rates)
    if isinstance(valid, CalculationError):
        return valid
    home_rate = PoissonRate.create(
        0.0 if valid.home_adjusted_rate == 0 else valid.home_adjusted_rate
    )
    if isinstance(home_rate, CalculationError):
        return home_rate
    away_rate = PoissonRate.create(
        0.0 if valid.away_adjusted_rate == 0 else valid.away_adjusted_rate
    )
    if isinstance(away_rate, CalculationError):
        return away_rate
    return PricingRequest.create(
        home_rate,
        away_rate,
        (ThreeWayResultRequest(),),
        NumericPolicy(),
    )


def price_method_one(
    adjusted_rates: MethodOneAdjustedRateResult,
) -> MethodOnePricingResult | CalculationError:
    """Explicitly invoke the public Pricing Engine and retain its unmodified result."""
    request = build_method_one_pricing_request(adjusted_rates)
    if isinstance(request, CalculationError):
        return request
    pricing_result = run_pricing_engine(request)
    if isinstance(pricing_result, CalculationError):
        return pricing_result
    valid = _validate_adjusted_rates(adjusted_rates)
    if isinstance(valid, CalculationError):
        return valid
    explanation = MethodOnePricingExplanation(
        valid.home_adjusted_rate,
        valid.away_adjusted_rate,
        request.home_rate,
        request.away_rate,
        request,
        pricing_result.metadata.package_version,
        valid.quality,
        valid.warnings,
        valid.blockers,
    )
    return MethodOnePricingResult(
        valid.match_id,
        valid.competition_id,
        valid.statistic,
        valid.period,
        valid,
        request.home_rate,
        request.away_rate,
        request,
        pricing_result,
        valid.quality,
        valid.warnings,
        valid.blockers,
        explanation,
        pricing_engine_version=pricing_result.metadata.package_version,
    )
