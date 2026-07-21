"""Distribuição auditável da diferença de gols derivada de uma matriz."""

from __future__ import annotations

import math
from dataclasses import dataclass

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy, stable_sum

from .score_matrix import ScoreProbabilityMatrix

_DEFAULT_POLICY = NumericPolicy()


def _error(code: ErrorCode, message: str, field: str | None = None) -> CalculationError:
    return CalculationError(code, message, field)


@dataclass(frozen=True, slots=True)
class GoalDifferenceDistribution:
    """Massa da matriz agrupada pelo valor inteiro ``home_goals - away_goals``."""

    min_difference: int
    max_difference: int
    probabilities: tuple[float, ...]
    total_probability: float
    residual_mass: float
    warnings: tuple[CalculationWarning, ...] = ()

    def __post_init__(self) -> None:
        if (
            isinstance(self.min_difference, bool)
            or isinstance(self.max_difference, bool)
            or not isinstance(self.min_difference, int)
            or not isinstance(self.max_difference, int)
            or self.min_difference > self.max_difference
            or len(self.probabilities) != self.max_difference - self.min_difference + 1
        ):
            raise _error(
                ErrorCode.PROBABILITY_SUM_INVALID, "difference support is inconsistent"
            )
        total = stable_sum(self.probabilities)
        if (
            isinstance(total, CalculationError)
            or not math.isfinite(self.total_probability)
            or not math.isfinite(self.residual_mass)
            or self.total_probability > 1.0 + _DEFAULT_POLICY.probability_sum_tolerance
            or self.residual_mass < -_DEFAULT_POLICY.probability_sum_tolerance
            or not math.isclose(
                total,
                self.total_probability,
                abs_tol=_DEFAULT_POLICY.probability_sum_tolerance,
            )
        ):
            raise _error(
                ErrorCode.PROBABILITY_SUM_INVALID, "difference mass is inconsistent"
            )
        if any(not math.isfinite(value) or value < 0.0 for value in self.probabilities):
            raise _error(
                ErrorCode.INVALID_PROBABILITY,
                "difference probabilities must be finite and non-negative",
            )
        if not isinstance(self.warnings, tuple) or any(
            not isinstance(warning, CalculationWarning) for warning in self.warnings
        ):
            raise _error(
                ErrorCode.CONFIGURATION_ERROR, "warnings must be typed and immutable"
            )

    def probability_for_difference(
        self, difference: object
    ) -> float | CalculationError:
        """Retorna a probabilidade para a diferença materializada."""
        if isinstance(difference, bool) or not isinstance(difference, int):
            return _error(
                ErrorCode.INVALID_NUMBER, "difference must be an integer", "difference"
            )
        if difference < self.min_difference or difference > self.max_difference:
            return _error(
                ErrorCode.INVALID_NUMBER,
                "difference is outside the materialized support",
            )
        return self.probabilities[difference - self.min_difference]

    def probability_home_positive_difference(self) -> float:
        return stable_sum(self.probabilities[max(0, 1 - self.min_difference) :])  # type: ignore[return-value]

    def probability_zero_difference(self) -> float:
        return self.probabilities[-self.min_difference]

    def probability_home_negative_difference(self) -> float:
        return stable_sum(self.probabilities[: -self.min_difference])  # type: ignore[return-value]


def build_goal_difference_distribution(
    matrix: ScoreProbabilityMatrix, policy: NumericPolicy = _DEFAULT_POLICY
) -> GoalDifferenceDistribution | CalculationError:
    """Agrupa cada célula da matriz exatamente uma vez, sem recalcular Poisson."""
    if not isinstance(policy, NumericPolicy):
        return _error(
            ErrorCode.CONFIGURATION_ERROR, "policy must be a NumericPolicy", "policy"
        )
    if not isinstance(matrix, ScoreProbabilityMatrix):
        return _error(
            ErrorCode.CONFIGURATION_ERROR,
            "matrix must be a ScoreProbabilityMatrix",
            "matrix",
        )
    minimum = -matrix.away_max_goals
    maximum = matrix.home_max_goals
    buckets: list[list[float]] = [[] for _ in range(maximum - minimum + 1)]
    for home, row in enumerate(matrix.probabilities):
        for away, probability in enumerate(row):
            buckets[home - away - minimum].append(probability)
    probabilities: list[float] = []
    for bucket in buckets:
        total = stable_sum(bucket)
        if isinstance(total, CalculationError):
            return _error(
                ErrorCode.PROBABILITY_SUM_INVALID,
                "difference probability sum is invalid",
            )
        probabilities.append(total)
    total = stable_sum(probabilities)
    if isinstance(total, CalculationError) or not math.isclose(
        total, matrix.total_probability, abs_tol=policy.probability_sum_tolerance
    ):
        return _error(
            ErrorCode.PROBABILITY_SUM_INVALID, "difference total is inconsistent"
        )
    return GoalDifferenceDistribution(
        minimum,
        maximum,
        tuple(probabilities),
        total,
        matrix.residual_mass,
    )
