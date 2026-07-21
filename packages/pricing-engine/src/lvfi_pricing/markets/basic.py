"""Precificação pura de resultado, dupla chance e BTTS."""

from __future__ import annotations

import math

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy, stable_sum
from lvfi_pricing.distributions import (
    GoalDifferenceDistribution,
    ScoreProbabilityMatrix,
)
from lvfi_pricing.domain import Probability

from .contracts import (
    BttsSelection,
    DoubleChanceSelection,
    MarketCode,
    MarketPrices,
    PricedSelection,
    ThreeWaySelection,
)

_DEFAULT_POLICY = NumericPolicy()


def _error(code: ErrorCode, message: str, field: str | None = None) -> CalculationError:
    return CalculationError(code, message, field)


def _selection(
    selection: object,
    value: float,
    warnings: tuple[CalculationWarning, ...],
) -> PricedSelection | CalculationError:
    probability = Probability.create(value)
    if isinstance(probability, CalculationError):
        return probability
    return PricedSelection.create(selection, probability, warnings)


def _market(
    code: MarketCode,
    values: tuple[tuple[object, float], ...],
    total: float,
    residual: float,
    warnings: tuple[CalculationWarning, ...],
    policy: NumericPolicy,
) -> MarketPrices | CalculationError:
    if not math.isfinite(total) or not math.isfinite(residual):
        return _error(ErrorCode.INVALID_NUMBER, "market mass must be finite")
    selection_values = stable_sum([value for _, value in values])
    expected_total = total * (2.0 if code is MarketCode.DOUBLE_CHANCE else 1.0)
    if isinstance(selection_values, CalculationError) or not math.isclose(
        selection_values, expected_total, abs_tol=policy.probability_sum_tolerance
    ):
        return _error(
            ErrorCode.PROBABILITY_SUM_INVALID,
            "market selections do not preserve source mass",
        )
    selections: list[PricedSelection] = []
    for selection, value in values:
        priced = _selection(selection, value, ())
        if isinstance(priced, CalculationError):
            return priced
        selections.append(priced)
    return MarketPrices(code, tuple(selections), total, residual, warnings)


def price_three_way_result(
    distribution: GoalDifferenceDistribution, policy: NumericPolicy = _DEFAULT_POLICY
) -> MarketPrices | CalculationError:
    if not isinstance(distribution, GoalDifferenceDistribution) or not isinstance(
        policy, NumericPolicy
    ):
        return _error(
            ErrorCode.CONFIGURATION_ERROR,
            "invalid difference distribution or policy",
        )
    values = (
        (ThreeWaySelection.HOME, distribution.probability_home_positive_difference()),
        (ThreeWaySelection.DRAW, distribution.probability_zero_difference()),
        (ThreeWaySelection.AWAY, distribution.probability_home_negative_difference()),
    )
    return _market(
        MarketCode.THREE_WAY_RESULT,
        values,
        distribution.total_probability,
        distribution.residual_mass,
        distribution.warnings,
        policy,
    )


def price_double_chance(
    result: MarketPrices, policy: NumericPolicy = _DEFAULT_POLICY
) -> MarketPrices | CalculationError:
    if (
        not isinstance(result, MarketPrices)
        or result.market is not MarketCode.THREE_WAY_RESULT
    ):
        return _error(
            ErrorCode.INVALID_MARKET,
            "double chance requires a three-way result",
            "result",
        )
    if not isinstance(policy, NumericPolicy):
        return _error(
            ErrorCode.CONFIGURATION_ERROR, "policy must be a NumericPolicy", "policy"
        )
    home, draw, away = (selection.probability.value for selection in result.selections)
    values = (
        (DoubleChanceSelection.HOME_OR_DRAW, stable_sum([home, draw])),
        (DoubleChanceSelection.HOME_OR_AWAY, stable_sum([home, away])),
        (DoubleChanceSelection.DRAW_OR_AWAY, stable_sum([draw, away])),
    )
    typed_values: list[tuple[object, float]] = []
    for selection, value in values:
        if isinstance(value, CalculationError):
            return _error(
                ErrorCode.PROBABILITY_SUM_INVALID, "double chance sum is invalid"
            )
        typed_values.append((selection, value))
    return _market(
        MarketCode.DOUBLE_CHANCE,
        tuple(typed_values),
        result.total_probability,
        result.residual_mass,
        result.warnings,
        policy,
    )


def price_btts(
    matrix: ScoreProbabilityMatrix, policy: NumericPolicy = _DEFAULT_POLICY
) -> MarketPrices | CalculationError:
    if not isinstance(matrix, ScoreProbabilityMatrix) or not isinstance(
        policy, NumericPolicy
    ):
        return _error(ErrorCode.CONFIGURATION_ERROR, "invalid score matrix or policy")
    yes = stable_sum(
        [
            matrix.probabilities[home][away]
            for home in range(1, matrix.home_max_goals + 1)
            for away in range(1, matrix.away_max_goals + 1)
        ]
    )
    no = stable_sum(
        [
            matrix.probabilities[home][away]
            for home in range(matrix.home_max_goals + 1)
            for away in range(matrix.away_max_goals + 1)
            if home == 0 or away == 0
        ]
    )
    if isinstance(yes, CalculationError) or isinstance(no, CalculationError):
        return _error(ErrorCode.PROBABILITY_SUM_INVALID, "BTTS sum is invalid")
    return _market(
        MarketCode.BOTH_TEAMS_TO_SCORE,
        ((BttsSelection.YES, yes), (BttsSelection.NO, no)),
        matrix.total_probability,
        matrix.residual_mass,
        matrix.warnings,
        policy,
    )
