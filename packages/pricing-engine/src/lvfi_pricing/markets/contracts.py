"""Contratos imutáveis para mercados básicos e seus preços justos."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy, stable_sum
from lvfi_pricing.domain import FairOdds, Probability

_DEFAULT_POLICY = NumericPolicy()


class MarketCode(StrEnum):
    THREE_WAY_RESULT = "three_way_result"
    DOUBLE_CHANCE = "double_chance"
    BOTH_TEAMS_TO_SCORE = "both_teams_to_score"
    TOTAL_GOALS = "total_goals"


class ThreeWaySelection(StrEnum):
    HOME = "home"
    DRAW = "draw"
    AWAY = "away"


class DoubleChanceSelection(StrEnum):
    HOME_OR_DRAW = "home_or_draw"
    HOME_OR_AWAY = "home_or_away"
    DRAW_OR_AWAY = "draw_or_away"


class BttsSelection(StrEnum):
    YES = "yes"
    NO = "no"


class TotalSelection(StrEnum):
    OVER = "over"
    UNDER = "under"


@dataclass(frozen=True, slots=True)
class PricedSelection:
    selection: (
        ThreeWaySelection | DoubleChanceSelection | BttsSelection | TotalSelection
    )
    probability: Probability
    fair_odds: FairOdds | None
    error: CalculationError | None = None
    warnings: tuple[CalculationWarning, ...] = ()

    @classmethod
    def create(
        cls,
        selection: object,
        probability: object,
        warnings: tuple[CalculationWarning, ...] = (),
    ) -> PricedSelection | CalculationError:
        if not isinstance(
            selection,
            (ThreeWaySelection, DoubleChanceSelection, BttsSelection, TotalSelection),
        ):
            return CalculationError(
                ErrorCode.INVALID_MARKET, "invalid market selection", "selection"
            )
        if not isinstance(probability, Probability):
            return CalculationError(
                ErrorCode.INVALID_PROBABILITY,
                "probability must be a Probability",
                "probability",
            )
        if not isinstance(warnings, tuple) or any(
            not isinstance(warning, CalculationWarning) for warning in warnings
        ):
            return CalculationError(
                ErrorCode.CONFIGURATION_ERROR,
                "warnings must be typed and immutable",
                "warnings",
            )
        odds = FairOdds.from_probability(probability)
        if probability.value == 0.0:
            assert isinstance(odds, CalculationError)
            return cls(selection, probability, None, odds, warnings)
        if isinstance(odds, CalculationError):
            return odds
        return cls(selection, probability, odds, None, warnings)


@dataclass(frozen=True, slots=True)
class MarketPrices:
    market: MarketCode
    selections: tuple[PricedSelection, ...]
    total_probability: float
    residual_mass: float
    warnings: tuple[CalculationWarning, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.market, MarketCode) or not isinstance(
            self.selections, tuple
        ):
            raise CalculationError(
                ErrorCode.CONFIGURATION_ERROR, "market contract is inconsistent"
            )
        if any(
            not isinstance(selection, PricedSelection) for selection in self.selections
        ):
            raise CalculationError(
                ErrorCode.CONFIGURATION_ERROR, "selections must be typed"
            )
        if not math.isfinite(self.total_probability) or not math.isfinite(
            self.residual_mass
        ):
            raise CalculationError(
                ErrorCode.INVALID_NUMBER, "market mass must be finite"
            )
        if (
            self.total_probability < 0.0
            or self.total_probability > 1.0 + _DEFAULT_POLICY.probability_sum_tolerance
        ):
            raise CalculationError(
                ErrorCode.INVALID_PROBABILITY, "market mass is outside [0, 1]"
            )
        if self.residual_mass < -_DEFAULT_POLICY.probability_sum_tolerance:
            raise CalculationError(
                ErrorCode.RESIDUAL_MASS_EXCEEDED, "residual mass is invalid"
            )
        if not isinstance(self.warnings, tuple) or any(
            not isinstance(warning, CalculationWarning) for warning in self.warnings
        ):
            raise CalculationError(
                ErrorCode.CONFIGURATION_ERROR, "warnings must be typed and immutable"
            )
        total = stable_sum(
            [selection.probability.value for selection in self.selections]
        )
        expected = self.total_probability * (
            2.0 if self.market is MarketCode.DOUBLE_CHANCE else 1.0
        )
        if isinstance(total, CalculationError) or not math.isclose(
            total, expected, abs_tol=_DEFAULT_POLICY.probability_sum_tolerance
        ):
            raise CalculationError(
                ErrorCode.PROBABILITY_SUM_INVALID, "market selections are inconsistent"
            )
