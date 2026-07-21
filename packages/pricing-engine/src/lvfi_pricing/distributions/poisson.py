"""Distribuição Poisson adaptativa, sem I/O ou normalização implícita."""

from __future__ import annotations

import math
from dataclasses import dataclass

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy, stable_sum
from lvfi_pricing.domain import PoissonRate

_DEFAULT_POLICY = NumericPolicy()
_INITIAL_MAX_COUNT = 10
_MAX_COUNT = 1_000


def _invalid_rate(value: object) -> CalculationError:
    return CalculationError(
        ErrorCode.INVALID_LAMBDA,
        "rate must be a PoissonRate",
        "rate",
        {"value_type": type(value).__name__},
    )


def _invalid_count(value: object) -> CalculationError:
    return CalculationError(
        ErrorCode.INVALID_NUMBER,
        "count must be a non-negative integer",
        "count",
        {"value_type": type(value).__name__},
    )


def poisson_pmf(rate: PoissonRate, count: object) -> float | CalculationError:
    """Calcula P(X=count) usando a recorrência Poisson a partir de zero."""
    if not isinstance(rate, PoissonRate):
        return _invalid_rate(rate)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return _invalid_count(count)
    if rate.value == 0.0:
        return 1.0 if count == 0 else 0.0

    probability = math.exp(-rate.value)
    for index in range(count):
        probability *= rate.value / (index + 1)
    return probability


@dataclass(frozen=True, slots=True)
class PoissonDistribution:
    """Suporte Poisson consecutivo com cauda explícita e imutável."""

    rate: PoissonRate
    probabilities: tuple[float, ...]
    max_count: int
    cumulative_probability: float
    residual_mass: float
    converged: bool
    warnings: tuple[CalculationWarning, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.rate, PoissonRate):
            raise _invalid_rate(self.rate)
        if (
            isinstance(self.max_count, bool)
            or not isinstance(self.max_count, int)
            or self.max_count != len(self.probabilities) - 1
        ):
            raise CalculationError(
                ErrorCode.PROBABILITY_SUM_INVALID,
                "max_count must match the final probability index",
                "max_count",
            )
        if not isinstance(self.warnings, tuple) or any(
            not isinstance(warning, CalculationWarning) for warning in self.warnings
        ):
            raise CalculationError(
                ErrorCode.CONFIGURATION_ERROR,
                "warnings must be a tuple of CalculationWarning values",
                "warnings",
            )
        if any(
            not isinstance(probability, float)
            or not math.isfinite(probability)
            or probability < 0.0
            for probability in self.probabilities
        ):
            raise CalculationError(
                ErrorCode.INVALID_PROBABILITY,
                "probabilities must be finite non-negative floats",
                "probabilities",
            )
        if not math.isfinite(self.cumulative_probability) or not math.isfinite(
            self.residual_mass
        ):
            raise CalculationError(
                ErrorCode.PROBABILITY_SUM_INVALID,
                "cumulative probability and residual mass must be finite",
            )


def _validated_total(
    probabilities: tuple[float, ...], policy: NumericPolicy
) -> float | CalculationError:
    total = stable_sum(probabilities)
    if isinstance(total, CalculationError):
        return CalculationError(
            ErrorCode.PROBABILITY_SUM_INVALID,
            "probability sum is invalid",
            context={"max_count": len(probabilities) - 1},
        )
    if total > 1.0 + policy.probability_sum_tolerance:
        return CalculationError(
            ErrorCode.PROBABILITY_SUM_INVALID,
            "probability sum exceeds one beyond tolerance",
            context={"max_count": len(probabilities) - 1, "sum": total},
        )
    return total


def build_poisson_distribution(
    rate: PoissonRate, policy: NumericPolicy = _DEFAULT_POLICY
) -> PoissonDistribution | CalculationError:
    """Materializa de 0 a 10 e expande até a cauda cumprir a política."""
    if not isinstance(rate, PoissonRate):
        return _invalid_rate(rate)
    if not isinstance(policy, NumericPolicy):
        return CalculationError(
            ErrorCode.CONFIGURATION_ERROR,
            "policy must be a NumericPolicy",
            "policy",
            {"value_type": type(policy).__name__},
        )

    first = poisson_pmf(rate, 0)
    if isinstance(first, CalculationError):
        return first
    probabilities = [first]
    for count in range(1, _INITIAL_MAX_COUNT + 1):
        probabilities.append(probabilities[-1] * rate.value / count)

    while True:
        frozen_probabilities = tuple(probabilities)
        total = _validated_total(frozen_probabilities, policy)
        if isinstance(total, CalculationError):
            return total
        residual = 1.0 - total
        if residual < -policy.probability_sum_tolerance:
            return CalculationError(
                ErrorCode.PROBABILITY_SUM_INVALID,
                "residual mass is negative beyond tolerance",
                context={
                    "max_count": len(probabilities) - 1,
                    "residual_mass": residual,
                },
            )
        converged = residual <= policy.poisson_residual_tolerance
        if converged:
            return PoissonDistribution(
                rate,
                frozen_probabilities,
                len(probabilities) - 1,
                total,
                residual,
                True,
            )
        if len(probabilities) - 1 >= _MAX_COUNT:
            return CalculationError(
                ErrorCode.NUMERIC_CONVERGENCE_FAILED,
                "Poisson distribution did not converge within the safety limit",
                context={
                    "rate": rate.value,
                    "max_count": _MAX_COUNT,
                    "residual_mass": residual,
                    "tolerance": policy.poisson_residual_tolerance,
                },
            )
        next_count = len(probabilities)
        probabilities.append(probabilities[-1] * rate.value / next_count)
