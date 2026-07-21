import dataclasses
from typing import cast

import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy
from lvfi_pricing.domain import (
    FairOdds,
    Multiplier,
    PoissonRate,
    Probability,
    QuarterLine,
    Weight,
)


def assert_error(result: object, code: ErrorCode) -> None:
    assert isinstance(result, CalculationError)
    assert result.code is code


@pytest.mark.parametrize("value", [0, 0.5, 1])
def test_probability_valid(value: int | float) -> None:
    result = Probability.create(value)
    assert isinstance(result, Probability) and result.value == float(value)


@pytest.mark.parametrize("value", [-1, 2, True, "0.5", float("nan"), float("inf")])
def test_probability_invalid(value: object) -> None:
    assert_error(Probability.create(value), ErrorCode.INVALID_PROBABILITY)


def test_probability_immutable_and_equal() -> None:
    first = Probability.create(0.25)
    second = Probability.create(0.25)
    assert isinstance(first, Probability) and first == second
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.value = 0.5  # type: ignore[misc]


@pytest.mark.parametrize("value", [1, 2.5])
def test_fair_odds_valid(value: int | float) -> None:
    result = FairOdds.create(value)
    assert isinstance(result, FairOdds) and result.value == float(value)


@pytest.mark.parametrize("value", [0, 0.99, True, "2", float("nan"), float("inf")])
def test_fair_odds_invalid(value: object) -> None:
    assert_error(FairOdds.create(value), ErrorCode.INVALID_ODD)


def test_fair_odds_from_probability() -> None:
    zero = Probability.create(0)
    one = Probability.create(1)
    half = Probability.create(0.5)
    assert isinstance(zero, Probability) and isinstance(one, Probability)
    assert isinstance(half, Probability)
    assert_error(FairOdds.from_probability(zero), ErrorCode.FAIR_ODD_UNDEFINED)
    assert FairOdds.from_probability(one) == FairOdds(1.0)
    assert FairOdds.from_probability(half) == FairOdds(2.0)
    assert_error(
        FairOdds.from_probability(cast(Probability, object())),
        ErrorCode.INVALID_PROBABILITY,
    )


@pytest.mark.parametrize("value", [0, 2.5])
def test_poisson_rate_valid(value: int | float) -> None:
    result = PoissonRate.create(value)
    assert isinstance(result, PoissonRate) and result.value == float(value)


@pytest.mark.parametrize(
    "value", [-1, True, "1", float("nan"), float("inf"), float("-inf")]
)
def test_poisson_rate_invalid(value: object) -> None:
    assert_error(PoissonRate.create(value), ErrorCode.INVALID_LAMBDA)


@pytest.mark.parametrize("value", [0, 0.5, 1])
def test_weight_valid(value: int | float) -> None:
    result = Weight.create(value)
    assert isinstance(result, Weight) and result.value == float(value)


@pytest.mark.parametrize("value", [-1, 2, True, "0.5", float("nan")])
def test_weight_invalid(value: object) -> None:
    assert_error(Weight.create(value), ErrorCode.INVALID_WEIGHT)


def test_weight_collection_uses_stable_sum_and_tolerance() -> None:
    one = Weight.create(1.0)
    zero = Weight.create(0.0)
    assert isinstance(one, Weight) and isinstance(zero, Weight)
    assert Weight.validate_collection([one, zero]) is None
    assert_error(Weight.validate_collection([]), ErrorCode.WEIGHTS_SUM_INVALID)
    assert_error(Weight.validate_collection([one, one]), ErrorCode.WEIGHTS_SUM_INVALID)
    assert_error(
        Weight.validate_collection(cast(list[Weight], [one, object()])),
        ErrorCode.INVALID_WEIGHT,
    )
    near = Weight.create(1.0 - 5e-9)
    assert isinstance(near, Weight)
    policy = NumericPolicy(1e-8, 1e-8, 1e-12, 1e-14)
    assert Weight.validate_collection([near], policy) is None
    assert_error(
        Weight.validate_collection([Weight(float("nan"))]), ErrorCode.INVALID_NUMBER
    )


def test_integer_overflow_is_typed() -> None:
    assert_error(Probability.create(10**1000), ErrorCode.INVALID_PROBABILITY)


@pytest.mark.parametrize("value", [1, 0.5, 1.1])
def test_multiplier_valid(value: int | float) -> None:
    result = Multiplier.create(value)
    assert isinstance(result, Multiplier) and result.value == float(value)


@pytest.mark.parametrize("value", [0, -1, True, "1", float("nan"), float("inf")])
def test_multiplier_invalid(value: object) -> None:
    assert_error(Multiplier.create(value), ErrorCode.INVALID_MULTIPLIER)


@pytest.mark.parametrize(
    ("quarters", "decimal"),
    [
        (0, 0.0),
        (1, 0.25),
        (2, 0.5),
        (3, 0.75),
        (4, 1.0),
        (-1, -0.25),
        (-2, -0.5),
        (-3, -0.75),
        (-5, -1.25),
    ],
)
def test_quarter_line(quarters: int, decimal: float) -> None:
    result = QuarterLine.create(quarters)
    assert isinstance(result, QuarterLine)
    assert result.quarters == quarters
    assert result.decimal_value == decimal


@pytest.mark.parametrize("value", [True, 0.25, 0.1, 0.3, "1"])
def test_quarter_line_rejects_noncanonical_constructor_values(value: object) -> None:
    assert_error(QuarterLine.create(value), ErrorCode.INVALID_ASIAN_LINE)
