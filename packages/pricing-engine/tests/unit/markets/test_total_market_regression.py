"""Deterministic regression tests for total-market partition stability."""

from __future__ import annotations

import math

import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.distributions import (
    GoalDifferenceDistribution,
    PoissonDistribution,
    ScoreProbabilityMatrix,
    build_goal_difference_distribution,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.domain import PoissonRate, Probability
from lvfi_pricing.markets import (
    HalfGoalLine,
    MarketPrices,
    price_btts,
    price_three_way_result,
    price_total_goals,
)


def _matrix(rate: float) -> ScoreProbabilityMatrix:
    typed_rate = PoissonRate.create(rate)
    assert isinstance(typed_rate, PoissonRate)
    distribution = build_poisson_distribution(typed_rate)
    assert isinstance(distribution, PoissonDistribution)
    result = build_score_probability_matrix(distribution, distribution)
    assert isinstance(result, ScoreProbabilityMatrix)
    return result


@pytest.mark.parametrize(
    ("rate", "units"),
    (
        (0.001953125, 11),
        (2.0**-20, 11),
        (10.0, 1),
    ),
)
def test_total_partition_is_stable_at_small_rates_and_both_complement_paths(
    rate: float, units: int
) -> None:
    source = _matrix(rate)
    line = HalfGoalLine.create(units)
    assert isinstance(line, HalfGoalLine)

    first = price_total_goals(source, line)
    second = price_total_goals(source, line)

    assert isinstance(first, MarketPrices)
    assert first == second
    assert math.isclose(
        sum(item.probability.value for item in first.selections),
        source.total_probability,
        abs_tol=1e-12,
    )
    assert all(0.0 <= item.probability.value <= 1.0 for item in first.selections)


def test_original_minimal_rate_case_preserves_other_market_types() -> None:
    source = _matrix(0.001953125)

    btts = price_btts(source)
    difference = build_goal_difference_distribution(source)
    assert isinstance(difference, GoalDifferenceDistribution)
    three_way = price_three_way_result(difference)

    assert isinstance(btts, MarketPrices)
    assert isinstance(three_way, MarketPrices)


def test_probability_contract_rejects_a_materially_out_of_range_value() -> None:
    invalid = Probability.create(math.nextafter(1.0, math.inf))

    assert isinstance(invalid, CalculationError)
    assert invalid.code is ErrorCode.INVALID_PROBABILITY
