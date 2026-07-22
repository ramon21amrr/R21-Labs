import math

from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.models.method_one import (
    ContextualAverage,
    calculate_contextual_average,
)
from tests.unit.models.method_one.test_averages import sample


@given(
    st.lists(
        st.floats(
            min_value=0,
            max_value=1e100,
            allow_nan=False,
            allow_infinity=False,
        ),
        min_size=1,
        max_size=20,
    )
)
def test_uniform_average_matches_stable_sum(values: list[float]) -> None:
    source = sample(tuple(values))
    first = calculate_contextual_average(source)
    second = calculate_contextual_average(source)
    assert isinstance(first, ContextualAverage)
    assert first == second
    assert first.numerator == math.fsum(values)
    assert first.value == math.fsum(values) / len(values)
    assert first.valid_count == len(values)
    assert first.effective_weights == (1.0,) * len(values)


@given(st.integers(min_value=1, max_value=20))
def test_zero_is_always_a_valid_observed_value(count: int) -> None:
    result = calculate_contextual_average(sample((0.0,) * count))
    assert isinstance(result, ContextualAverage)
    assert result.value == 0.0
    assert result.used_match_ids == tuple(f"match-{index}" for index in range(count))
