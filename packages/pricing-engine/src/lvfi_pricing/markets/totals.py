"""Totais simples de gols em linhas de meia unidade aprovadas."""

from __future__ import annotations

from dataclasses import dataclass

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy, stable_sum
from lvfi_pricing.distributions import ScoreProbabilityMatrix

from .basic import _market
from .contracts import MarketCode, MarketPrices, TotalSelection

_DEFAULT_POLICY = NumericPolicy()


@dataclass(frozen=True, slots=True)
class HalfGoalLine:
    """Linha simples de gols, armazenada em unidades de meia-gol."""

    half_units: int

    @classmethod
    def create(cls, value: object) -> HalfGoalLine | CalculationError:
        if isinstance(value, bool) or not isinstance(value, int):
            return CalculationError(
                ErrorCode.INVALID_NUMBER,
                "half-goal line must be an integer",
                "line",
            )
        if value not in (1, 3, 5, 7, 9, 11):
            return CalculationError(
                ErrorCode.INVALID_MARKET,
                "line is outside the T08 total catalog",
                "line",
            )
        return cls(value)

    @property
    def decimal_value(self) -> float:
        return self.half_units / 2.0


def price_total_goals(
    matrix: ScoreProbabilityMatrix,
    line: HalfGoalLine,
    policy: NumericPolicy = _DEFAULT_POLICY,
) -> MarketPrices | CalculationError:
    if not isinstance(matrix, ScoreProbabilityMatrix):
        return CalculationError(
            ErrorCode.CONFIGURATION_ERROR,
            "matrix must be a ScoreProbabilityMatrix",
            "matrix",
        )
    if not isinstance(line, HalfGoalLine):
        return CalculationError(
            ErrorCode.INVALID_MARKET, "line must be a HalfGoalLine", "line"
        )
    if not isinstance(policy, NumericPolicy):
        return CalculationError(
            ErrorCode.CONFIGURATION_ERROR,
            "policy must be a NumericPolicy",
            "policy",
        )
    under = stable_sum(
        [
            matrix.probabilities[home][away]
            for home in range(matrix.home_max_goals + 1)
            for away in range(matrix.away_max_goals + 1)
            if 2 * (home + away) < line.half_units
        ]
    )
    over = stable_sum(
        [
            matrix.probabilities[home][away]
            for home in range(matrix.home_max_goals + 1)
            for away in range(matrix.away_max_goals + 1)
            if 2 * (home + away) > line.half_units
        ]
    )
    if isinstance(under, CalculationError) or isinstance(over, CalculationError):
        return CalculationError(
            ErrorCode.PROBABILITY_SUM_INVALID, "total sum is invalid"
        )
    return _market(
        MarketCode.TOTAL_GOALS,
        ((TotalSelection.OVER, over), (TotalSelection.UNDER, under)),
        matrix.total_probability,
        matrix.residual_mass,
        matrix.warnings,
        policy,
    )
