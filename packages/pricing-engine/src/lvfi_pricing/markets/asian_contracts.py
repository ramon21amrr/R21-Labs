"""Immutable contracts for deterministic Asian market pricing."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy, is_close, stable_sum
from lvfi_pricing.domain import FairOdds, Probability, QuarterLine
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection

_DEFAULT_POLICY = NumericPolicy()


class AsianMarketCode(StrEnum):
    """Canonical Asian market families."""

    HANDICAP = "asian_handicap"
    TOTAL = "asian_total"


def _error(code: ErrorCode, message: str, field: str) -> CalculationError:
    return CalculationError(code, message, field)


def _finite_non_negative(value: object, field: str) -> bool:
    return isinstance(value, float) and math.isfinite(value) and value >= 0.0


@dataclass(frozen=True, slots=True)
class AsianSettlementProbabilities:
    """Probability mass in the canonical five-state settlement order."""

    win: Probability
    half_win: Probability
    push: Probability
    half_loss: Probability
    loss: Probability
    total_probability: float
    residual_mass: float

    def __post_init__(self) -> None:
        values = (self.win, self.half_win, self.push, self.half_loss, self.loss)
        if any(not isinstance(value, Probability) for value in values):
            raise _error(
                ErrorCode.INVALID_PROBABILITY,
                "states must be Probability values",
                "states",
            )
        if not _finite_non_negative(self.total_probability, "total_probability"):
            raise _error(
                ErrorCode.INVALID_PROBABILITY,
                "total probability is invalid",
                "total_probability",
            )
        if (
            not isinstance(self.residual_mass, float)
            or not math.isfinite(self.residual_mass)
            or self.residual_mass < -_DEFAULT_POLICY.probability_sum_tolerance
        ):
            raise _error(
                ErrorCode.RESIDUAL_MASS_EXCEEDED,
                "residual mass is invalid",
                "residual_mass",
            )
        total = stable_sum([value.value for value in values])
        close = (
            is_close(total, self.total_probability, _DEFAULT_POLICY)
            if not isinstance(total, CalculationError)
            else total
        )
        if isinstance(close, CalculationError) or not close:
            raise _error(
                ErrorCode.PROBABILITY_SUM_INVALID,
                "state probabilities do not match matrix mass",
                "states",
            )


@dataclass(frozen=True, slots=True)
class ExpectedAsianSettlementProfile:
    """Expected fractions of a unit stake under the five-state distribution."""

    won_fraction: float
    pushed_fraction: float
    lost_fraction: float
    total_probability: float
    residual_mass: float

    def __post_init__(self) -> None:
        values = (self.won_fraction, self.pushed_fraction, self.lost_fraction)
        if any(not _finite_non_negative(value, "fraction") for value in values):
            raise _error(
                ErrorCode.INVALID_NUMBER,
                "expected fractions must be finite and non-negative",
                "profile",
            )
        if not _finite_non_negative(self.total_probability, "total_probability"):
            raise _error(
                ErrorCode.INVALID_PROBABILITY,
                "total probability is invalid",
                "total_probability",
            )
        if (
            not isinstance(self.residual_mass, float)
            or not math.isfinite(self.residual_mass)
            or self.residual_mass < -_DEFAULT_POLICY.probability_sum_tolerance
        ):
            raise _error(
                ErrorCode.RESIDUAL_MASS_EXCEEDED,
                "residual mass is invalid",
                "residual_mass",
            )
        total = stable_sum(list(values))
        close = (
            is_close(total, self.total_probability, _DEFAULT_POLICY)
            if not isinstance(total, CalculationError)
            else total
        )
        if isinstance(close, CalculationError) or not close:
            raise _error(
                ErrorCode.PROBABILITY_SUM_INVALID,
                "expected fractions do not match matrix mass",
                "profile",
            )


@dataclass(frozen=True, slots=True)
class AsianMarketPrice:
    """Auditable fair price for one Asian selection and canonical line."""

    market: AsianMarketCode
    selection: HandicapSelection | AsianTotalSelection
    line: QuarterLine
    settlement_probabilities: AsianSettlementProbabilities
    expected_profile: ExpectedAsianSettlementProfile
    fair_odds: FairOdds | None
    error: CalculationError | None
    warnings: tuple[CalculationWarning, ...]
    residual_mass: float

    def __post_init__(self) -> None:
        if not isinstance(self.market, AsianMarketCode):
            raise _error(
                ErrorCode.INVALID_MARKET, "market must be an AsianMarketCode", "market"
            )
        allowed = (
            HandicapSelection
            if self.market is AsianMarketCode.HANDICAP
            else AsianTotalSelection
        )
        if not isinstance(self.selection, allowed):
            raise _error(
                ErrorCode.INVALID_MARKET, "selection is invalid for market", "selection"
            )
        if not isinstance(self.line, QuarterLine):
            raise _error(
                ErrorCode.INVALID_ASIAN_LINE, "line must be a QuarterLine", "line"
            )
        if not isinstance(
            self.settlement_probabilities, AsianSettlementProbabilities
        ) or not isinstance(self.expected_profile, ExpectedAsianSettlementProfile):
            raise _error(
                ErrorCode.INCONSISTENT_DATA,
                "Asian pricing contracts are inconsistent",
                "price",
            )
        if not isinstance(self.warnings, tuple) or any(
            not isinstance(item, CalculationWarning) for item in self.warnings
        ):
            raise _error(
                ErrorCode.CONFIGURATION_ERROR,
                "warnings must be an immutable typed tuple",
                "warnings",
            )
        if (
            not isinstance(self.residual_mass, float)
            or not math.isfinite(self.residual_mass)
            or self.residual_mass < -_DEFAULT_POLICY.probability_sum_tolerance
            or not math.isclose(
                self.residual_mass,
                self.expected_profile.residual_mass,
                abs_tol=_DEFAULT_POLICY.probability_sum_tolerance,
            )
        ):
            raise _error(
                ErrorCode.RESIDUAL_MASS_EXCEEDED,
                "residual mass is inconsistent",
                "residual_mass",
            )
        if (
            self.settlement_probabilities.total_probability
            != self.expected_profile.total_probability
        ):
            raise _error(
                ErrorCode.PROBABILITY_SUM_INVALID,
                "price masses are inconsistent",
                "price",
            )
        if self.expected_profile.won_fraction == 0.0:
            if (
                self.fair_odds is not None
                or self.error is None
                or self.error.code is not ErrorCode.FAIR_ODD_UNDEFINED
            ):
                raise _error(
                    ErrorCode.FAIR_ODD_UNDEFINED,
                    "zero wins require an undefined fair odd",
                    "fair_odds",
                )
        elif self.fair_odds is None or self.error is not None:
            raise _error(
                ErrorCode.INCONSISTENT_DATA,
                "positive wins require fair odds",
                "fair_odds",
            )


@dataclass(frozen=True, slots=True)
class AsianMainLine:
    """Deterministically selected balanced Asian line and both prices."""

    market: AsianMarketCode
    reference_selection: HandicapSelection | AsianTotalSelection
    line: QuarterLine
    reference_price: AsianMarketPrice
    opposite_price: AsianMarketPrice
    balance_value: float
    balance_distance: float
    evaluated_lines: int
    warnings: tuple[CalculationWarning, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.market, AsianMarketCode) or not isinstance(
            self.line, QuarterLine
        ):
            raise _error(
                ErrorCode.INVALID_MARKET, "main line market is invalid", "market"
            )
        expected_selection = (
            HandicapSelection.HOME
            if self.market is AsianMarketCode.HANDICAP
            else AsianTotalSelection.OVER
        )
        if self.reference_selection is not expected_selection:
            raise _error(
                ErrorCode.INVALID_MARKET,
                "reference selection is not canonical",
                "reference_selection",
            )
        if not isinstance(self.reference_price, AsianMarketPrice) or not isinstance(
            self.opposite_price, AsianMarketPrice
        ):
            raise _error(
                ErrorCode.INCONSISTENT_DATA, "main line prices are invalid", "prices"
            )
        if (
            self.reference_price.market is not self.market
            or self.reference_price.line != self.line
        ):
            raise _error(
                ErrorCode.INCONSISTENT_DATA,
                "reference price does not match main line",
                "reference_price",
            )
        expected_opposite = (
            -self.line.quarters
            if self.market is AsianMarketCode.HANDICAP
            else self.line.quarters
        )
        if (
            self.opposite_price.market is not self.market
            or self.opposite_price.line.quarters != expected_opposite
        ):
            raise _error(
                ErrorCode.INCONSISTENT_DATA,
                "opposite price line is invalid",
                "opposite_price",
            )
        if (
            not all(
                _finite_non_negative(value, "value")
                for value in (self.balance_distance,)
            )
            or not isinstance(self.balance_value, float)
            or not math.isfinite(self.balance_value)
        ):
            raise _error(
                ErrorCode.INVALID_NUMBER, "balance values must be finite", "balance"
            )
        if (
            self.balance_distance != abs(self.balance_value)
            or isinstance(self.evaluated_lines, bool)
            or not isinstance(self.evaluated_lines, int)
            or self.evaluated_lines <= 0
        ):
            raise _error(
                ErrorCode.INCONSISTENT_DATA,
                "main line balance is inconsistent",
                "balance",
            )
        if not isinstance(self.warnings, tuple) or any(
            not isinstance(item, CalculationWarning) for item in self.warnings
        ):
            raise _error(
                ErrorCode.CONFIGURATION_ERROR,
                "warnings must be an immutable typed tuple",
                "warnings",
            )
