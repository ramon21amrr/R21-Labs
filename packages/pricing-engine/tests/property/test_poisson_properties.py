"""Propriedades determinísticas da distribuição Poisson."""

import math

from hypothesis import given, settings
from hypothesis import strategies as st

from lvfi_pricing.core.errors import CalculationError
from lvfi_pricing.distributions import (
    PoissonDistribution,
    build_poisson_distribution,
    poisson_pmf,
)
from lvfi_pricing.domain import PoissonRate

rates = st.floats(
    min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False, width=64
)


@settings(database=None, derandomize=True)
@given(rates)
def test_distribution_invariants(value: float) -> None:
    rate = PoissonRate.create(value)
    assert isinstance(rate, PoissonRate)
    result = build_poisson_distribution(rate)
    assert isinstance(result, PoissonDistribution)
    assert result.max_count == len(result.probabilities) - 1
    assert result.cumulative_probability <= 1.0 + 1e-12
    assert result.residual_mass >= -1e-12
    assert result.residual_mass <= 1e-14
    assert all(math.isfinite(item) and item >= 0.0 for item in result.probabilities)
    assert result == build_poisson_distribution(rate)


@settings(database=None, derandomize=True)
@given(rates, st.integers(min_value=0, max_value=50))
def test_pmf_recurrence_and_boolean_rejection(value: float, count: int) -> None:
    rate = PoissonRate.create(value)
    assert isinstance(rate, PoissonRate)
    pmf = poisson_pmf(rate, count)
    assert isinstance(pmf, float) and math.isfinite(pmf) and pmf >= 0.0
    rejected = poisson_pmf(rate, True)
    assert isinstance(rejected, CalculationError)
    if count > 0:
        previous = poisson_pmf(rate, count - 1)
        assert isinstance(previous, float)
        assert math.isclose(pmf, previous * rate.value / count, rel_tol=1e-15)


def test_zero_is_degenerate() -> None:
    rate = PoissonRate.create(0.0)
    assert isinstance(rate, PoissonRate)
    result = build_poisson_distribution(rate)
    assert isinstance(result, PoissonDistribution)
    assert result.probabilities == (1.0,) + (0.0,) * 10
