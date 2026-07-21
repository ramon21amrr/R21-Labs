"""Value objects imutáveis para os contratos matemáticos fundamentais."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from lvfi_pricing.core.errors import CalculationError, ErrorCode, SafeValue
from lvfi_pricing.core.numeric import (
    NumericPolicy,
    is_close,
    stable_sum,
    validate_finite,
    validate_interval,
)

_DEFAULT_POLICY = NumericPolicy()


def _invalid(
    value: object, code: ErrorCode, message: str, field: str
) -> CalculationError:
    return CalculationError(
        code,
        message,
        field,
        {"value_type": type(value).__name__},
    )


def _float_value(
    value: object, code: ErrorCode, field: str
) -> float | CalculationError:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return _invalid(value, code, "value must be a finite int or float", field)
    try:
        finite_error = validate_finite(value, field=field)
    except OverflowError:
        finite_error = _invalid(value, code, "value must be finite", field)
    if finite_error is not None:
        return _invalid(value, code, "value must be finite", field)
    return float(value)


@dataclass(frozen=True, slots=True)
class Probability:
    """Probabilidade binary64 no intervalo fechado [0, 1]."""

    value: float

    @classmethod
    def create(cls, value: object) -> Probability | CalculationError:
        numeric = _float_value(value, ErrorCode.INVALID_PROBABILITY, "probability")
        if isinstance(numeric, CalculationError):
            return numeric
        error = validate_interval(
            numeric,
            minimum=0.0,
            maximum=1.0,
            field="probability",
            error_code=ErrorCode.INVALID_PROBABILITY,
        )
        if error is not None:
            return error
        return cls(numeric)


@dataclass(frozen=True, slots=True)
class FairOdds:
    """Odd decimal justa, sem arredondamento interno."""

    value: float

    @classmethod
    def create(cls, value: object) -> FairOdds | CalculationError:
        numeric = _float_value(value, ErrorCode.INVALID_ODD, "fair_odds")
        if isinstance(numeric, CalculationError):
            return numeric
        error = validate_interval(
            numeric,
            minimum=1.0,
            field="fair_odds",
            error_code=ErrorCode.INVALID_ODD,
        )
        if error is not None:
            return error
        return cls(numeric)

    @classmethod
    def from_probability(cls, probability: Probability) -> FairOdds | CalculationError:
        if not isinstance(probability, Probability):
            return _invalid(
                probability,
                ErrorCode.INVALID_PROBABILITY,
                "probability must be a Probability",
                "probability",
            )
        if probability.value == 0.0:
            return CalculationError(
                ErrorCode.FAIR_ODD_UNDEFINED,
                "fair odds are undefined for zero probability",
                "probability",
            )
        return cls(1.0 / probability.value)


@dataclass(frozen=True, slots=True)
class PoissonRate:
    """Taxa lambda binary64 não negativa para uso futuro em Poisson."""

    value: float

    @classmethod
    def create(cls, value: object) -> PoissonRate | CalculationError:
        numeric = _float_value(value, ErrorCode.INVALID_LAMBDA, "lambda")
        if isinstance(numeric, CalculationError):
            return numeric
        error = validate_interval(
            numeric,
            minimum=0.0,
            field="lambda",
            error_code=ErrorCode.INVALID_LAMBDA,
        )
        if error is not None:
            return error
        return cls(numeric)


@dataclass(frozen=True, slots=True)
class Weight:
    """Peso binary64 no intervalo fechado [0, 1]."""

    value: float

    @classmethod
    def create(cls, value: object) -> Weight | CalculationError:
        numeric = _float_value(value, ErrorCode.INVALID_WEIGHT, "weight")
        if isinstance(numeric, CalculationError):
            return numeric
        error = validate_interval(
            numeric,
            minimum=0.0,
            maximum=1.0,
            field="weight",
            error_code=ErrorCode.INVALID_WEIGHT,
        )
        if error is not None:
            return error
        return cls(numeric)

    @classmethod
    def validate_collection(
        cls,
        weights: Sequence[Weight],
        policy: NumericPolicy = _DEFAULT_POLICY,
    ) -> None | CalculationError:
        if not weights:
            return CalculationError(
                ErrorCode.WEIGHTS_SUM_INVALID,
                "weights collection must not be empty",
                "weights",
            )
        if any(not isinstance(weight, cls) for weight in weights):
            return CalculationError(
                ErrorCode.INVALID_WEIGHT,
                "weights collection must contain Weight values",
                "weights",
            )
        total = stable_sum([weight.value for weight in weights])
        if isinstance(total, CalculationError):
            return total
        comparison = is_close(total, 1.0, policy)
        if isinstance(comparison, CalculationError) or not comparison:
            context: dict[str, SafeValue] = {"count": len(weights)}
            return CalculationError(
                ErrorCode.WEIGHTS_SUM_INVALID,
                "weights must sum to one within numeric tolerance",
                "weights",
                context,
            )
        return None


@dataclass(frozen=True, slots=True)
class Multiplier:
    """Multiplicador positivo, sem faixa rígida de operação."""

    value: float

    @classmethod
    def create(cls, value: object) -> Multiplier | CalculationError:
        numeric = _float_value(value, ErrorCode.INVALID_MULTIPLIER, "multiplier")
        if isinstance(numeric, CalculationError):
            return numeric
        error = validate_interval(
            numeric,
            minimum=0.0,
            minimum_inclusive=False,
            field="multiplier",
            error_code=ErrorCode.INVALID_MULTIPLIER,
        )
        if error is not None:
            return error
        return cls(numeric)


@dataclass(frozen=True, slots=True)
class QuarterLine:
    """Linha asiática armazenada exatamente como quantidade inteira de quartos."""

    quarters: int

    @classmethod
    def create(cls, value: object) -> QuarterLine | CalculationError:
        if isinstance(value, bool) or not isinstance(value, int):
            return _invalid(
                value,
                ErrorCode.INVALID_ASIAN_LINE,
                "quarter line must be an integer number of quarters",
                "quarter_line",
            )
        return cls(value)

    @property
    def decimal_value(self) -> float:
        return self.quarters / 4.0
