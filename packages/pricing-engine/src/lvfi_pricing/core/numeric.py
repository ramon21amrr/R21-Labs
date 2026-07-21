"""Política e validações numéricas puras."""

import math
from collections.abc import Mapping
from dataclasses import dataclass

from .errors import CalculationError, ErrorCode, SafeValue

Number = int | float


def validate_finite(
    value: object,
    *,
    field: str | None = None,
    context: Mapping[str, SafeValue] | None = None,
) -> CalculationError | None:
    """Retorna erro tipado quando value não é um número finito."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        return CalculationError(
            ErrorCode.INVALID_NUMBER,
            "value must be a finite int or float",
            field,
            {} if context is None else context,
        )
    return None


def _invalid_policy(value: object, field: str) -> CalculationError:
    return CalculationError(
        ErrorCode.CONFIGURATION_ERROR,
        f"{field} must be a finite non-negative float",
        field,
        {"value_type": type(value).__name__},
    )


@dataclass(frozen=True, slots=True)
class NumericPolicy:
    absolute_tolerance: float = 1e-8
    relative_tolerance: float = 1e-8
    probability_sum_tolerance: float = 1e-12
    poisson_residual_tolerance: float = 1e-14

    def __post_init__(self) -> None:
        for name in (
            "absolute_tolerance",
            "relative_tolerance",
            "probability_sum_tolerance",
            "poisson_residual_tolerance",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, float)
                or not math.isfinite(value)
                or value < 0
            ):
                raise _invalid_policy(value, name)


_DEFAULT_POLICY = NumericPolicy()


def is_close(
    a: Number, b: Number, policy: NumericPolicy = _DEFAULT_POLICY
) -> bool | CalculationError:
    for value, field in ((a, "a"), (b, "b")):
        error = validate_finite(value, field=field)
        if error is not None:
            return error
    return abs(a - b) <= max(
        policy.absolute_tolerance, policy.relative_tolerance * max(abs(a), abs(b))
    )


def stable_sum(values: tuple[Number, ...] | list[Number]) -> float | CalculationError:
    for index, value in enumerate(values):
        error = validate_finite(value, field=f"values[{index}]")
        if error is not None:
            return error
    try:
        return math.fsum(values)
    except OverflowError:
        return CalculationError(ErrorCode.INVALID_NUMBER, "stable sum overflowed")


def validate_interval(
    value: Number,
    *,
    minimum: Number | None = None,
    maximum: Number | None = None,
    minimum_inclusive: bool = True,
    maximum_inclusive: bool = True,
    field: str | None = None,
    error_code: ErrorCode = ErrorCode.INVALID_NUMBER,
    context: Mapping[str, SafeValue] | None = None,
) -> CalculationError | None:
    details = {} if context is None else context
    if (error := validate_finite(value, field=field, context=details)) is not None:
        return error
    if minimum is not None and validate_finite(minimum) is not None:
        return CalculationError(
            ErrorCode.CONFIGURATION_ERROR, "minimum must be finite", field, details
        )
    if maximum is not None and validate_finite(maximum) is not None:
        return CalculationError(
            ErrorCode.CONFIGURATION_ERROR, "maximum must be finite", field, details
        )
    if minimum is not None and maximum is not None and minimum > maximum:
        return CalculationError(
            ErrorCode.CONFIGURATION_ERROR,
            "minimum cannot exceed maximum",
            field,
            details,
        )
    lower_ok = minimum is None or (
        value >= minimum if minimum_inclusive else value > minimum
    )
    upper_ok = maximum is None or (
        value <= maximum if maximum_inclusive else value < maximum
    )
    if lower_ok and upper_ok:
        return None
    return CalculationError(
        error_code, "value is outside the permitted interval", field, details
    )
