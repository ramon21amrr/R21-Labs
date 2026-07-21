"""Propriedades dos totais simples."""

import math

from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.distributions import (
    PoissonDistribution,
    ScoreProbabilityMatrix,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.domain import PoissonRate
from lvfi_pricing.markets import (
    HalfGoalLine,
    MarketPrices,
    TotalSelection,
    price_total_goals,
)


@st.composite
def source_matrices(draw: st.DrawFn) -> ScoreProbabilityMatrix:
    rates = [
        draw(st.floats(0.0, 10.0, allow_nan=False, allow_infinity=False))
        for _ in range(2)
    ]
    typed_rates = [PoissonRate.create(rate) for rate in rates]
    assert all(isinstance(rate, PoissonRate) for rate in typed_rates)
    distributions = [
        build_poisson_distribution(rate)
        for rate in typed_rates
        if isinstance(rate, PoissonRate)
    ]
    assert all(isinstance(value, PoissonDistribution) for value in distributions)
    typed = [value for value in distributions if isinstance(value, PoissonDistribution)]
    result = build_score_probability_matrix(typed[0], typed[1])
    assert isinstance(result, ScoreProbabilityMatrix)
    return result


@given(source_matrices(), st.sampled_from([1, 3, 5, 7, 9, 11]))
def test_totals_partition_and_are_monotonic(
    source: ScoreProbabilityMatrix, lower_units: int
) -> None:
    lower = HalfGoalLine.create(lower_units)
    assert isinstance(lower, HalfGoalLine)
    lower_market = price_total_goals(source, lower)
    assert isinstance(lower_market, MarketPrices)
    assert tuple(item.selection for item in lower_market.selections) == (
        TotalSelection.OVER,
        TotalSelection.UNDER,
    )
    assert math.isclose(
        sum(item.probability.value for item in lower_market.selections),
        source.total_probability,
        abs_tol=1e-12,
    )
    for item in lower_market.selections:
        if item.fair_odds is not None:
            assert math.isclose(item.fair_odds.value, 1.0 / item.probability.value)
