"""Generative invariants for Asian probabilistic pricing."""

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from lvfi_pricing.distributions import (
    PoissonDistribution,
    ScoreProbabilityMatrix,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.domain import PoissonRate, QuarterLine
from lvfi_pricing.markets import price_asian_handicap, price_asian_total
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection


@settings(max_examples=12, deadline=1000, derandomize=True)
@given(
    home=st.floats(0.0, 4.0, allow_nan=False, allow_infinity=False),
    away=st.floats(0.0, 4.0, allow_nan=False, allow_infinity=False),
    quarters=st.integers(-20, 30),
)
def test_asian_prices_preserve_mass_and_balance(
    home: float, away: float, quarters: int
) -> None:
    distributions = []
    for value in (home, away):
        rate = PoissonRate.create(value)
        assert isinstance(rate, PoissonRate)
        distribution = build_poisson_distribution(rate)
        assert isinstance(distribution, PoissonDistribution)
        distributions.append(distribution)
    matrix = build_score_probability_matrix(distributions[0], distributions[1])
    assert isinstance(matrix, ScoreProbabilityMatrix)
    for price in (
        price_asian_handicap(matrix, HandicapSelection.HOME, QuarterLine(quarters)),
        price_asian_total(matrix, AsianTotalSelection.OVER, QuarterLine(abs(quarters))),
    ):
        assert not isinstance(price, Exception)
        profile = price.expected_profile
        assert all(
            math.isfinite(value) and value >= 0.0
            for value in (
                profile.won_fraction,
                profile.pushed_fraction,
                profile.lost_fraction,
            )
        )
        assert math.isclose(
            profile.won_fraction + profile.pushed_fraction + profile.lost_fraction,
            matrix.total_probability,
            abs_tol=1e-12,
        )
        assert price.residual_mass == matrix.residual_mass
        if price.fair_odds is not None:
            assert math.isclose(
                profile.won_fraction * price.fair_odds.value + profile.pushed_fraction,
                1.0,
                abs_tol=1e-12,
            )
