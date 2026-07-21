from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.core.numeric import is_close, stable_sum, validate_finite

finite_numbers = st.integers() | st.floats(
    allow_nan=False, allow_infinity=False, width=64
)


@given(finite_numbers)
def test_finite_values_are_accepted_and_reflexive(value: int | float) -> None:
    assert validate_finite(value) is None
    assert is_close(value, value) is True


@given(finite_numbers, finite_numbers)
def test_is_close_is_symmetric(a: int | float, b: int | float) -> None:
    assert is_close(a, b) == is_close(b, a)


@given(st.lists(finite_numbers, max_size=20))
def test_stable_sum_is_deterministic(values: list[int | float]) -> None:
    assert stable_sum(values) == stable_sum(values)
