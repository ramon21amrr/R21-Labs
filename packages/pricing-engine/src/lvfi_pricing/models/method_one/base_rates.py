"""Pure, auditable base-rate combination for Method One."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from lvfi_pricing.core import (
    CalculationError,
    CalculationWarning,
    ErrorCode,
    stable_sum,
)
from lvfi_pricing.core.numeric import NumericPolicy, is_close, validate_finite
from lvfi_pricing.models.samples import (
    MatchPeriodCode,
    SampleQuality,
    SampleQualityLevel,
    StatisticCode,
)
from lvfi_pricing.models.samples.contracts import COMMON_CONTRACT_VERSION

from .averages import MethodOneContextualAverages
from .contracts import (
    METHOD_ONE_VERSION,
    ContextualAverage,
    ContextualAverageEvidence,
    MethodOneConfiguration,
    MethodOneRecencyConfiguration,
    MethodOneSeriesRole,
    MethodOneWeightConfiguration,
    RecencyPolicyCode,
)

_ROLES = tuple(MethodOneSeriesRole)
_QUALITY_RANK = {
    SampleQualityLevel.EMPTY: 0,
    SampleQualityLevel.INSUFFICIENT: 1,
    SampleQualityLevel.PARTIAL: 2,
    SampleQualityLevel.ADEQUATE: 3,
}


def _error(code: ErrorCode, message: str, field: str) -> CalculationError:
    return CalculationError(code, message, field)


def _non_negative(value: object, field: str) -> CalculationError | None:
    if (error := validate_finite(value, field=field)) is not None:
        return error
    if cast(int | float, value) < 0:
        return _error(ErrorCode.INVALID_NUMBER, "value must be non-negative", field)
    return None


@dataclass(frozen=True, slots=True)
class MethodOneWeightedComponent:
    """One visible term of a participant's weighted base-rate formula."""

    average: ContextualAverage
    weight: float
    value: float


@dataclass(frozen=True, slots=True)
class MethodOneParticipantBaseRateExplanation:
    """The two weighted inputs and their stable sum for one participant."""

    participant_id: str
    own_production: MethodOneWeightedComponent
    opponent_concession: MethodOneWeightedComponent
    base_rate: float


@dataclass(frozen=True, slots=True)
class MethodOneBaseRateExplanation:
    """Audit record for the two Method One base-rate formulas."""

    home: MethodOneParticipantBaseRateExplanation
    away: MethodOneParticipantBaseRateExplanation
    averages: tuple[ContextualAverage, ...]
    qualities: tuple[SampleQuality, ...]
    consolidated_quality: SampleQuality
    warnings: tuple[CalculationWarning, ...]
    recency_policy: RecencyPolicyCode
    formula_version: str = METHOD_ONE_VERSION
    explanation_schema_version: int = 1
    deterministic: bool = True


@dataclass(frozen=True, slots=True)
class MethodOneBaseRateResult:
    """Immutable result of combining the four canonical contextual averages."""

    home_base_rate: float
    away_base_rate: float
    statistic: StatisticCode
    period: MatchPeriodCode
    home_team_id: str
    away_team_id: str
    match_id: str
    competition_id: str
    home_weights: MethodOneWeightConfiguration
    away_weights: MethodOneWeightConfiguration
    contextual_averages: MethodOneContextualAverages
    quality: SampleQuality
    warnings: tuple[CalculationWarning, ...]
    explanation: MethodOneBaseRateExplanation
    method_version: str = METHOD_ONE_VERSION
    result_schema_version: int = 2
    deterministic: bool = True


def _validate_weights(
    value: object, policy: NumericPolicy, field: str
) -> CalculationError | None:
    if not isinstance(value, MethodOneWeightConfiguration):
        return _error(ErrorCode.INVALID_WEIGHT, "invalid weight configuration", field)
    if (
        value.configuration_version != METHOD_ONE_VERSION
        or value.configuration_schema_version != 1
    ):
        return _error(
            ErrorCode.SCHEMA_VERSION_UNSUPPORTED, "unsupported weights", field
        )
    for weight in (value.weight_own, value.weight_opponent):
        if _non_negative(weight, field) is not None or weight > 1:
            return _error(ErrorCode.INVALID_WEIGHT, "weight is outside [0, 1]", field)
    total_is_one = is_close(value.weight_own + value.weight_opponent, 1.0, policy)
    if isinstance(total_is_one, CalculationError) or total_is_one is not True:
        return _error(ErrorCode.WEIGHTS_SUM_INVALID, "weights must sum to one", field)
    return None


def _validate_configuration(
    configuration: object,
) -> tuple[MethodOneConfiguration | None, CalculationError | None]:
    if not isinstance(configuration, MethodOneConfiguration):
        return None, _error(
            ErrorCode.CONFIGURATION_ERROR, "invalid configuration", "configuration"
        )
    if (
        configuration.formula_version != METHOD_ONE_VERSION
        or configuration.configuration_version != METHOD_ONE_VERSION
        or configuration.configuration_schema_version != 1
    ):
        return None, _error(
            ErrorCode.SCHEMA_VERSION_UNSUPPORTED,
            "unsupported configuration schema",
            "configuration",
        )
    if (
        not isinstance(configuration.numeric_policy, NumericPolicy)
        or not isinstance(configuration.recency, MethodOneRecencyConfiguration)
        or configuration.recency.code is not RecencyPolicyCode.UNIFORM_V1
        or configuration.recency.recency_schema_version != 1
    ):
        return None, _error(
            ErrorCode.CONFIGURATION_ERROR,
            "invalid base-rate configuration",
            "configuration",
        )
    if configuration.multiplier_resolutions:
        return None, _error(
            ErrorCode.INVALID_MULTIPLIER,
            "multipliers are outside this stage",
            "multiplier_resolutions",
        )
    for field, weights in (
        ("home_weights", configuration.home_weights),
        ("away_weights", configuration.away_weights),
    ):
        if error := _validate_weights(weights, configuration.numeric_policy, field):
            return None, error
    return configuration, None


def _validate_averages(
    contextual_averages: object,
) -> tuple[
    tuple[ContextualAverage, ContextualAverage, ContextualAverage, ContextualAverage]
    | None,
    tuple[
        ContextualAverageEvidence,
        ContextualAverageEvidence,
        ContextualAverageEvidence,
        ContextualAverageEvidence,
    ]
    | None,
    CalculationError | None,
]:
    if not isinstance(contextual_averages, MethodOneContextualAverages):
        return (
            None,
            None,
            _error(
                ErrorCode.INCONSISTENT_DATA,
                "averages must be a MethodOneContextualAverages contract",
                "contextual_averages",
            ),
        )
    values = contextual_averages.values
    for average, role in zip(values, _ROLES, strict=True):
        if not isinstance(average, ContextualAverage) or average.role is not role:
            return (
                None,
                None,
                _error(
                    ErrorCode.INCONSISTENT_DATA,
                    "averages are not in canonical role order",
                    "averages",
                ),
            )
        if average.average_schema_version != 1 or not isinstance(
            average.evidence, ContextualAverageEvidence
        ):
            return (
                None,
                None,
                _error(
                    ErrorCode.SCHEMA_VERSION_UNSUPPORTED,
                    "unsupported average schema",
                    "averages",
                ),
            )
        if (error := _non_negative(average.value, "average.value")) is not None:
            return None, None, error
    audit = cast(
        tuple[
            ContextualAverageEvidence,
            ContextualAverageEvidence,
            ContextualAverageEvidence,
            ContextualAverageEvidence,
        ],
        tuple(average.evidence for average in values),
    )
    if any(
        evidence.common_contract_version != COMMON_CONTRACT_VERSION
        or evidence.recency_policy is not RecencyPolicyCode.UNIFORM_V1
        or evidence.deterministic is not True
        or not isinstance(evidence.quality, SampleQuality)
        for evidence in audit
    ):
        return (
            None,
            None,
            _error(
                ErrorCode.SCHEMA_VERSION_UNSUPPORTED,
                "unsupported average evidence",
                "averages",
            ),
        )
    if any(not evidence.quality.calculation_allowed for evidence in audit):
        return (
            None,
            None,
            _error(
                ErrorCode.MODEL_NOT_APPLICABLE,
                "a contextual average is blocked",
                "averages",
            ),
        )
    home_ids = {audit[0].subject_id, audit[1].subject_id}
    away_ids = {audit[2].subject_id, audit[3].subject_id}
    if (
        len({evidence.statistic for evidence in audit}) != 1
        or len({evidence.period for evidence in audit}) != 1
        or contextual_averages.statistic is not audit[0].statistic
        or contextual_averages.period is not audit[0].period
        or contextual_averages.home_team_id not in home_ids
        or contextual_averages.away_team_id not in away_ids
        or not isinstance(contextual_averages.match_id, str)
        or not contextual_averages.match_id
        or not isinstance(contextual_averages.competition_id, str)
        or not contextual_averages.competition_id
        or len(home_ids) != 1
        or len(away_ids) != 1
        or home_ids == away_ids
    ):
        return (
            None,
            None,
            _error(
                ErrorCode.INCONSISTENT_DATA,
                "incoherent contextual averages",
                "averages",
            ),
        )
    return (
        cast(
            tuple[
                ContextualAverage,
                ContextualAverage,
                ContextualAverage,
                ContextualAverage,
            ],
            values,
        ),
        audit,
        None,
    )


def _participant(
    participant_id: str,
    production: ContextualAverage,
    own_weight: float,
    concession: ContextualAverage,
    opponent_weight: float,
) -> MethodOneParticipantBaseRateExplanation | CalculationError:
    own_value = production.value * own_weight
    opponent_value = concession.value * opponent_weight
    if (error := _non_negative(own_value, "own_component")) is not None:
        return error
    if (error := _non_negative(opponent_value, "opponent_component")) is not None:
        return error
    total = stable_sum((own_value, opponent_value))
    if isinstance(total, CalculationError):
        return total
    if (error := _non_negative(total, "base_rate")) is not None:
        return error
    normalized_total = 0.0 if total == 0 else total
    return MethodOneParticipantBaseRateExplanation(
        participant_id,
        MethodOneWeightedComponent(production, own_weight, own_value),
        MethodOneWeightedComponent(concession, opponent_weight, opponent_value),
        normalized_total,
    )


def calculate_method_one_base_rates(
    contextual_averages: MethodOneContextualAverages,
    configuration: MethodOneConfiguration,
) -> MethodOneBaseRateResult | CalculationError:
    """Combine four canonical averages; never apply multipliers or call the engine."""
    values, audit, average_error = _validate_averages(contextual_averages)
    if average_error is not None:
        return average_error
    config, configuration_error = _validate_configuration(configuration)
    if configuration_error is not None:
        return configuration_error
    assert values is not None and audit is not None and config is not None
    home = _participant(
        audit[0].subject_id,
        values[0],
        config.home_weights.weight_own,
        values[3],
        config.home_weights.weight_opponent,
    )
    away = _participant(
        audit[2].subject_id,
        values[2],
        config.away_weights.weight_own,
        values[1],
        config.away_weights.weight_opponent,
    )
    if isinstance(home, CalculationError):
        return home
    if isinstance(away, CalculationError):
        return away
    qualities = tuple(evidence.quality for evidence in audit)
    quality = min(qualities, key=lambda item: _QUALITY_RANK[item.level])
    warnings = tuple(warning for item in qualities for warning in item.warnings)
    explanation = MethodOneBaseRateExplanation(
        home,
        away,
        values,
        qualities,
        quality,
        warnings,
        config.recency.code,
    )
    return MethodOneBaseRateResult(
        home.base_rate,
        away.base_rate,
        audit[0].statistic,
        audit[0].period,
        home.participant_id,
        away.participant_id,
        contextual_averages.match_id,
        contextual_averages.competition_id,
        config.home_weights,
        config.away_weights,
        contextual_averages,
        quality,
        warnings,
        explanation,
    )
