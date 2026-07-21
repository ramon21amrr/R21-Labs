"""Propriedades determinísticas da matriz de placares."""

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from lvfi_pricing.distributions import (
    PoissonDistribution,
    ScoreProbabilityMatrix,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.domain import PoissonRate

rates = st.floats(
    min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False, width=64
)


@settings(database=None, deadline=None, derandomize=True)
@given(rates, rates)
def test_matrix_invariants(home_value: float, away_value: float) -> None:
    home_rate = PoissonRate.create(home_value)
    away_rate = PoissonRate.create(away_value)
    assert isinstance(home_rate, PoissonRate)
    assert isinstance(away_rate, PoissonRate)
    home = build_poisson_distribution(home_rate)
    away = build_poisson_distribution(away_rate)
    assert isinstance(home, PoissonDistribution)
    assert isinstance(away, PoissonDistribution)
    matrix = build_score_probability_matrix(home, away)
    assert isinstance(matrix, ScoreProbabilityMatrix)
    assert len(matrix.probabilities) == home.max_count + 1
    assert all(len(row) == away.max_count + 1 for row in matrix.probabilities)
    assert math.isclose(
        math.fsum(cell for row in matrix.probabilities for cell in row),
        matrix.total_probability,
        abs_tol=1e-12,
    )
    assert math.isclose(
        matrix.total_probability,
        home.cumulative_probability * away.cumulative_probability,
        abs_tol=1e-12,
    )
    assert matrix == build_score_probability_matrix(home, away)
