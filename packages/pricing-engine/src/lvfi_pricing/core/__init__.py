"""Tipos fundamentais de erros, avisos e validação numérica."""

from .errors import CalculationError, CalculationWarning, ErrorCode, IssueSeverity
from .numeric import (
    NumericPolicy,
    is_close,
    stable_sum,
    validate_finite,
    validate_interval,
)

__all__ = (
    "CalculationError",
    "CalculationWarning",
    "ErrorCode",
    "IssueSeverity",
    "NumericPolicy",
    "is_close",
    "stable_sum",
    "validate_finite",
    "validate_interval",
)
