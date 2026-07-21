"""Erros e avisos determinísticos do Pricing Engine."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class ErrorCode(StrEnum):
    SAMPLE_EMPTY = "sample_empty"
    SAMPLE_INSUFFICIENT = "sample_insufficient"
    MISSING_STATISTIC = "missing_statistic"
    INVALID_STATISTIC = "invalid_statistic"
    INCONSISTENT_DATA = "inconsistent_data"
    INVALID_NUMBER = "invalid_number"
    INVALID_PROBABILITY = "invalid_probability"
    INVALID_ODD = "invalid_odd"
    FAIR_ODD_UNDEFINED = "fair_odd_undefined"
    INVALID_LAMBDA = "invalid_lambda"
    DIVISION_BY_ZERO = "division_by_zero"
    INVALID_WEIGHT = "invalid_weight"
    WEIGHTS_SUM_INVALID = "weights_sum_invalid"
    INVALID_MULTIPLIER = "invalid_multiplier"
    CONFIGURATION_ERROR = "configuration_error"
    MODEL_NOT_APPLICABLE = "model_not_applicable"
    INVALID_MARKET = "invalid_market"
    UNSUPPORTED_MARKET = "unsupported_market"
    INVALID_ASIAN_LINE = "invalid_asian_line"
    NUMERIC_CONVERGENCE_FAILED = "numeric_convergence_failed"
    PROBABILITY_SUM_INVALID = "probability_sum_invalid"
    RESIDUAL_MASS_EXCEEDED = "residual_mass_exceeded"
    SCHEMA_VERSION_UNSUPPORTED = "schema_version_unsupported"
    SERIALIZATION_ERROR = "serialization_error"


class IssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


type SafeValue = (
    None
    | bool
    | int
    | float
    | str
    | tuple["SafeValue", ...]
    | Mapping[str, "SafeValue"]
)


def _safe(value: object) -> SafeValue:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _safe(item)
                for key, item in sorted(value.items())
                if isinstance(key, str)
            }
        )
    if isinstance(value, tuple):
        return tuple(_safe(item) for item in value)
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise TypeError("context contains an unsafe value")


def _safe_context(context: Mapping[str, SafeValue]) -> Mapping[str, SafeValue]:
    if not isinstance(context, Mapping) or any(
        not isinstance(key, str) for key in context
    ):
        raise TypeError("context must map string keys to safe values")
    return MappingProxyType({key: _safe(context[key]) for key in sorted(context)})


@dataclass(frozen=True, slots=True)
class CalculationError(Exception):
    code: ErrorCode
    message: str
    field: str | None = None
    context: Mapping[str, SafeValue] = MappingProxyType({})

    def __post_init__(self) -> None:
        if (
            not isinstance(self.code, ErrorCode)
            or not isinstance(self.message, str)
            or (self.field is not None and not isinstance(self.field, str))
        ):
            raise TypeError("invalid CalculationError fields")
        Exception.__init__(self, self.message)
        object.__setattr__(self, "context", _safe_context(self.context))


@dataclass(frozen=True, slots=True)
class CalculationWarning:
    code: ErrorCode
    message: str
    severity: IssueSeverity = IssueSeverity.WARNING
    field: str | None = None
    context: Mapping[str, SafeValue] = MappingProxyType({})

    def __post_init__(self) -> None:
        if (
            not isinstance(self.code, ErrorCode)
            or not isinstance(self.message, str)
            or not isinstance(self.severity, IssueSeverity)
            or (self.field is not None and not isinstance(self.field, str))
        ):
            raise TypeError("invalid CalculationWarning fields")
        object.__setattr__(self, "context", _safe_context(self.context))
