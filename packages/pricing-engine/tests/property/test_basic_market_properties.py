"""Propriedades dos mercados básicos."""

import math

from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.distributions import (
    PoissonDistribution,
    ScoreProbabilityMatrix,
    build_goal_difference_distribution,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.domain import PoissonRate
from lvfi_pricing.markets import (
    MarketPrices,
    ThreeWaySelection,
    price_btts,
    price_double_chance,
    price_three_way_result,
)


@st.composite
def matrices(draw: st.DrawFn) -> ScoreProbabilityMatrix:
    rates = [
        draw(st.floats(0.01, 10.0, allow_nan=False, allow_infinity=False))
        for _ in range(2)
    ]
    values = [PoissonRate.create(rate) for rate in rates]
    assert all(isinstance(value, PoissonRate) for value in values)
    distributions = [
        build_poisson_distribution(value)
        for value in values
        if isinstance(value, PoissonRate)
    ]
    assert all(isinstance(value, PoissonDistribution) for value in distributions)
    typed = [value for value in distributions if isinstance(value, PoissonDistribution)]
    result = build_score_probability_matrix(typed[0], typed[1])
    assert isinstance(result, ScoreProbabilityMatrix)
    return result


@given(matrices())
def test_basic_markets_preserve_finite_mass_and_odds(
    source: ScoreProbabilityMatrix,
) -> None:
    difference = build_goal_difference_distribution(source)
    assert not hasattr(difference, "code")
    result = price_three_way_result(difference)
    btts = price_btts(source)
    assert isinstance(result, MarketPrices)
    assert isinstance(btts, MarketPrices)
    double = price_double_chance(result)
    assert isinstance(double, MarketPrices)
    for market in (result, double, btts):
        assert all(0.0 <= item.probability.value <= 1.0 for item in market.selections)
        assert all(
            item.fair_odds is None
            or (
                math.isfinite(item.fair_odds.value)
                and item.fair_odds.value >= 1.0 - 1e-8
            )
            for item in market.selections
        )
    assert math.isclose(
        sum(item.probability.value for item in result.selections),
        result.total_probability,
        abs_tol=1e-12,
    )
    assert math.isclose(
        sum(item.probability.value for item in btts.selections),
        btts.total_probability,
        abs_tol=1e-12,
    )
    assert math.isclose(
        sum(item.probability.value for item in double.selections),
        2.0 * result.total_probability,
        abs_tol=1e-12,
    )


@given(st.floats(0.0, 10.0))
def test_equal_rates_are_symmetric(home_rate: float) -> None:
    away_rate = home_rate
    left = PoissonRate.create(home_rate)
    right = PoissonRate.create(away_rate)
    assert isinstance(left, PoissonRate) and isinstance(right, PoissonRate)
    home = build_poisson_distribution(left)
    away = build_poisson_distribution(right)
    assert isinstance(home, PoissonDistribution) and isinstance(
        away, PoissonDistribution
    )
    matrix = build_score_probability_matrix(home, away)
    assert isinstance(matrix, ScoreProbabilityMatrix)
    difference = build_goal_difference_distribution(matrix)
    assert not hasattr(difference, "code")
    result = price_three_way_result(difference)
    assert isinstance(result, MarketPrices)
    assert result.selections[0].selection is ThreeWaySelection.HOME
    assert result.selections[2].selection is ThreeWaySelection.AWAY
    assert math.isclose(
        result.selections[0].probability.value,
        result.selections[2].probability.value,
        abs_tol=1e-12,
    )
