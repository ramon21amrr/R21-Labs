import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.core.numeric import (
    NumericPolicy,
    is_close,
    stable_sum,
    validate_finite,
    validate_interval,
)


def test_policy_defaults_and_invalid_values() -> None:
    assert NumericPolicy() == NumericPolicy(1e-8, 1e-8, 1e-12, 1e-14)
    for value in (-1.0, True, "1", float("nan"), float("inf"), float("-inf")):
        with pytest.raises(CalculationError) as raised:
            NumericPolicy(absolute_tolerance=value)  # type: ignore[arg-type]
        assert raised.value.code is ErrorCode.CONFIGURATION_ERROR


@pytest.mark.parametrize("value", [1, 1.5, -2])
def test_validate_finite_accepts_finite_numbers(value: int | float) -> None:
    assert validate_finite(value) is None


@pytest.mark.parametrize(
    "value", [True, "1", float("nan"), float("inf"), float("-inf")]
)
def test_validate_finite_rejects_invalid_values(value: object) -> None:
    result = validate_finite(value)
    assert (
        isinstance(result, CalculationError) and result.code is ErrorCode.INVALID_NUMBER
    )


def test_is_close_formula() -> None:
    assert is_close(1.0, 1.0) is True
    assert is_close(1.0, 1.0 + 5e-9) is True
    assert is_close(1e8, 1e8 + 0.5) is True
    assert is_close(1e8, 1e8 + 2.0) is False
    assert is_close(1e-15, -1e-15) is True
    assert is_close(1.0, 1.0 + 2e-8) == is_close(1.0 + 2e-8, 1.0)
    assert isinstance(is_close(True, 1.0), CalculationError)


def test_stable_sum() -> None:
    assert stable_sum([1e16, 1.0, -1e16]) == 1.0
    assert isinstance(stable_sum([float("1e308"), float("1e308")]), CalculationError)
    assert isinstance(stable_sum([True]), CalculationError)


@pytest.mark.parametrize(
    ("value", "minimum", "maximum", "minimum_inclusive", "maximum_inclusive"),
    [
        (0.5, 0, 1, True, True),
        (0.5, 0, 1, False, True),
        (0.5, None, 1, True, False),
        (0.5, 0, None, False, True),
    ],
)
def test_intervals(
    value: float,
    minimum: int | None,
    maximum: int | None,
    minimum_inclusive: bool,
    maximum_inclusive: bool,
) -> None:
    assert (
        validate_interval(
            value,
            minimum=minimum,
            maximum=maximum,
            minimum_inclusive=minimum_inclusive,
            maximum_inclusive=maximum_inclusive,
        )
        is None
    )


def test_interval_error_is_typed_and_deterministic() -> None:
    first = validate_interval(
        2,
        minimum=0,
        maximum=1,
        field="p",
        error_code=ErrorCode.INVALID_PROBABILITY,
        context={"source": "test"},
    )
    second = validate_interval(
        2,
        minimum=0,
        maximum=1,
        field="p",
        error_code=ErrorCode.INVALID_PROBABILITY,
        context={"source": "test"},
    )
    assert first == second
    assert (
        isinstance(first, CalculationError)
        and first.code is ErrorCode.INVALID_PROBABILITY
    )
    invalid_bounds = validate_interval(1, minimum=2, maximum=1)
    assert (
        isinstance(invalid_bounds, CalculationError)
        and invalid_bounds.code is ErrorCode.CONFIGURATION_ERROR
    )
    assert isinstance(validate_interval(float("nan")), CalculationError)
    assert isinstance(validate_interval(1, minimum=float("nan")), CalculationError)
    assert isinstance(validate_interval(1, maximum=float("inf")), CalculationError)
