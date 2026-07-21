"""Propriedades determinísticas da distribuição de diferenças."""

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from lvfi_pricing.distributions import (
    GoalDifferenceDistribution,
    PoissonDistribution,
    build_goal_difference_distribution,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.domain import PoissonRate

rates = st.floats(
    min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False, width=64
)


@settings(database=None, derandomize=True)
@given(rates, rates)
def test_difference_invariants(home_value: float, away_value: float) -> None:
    home_rate = PoissonRate.create(home_value)
    away_rate = PoissonRate.create(away_value)
    assert isinstance(home_rate, PoissonRate)
    assert isinstance(away_rate, PoissonRate)
    home = build_poisson_distribution(home_rate)
    away = build_poisson_distribution(away_rate)
    assert isinstance(home, PoissonDistribution)
    assert isinstance(away, PoissonDistribution)
    matrix = build_score_probability_matrix(home, away)
    assert not isinstance(matrix, Exception)
    result = build_goal_difference_distribution(matrix)
    assert isinstance(result, GoalDifferenceDistribution)
    assert result.min_difference == -matrix.away_max_goals
    assert result.max_difference == matrix.home_max_goals
    assert math.isclose(
        math.fsum(result.probabilities), matrix.total_probability, abs_tol=1e-12
    )
    assert all(math.isfinite(value) and value >= 0.0 for value in result.probabilities)
