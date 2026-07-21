"""Matriz auditável de placares de duas distribuições Poisson independentes."""

from __future__ import annotations

import math
from dataclasses import dataclass

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy, stable_sum

from .poisson import PoissonDistribution

_DEFAULT_POLICY = NumericPolicy()


def _error(code: ErrorCode, message: str, field: str | None = None) -> CalculationError:
    return CalculationError(code, message, field)


def _valid_distribution(
    distribution: object, policy: NumericPolicy
) -> CalculationError | None:
    if not isinstance(distribution, PoissonDistribution):
        return _error(
            ErrorCode.CONFIGURATION_ERROR, "distribution must be a PoissonDistribution"
        )
    if not distribution.converged:
        return _error(
            ErrorCode.NUMERIC_CONVERGENCE_FAILED, "distribution must converge"
        )
    if distribution.residual_mass > policy.poisson_residual_tolerance:
        return _error(
            ErrorCode.RESIDUAL_MASS_EXCEEDED, "distribution residual exceeds policy"
        )
    total = stable_sum(distribution.probabilities)
    if isinstance(total, CalculationError) or not math.isclose(
        total,
        distribution.cumulative_probability,
        rel_tol=policy.relative_tolerance,
        abs_tol=policy.probability_sum_tolerance,
    ):
        return _error(
            ErrorCode.PROBABILITY_SUM_INVALID,
            "distribution probabilities are inconsistent",
        )
    residual = 1.0 - distribution.cumulative_probability
    if not math.isclose(
        residual,
        distribution.residual_mass,
        rel_tol=policy.relative_tolerance,
        abs_tol=policy.probability_sum_tolerance,
    ):
        return _error(
            ErrorCode.PROBABILITY_SUM_INVALID, "distribution residual is inconsistent"
        )
    return None


@dataclass(frozen=True, slots=True)
class ScoreProbabilityMatrix:
    """Produto cartesiano materializado de dois suportes Poisson consecutivos."""

    home_distribution: PoissonDistribution
    away_distribution: PoissonDistribution
    probabilities: tuple[tuple[float, ...], ...]
    home_max_goals: int
    away_max_goals: int
    total_probability: float
    residual_mass: float
    warnings: tuple[CalculationWarning, ...] = ()

    def __post_init__(self) -> None:
        policy = _DEFAULT_POLICY
        for distribution, field in (
            (self.home_distribution, "home_distribution"),
            (self.away_distribution, "away_distribution"),
        ):
            if (error := _valid_distribution(distribution, policy)) is not None:
                raise CalculationError(error.code, error.message, field)
        if (
            isinstance(self.home_max_goals, bool)
            or isinstance(self.away_max_goals, bool)
            or not isinstance(self.home_max_goals, int)
            or not isinstance(self.away_max_goals, int)
            or self.home_max_goals != self.home_distribution.max_count
            or self.away_max_goals != self.away_distribution.max_count
        ):
            raise _error(
                ErrorCode.PROBABILITY_SUM_INVALID, "matrix limits are inconsistent"
            )
        if (
            not isinstance(self.probabilities, tuple)
            or len(self.probabilities) != self.home_max_goals + 1
            or any(
                not isinstance(row, tuple) or len(row) != self.away_max_goals + 1
                for row in self.probabilities
            )
        ):
            raise _error(
                ErrorCode.PROBABILITY_SUM_INVALID, "matrix dimensions are inconsistent"
            )
        cells = tuple(cell for row in self.probabilities for cell in row)
        total = stable_sum(cells)
        if isinstance(total, CalculationError) or not math.isfinite(
            self.total_probability
        ):
            raise _error(ErrorCode.PROBABILITY_SUM_INVALID, "matrix total is invalid")
        expected_total = (
            self.home_distribution.cumulative_probability
            * self.away_distribution.cumulative_probability
        )
        expected_residual = 1.0 - expected_total
        if (
            not math.isclose(
                total, self.total_probability, abs_tol=policy.probability_sum_tolerance
            )
            or not math.isclose(
                expected_total,
                self.total_probability,
                abs_tol=policy.probability_sum_tolerance,
            )
            or not math.isclose(
                expected_residual,
                self.residual_mass,
                abs_tol=policy.probability_sum_tolerance,
            )
            or self.total_probability > 1.0 + policy.probability_sum_tolerance
            or self.residual_mass < -policy.probability_sum_tolerance
            or not math.isfinite(self.residual_mass)
        ):
            raise _error(
                ErrorCode.PROBABILITY_SUM_INVALID, "matrix mass is inconsistent"
            )
        if any(not math.isfinite(cell) or cell < 0.0 for cell in cells):
            raise _error(
                ErrorCode.INVALID_PROBABILITY,
                "matrix cells must be finite and non-negative",
            )
        if any(
            not math.isclose(
                self.probabilities[home][away],
                self.home_distribution.probabilities[home]
                * self.away_distribution.probabilities[away],
                abs_tol=policy.probability_sum_tolerance,
            )
            for home in range(self.home_max_goals + 1)
            for away in range(self.away_max_goals + 1)
        ):
            raise _error(
                ErrorCode.PROBABILITY_SUM_INVALID, "matrix cells are inconsistent"
            )
        if not isinstance(self.warnings, tuple) or any(
            not isinstance(warning, CalculationWarning) for warning in self.warnings
        ):
            raise _error(
                ErrorCode.CONFIGURATION_ERROR, "warnings must be typed and immutable"
            )

    def probability_at(
        self, home_goals: object, away_goals: object
    ) -> float | CalculationError:
        """Retorna a probabilidade exata, ou erro para índices fora do suporte."""
        for value, field in ((home_goals, "home_goals"), (away_goals, "away_goals")):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                return _error(
                    ErrorCode.INVALID_NUMBER,
                    "goals must be non-negative integers",
                    field,
                )
        assert isinstance(home_goals, int)
        assert isinstance(away_goals, int)
        if home_goals > self.home_max_goals or away_goals > self.away_max_goals:
            return _error(
                ErrorCode.INVALID_NUMBER, "goals are outside the materialized support"
            )
        return self.probabilities[home_goals][away_goals]


def build_score_probability_matrix(
    home_distribution: PoissonDistribution,
    away_distribution: PoissonDistribution,
    policy: NumericPolicy = _DEFAULT_POLICY,
) -> ScoreProbabilityMatrix | CalculationError:
    """Combina duas distribuições independentes sem renormalizar a massa."""
    if not isinstance(policy, NumericPolicy):
        return _error(
            ErrorCode.CONFIGURATION_ERROR, "policy must be a NumericPolicy", "policy"
        )
    for distribution, field in (
        (home_distribution, "home_distribution"),
        (away_distribution, "away_distribution"),
    ):
        if (error := _valid_distribution(distribution, policy)) is not None:
            return CalculationError(error.code, error.message, field)
    probabilities = tuple(
        tuple(home * away for away in away_distribution.probabilities)
        for home in home_distribution.probabilities
    )
    total = stable_sum(tuple(cell for row in probabilities for cell in row))
    if isinstance(total, CalculationError):
        return _error(
            ErrorCode.PROBABILITY_SUM_INVALID, "matrix probability sum is invalid"
        )
    residual = 1.0 - total
    combined_residual = (
        home_distribution.residual_mass
        + away_distribution.residual_mass
        - home_distribution.residual_mass * away_distribution.residual_mass
    )
    if (
        total > 1.0 + policy.probability_sum_tolerance
        or residual < -policy.probability_sum_tolerance
        or not math.isclose(
            residual, combined_residual, abs_tol=policy.probability_sum_tolerance
        )
    ):
        return _error(
            ErrorCode.RESIDUAL_MASS_EXCEEDED, "combined residual is inconsistent"
        )
    return ScoreProbabilityMatrix(
        home_distribution,
        away_distribution,
        probabilities,
        home_distribution.max_count,
        away_distribution.max_count,
        total,
        residual,
    )
