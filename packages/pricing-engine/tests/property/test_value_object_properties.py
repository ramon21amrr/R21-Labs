from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.domain import (
    FairOdds,
    Multiplier,
    PoissonRate,
    Probability,
    QuarterLine,
    Weight,
)


@given(
    st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False, width=64)
)
def test_probability_invariant(value: float) -> None:
    result = Probability.create(value)
    assert isinstance(result, Probability) and 0.0 <= result.value <= 1.0


@given(st.floats(min_value=0, allow_nan=False, allow_infinity=False, width=64))
def test_poisson_rate_invariant(value: float) -> None:
    result = PoissonRate.create(value)
    assert isinstance(result, PoissonRate) and result.value >= 0.0


@given(
    st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False, width=64)
)
def test_weight_invariant(value: float) -> None:
    result = Weight.create(value)
    assert isinstance(result, Weight) and 0.0 <= result.value <= 1.0


@given(
    st.floats(
        min_value=0, exclude_min=True, allow_nan=False, allow_infinity=False, width=64
    )
)
def test_multiplier_invariant(value: float) -> None:
    result = Multiplier.create(value)
    assert isinstance(result, Multiplier) and result.value > 0.0


@given(st.integers())
def test_quarter_line_preserves_integer(value: int) -> None:
    result = QuarterLine.create(value)
    assert isinstance(result, QuarterLine)
    assert result.quarters == value
    assert result.decimal_value == value / 4.0


@given(st.floats(allow_nan=False, allow_infinity=False, width=64))
def test_fair_odds_of_positive_probability_is_at_least_one(value: float) -> None:
    probability = Probability.create(abs(value) % 1.0)
    if isinstance(probability, Probability) and probability.value > 0.0:
        result = FairOdds.from_probability(probability)
        assert isinstance(result, FairOdds) and result.value >= 1.0
