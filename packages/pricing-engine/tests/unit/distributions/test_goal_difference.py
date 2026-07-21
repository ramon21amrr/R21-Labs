"""Testes unitários da distribuição de diferença de gols."""

import math
from dataclasses import FrozenInstanceError

import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.distributions import (
    GoalDifferenceDistribution,
    PoissonDistribution,
    build_goal_difference_distribution,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.distributions import goal_difference as difference_module
from lvfi_pricing.domain import PoissonRate


def goal_difference(home_rate: float, away_rate: float) -> GoalDifferenceDistribution:
    home_rate_result = PoissonRate.create(home_rate)
    away_rate_result = PoissonRate.create(away_rate)
    assert isinstance(home_rate_result, PoissonRate)
    assert isinstance(away_rate_result, PoissonRate)
    home = build_poisson_distribution(home_rate_result)
    away = build_poisson_distribution(away_rate_result)
    assert isinstance(home, PoissonDistribution)
    assert isinstance(away, PoissonDistribution)
    matrix = build_score_probability_matrix(home, away)
    assert not isinstance(matrix, CalculationError)
    result = build_goal_difference_distribution(matrix)
    assert isinstance(result, GoalDifferenceDistribution)
    return result


@pytest.mark.parametrize(
    "home_rate, away_rate",
    [
        (0.0, 0.0),
        (0.5, 0.5),
        (1.0, 1.0),
        (1.5, 1.0),
        (1.0, 1.5),
        (2.5, 1.2),
        (5.0, 3.0),
        (10.0, 10.0),
    ],
)
def test_difference_reference_cases(home_rate: float, away_rate: float) -> None:
    result = goal_difference(home_rate, away_rate)
    assert result.max_difference - result.min_difference + 1 == len(
        result.probabilities
    )
    assert math.isclose(
        sum(result.probabilities), result.total_probability, abs_tol=1e-12
    )
    assert all(math.isfinite(value) and value >= 0.0 for value in result.probabilities)
    assert math.isclose(
        result.probability_home_negative_difference()
        + result.probability_zero_difference()
        + result.probability_home_positive_difference(),
        result.total_probability,
        abs_tol=1e-12,
    )


def test_difference_symmetry_asymmetry_and_access() -> None:
    symmetric = goal_difference(1.0, 1.0)
    assert math.isclose(
        symmetric.probability_home_positive_difference(),
        symmetric.probability_home_negative_difference(),
        abs_tol=1e-12,
    )
    assert (
        goal_difference(2.0, 0.5).probability_home_positive_difference()
        > goal_difference(2.0, 0.5).probability_home_negative_difference()
    )
    assert (
        goal_difference(0.5, 2.0).probability_home_negative_difference()
        > goal_difference(0.5, 2.0).probability_home_positive_difference()
    )
    zero = goal_difference(0.0, 0.0)
    assert zero.probability_zero_difference() == 1.0
    assert zero.probability_for_difference(0) == 1.0
    for value in (True, "0", 100):
        rejected = zero.probability_for_difference(value)
        assert isinstance(rejected, CalculationError)
        assert rejected.code is ErrorCode.INVALID_NUMBER
    with pytest.raises(FrozenInstanceError):
        zero.max_difference = 0  # type: ignore[misc]
    assert zero == goal_difference(0.0, 0.0)


def test_difference_rejects_invalid_inputs_and_contracts() -> None:
    result = build_goal_difference_distribution(object())  # type: ignore[arg-type]
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.CONFIGURATION_ERROR
    valid = goal_difference(0.0, 0.0)
    with pytest.raises(CalculationError, match="difference support"):
        GoalDifferenceDistribution(1, 0, (), 0.0, 1.0)
    with pytest.raises(CalculationError, match="difference mass"):
        GoalDifferenceDistribution(0, 0, (1.0,), 0.5, 0.5)
    with pytest.raises(CalculationError, match="difference probabilities"):
        GoalDifferenceDistribution(-1, 0, (2.0, -1.0), 1.0, 0.0)
    assert valid.warnings == ()


def test_difference_validation_failure_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(CalculationError, match="warnings"):
        GoalDifferenceDistribution(0, 0, (1.0,), 1.0, 0.0, (object(),))  # type: ignore[arg-type]
    result = build_goal_difference_distribution(object(), object())  # type: ignore[arg-type]
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.CONFIGURATION_ERROR
    rate = PoissonRate.create(0.0)
    assert isinstance(rate, PoissonRate)
    poisson = build_poisson_distribution(rate)
    assert isinstance(poisson, PoissonDistribution)
    matrix = build_score_probability_matrix(poisson, poisson)
    assert not isinstance(matrix, CalculationError)
    monkeypatch.setattr(
        difference_module,
        "stable_sum",
        lambda _: CalculationError(ErrorCode.INVALID_NUMBER, "bad"),
    )
    result = build_goal_difference_distribution(matrix)
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.PROBABILITY_SUM_INVALID
    monkeypatch.setattr(difference_module, "stable_sum", math.fsum)
    object.__setattr__(matrix, "total_probability", 0.0)
    result = build_goal_difference_distribution(matrix)
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.PROBABILITY_SUM_INVALID
