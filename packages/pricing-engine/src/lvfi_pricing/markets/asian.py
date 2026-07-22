"""Pure probabilistic pricing of Asian handicaps and totals."""

from __future__ import annotations

from collections.abc import Callable

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy, stable_sum
from lvfi_pricing.distributions import ScoreProbabilityMatrix
from lvfi_pricing.domain import FairOdds, Probability, QuarterLine
from lvfi_pricing.settlement import (
    AsianSettlementResult,
    AsianSettlementState,
    AsianTotalSelection,
    HandicapSelection,
    settle_asian_handicap,
    settle_asian_total,
)

from .asian_contracts import (
    AsianMarketCode,
    AsianMarketPrice,
    AsianSettlementProbabilities,
    ExpectedAsianSettlementProfile,
)

_DEFAULT_POLICY = NumericPolicy()


def _error(code: ErrorCode, message: str, field: str) -> CalculationError:
    return CalculationError(code, message, field)


def _policy(value: NumericPolicy | None) -> NumericPolicy | CalculationError:
    return (
        _DEFAULT_POLICY
        if value is None
        else value
        if isinstance(value, NumericPolicy)
        else _error(
            ErrorCode.CONFIGURATION_ERROR,
            "policy must be a NumericPolicy or None",
            "policy",
        )
    )


def _price(
    matrix: object,
    selection: object,
    line: object,
    market: AsianMarketCode,
    settle: Callable[..., AsianSettlementResult | CalculationError],
    policy: NumericPolicy | None,
) -> AsianMarketPrice | CalculationError:
    active_policy = _policy(policy)
    if isinstance(active_policy, CalculationError):
        return active_policy
    if not isinstance(matrix, ScoreProbabilityMatrix):
        return _error(
            ErrorCode.CONFIGURATION_ERROR,
            "matrix must be a ScoreProbabilityMatrix",
            "matrix",
        )
    expected_selection = (
        HandicapSelection if market is AsianMarketCode.HANDICAP else AsianTotalSelection
    )
    if not isinstance(selection, expected_selection):
        return _error(
            ErrorCode.INVALID_MARKET, "selection is invalid for market", "selection"
        )
    if not isinstance(line, QuarterLine):
        return _error(
            ErrorCode.INVALID_ASIAN_LINE, "line must be a QuarterLine", "line"
        )
    buckets: dict[AsianSettlementState, list[float]] = {
        state: [] for state in AsianSettlementState
    }
    for home_goals, row in enumerate(matrix.probabilities):
        for away_goals, probability in enumerate(row):
            settlement = settle(home_goals, away_goals, line, selection)
            if isinstance(settlement, CalculationError):
                return settlement
            state = settlement.state
            buckets[state].append(probability)
    values: list[float] = []
    for state in AsianSettlementState:
        total = stable_sum(buckets[state])
        if isinstance(total, CalculationError):
            return _error(
                ErrorCode.PROBABILITY_SUM_INVALID,
                "state probability sum is invalid",
                "states",
            )
        values.append(total)
    typed = [Probability(value) for value in values]
    settlement_probabilities = AsianSettlementProbabilities(
        typed[0],
        typed[1],
        typed[2],
        typed[3],
        typed[4],
        matrix.total_probability,
        matrix.residual_mass,
    )
    won = values[0] + 0.5 * values[1]
    pushed = values[2] + 0.5 * values[1] + 0.5 * values[3]
    lost = values[4] + 0.5 * values[3]
    profile = ExpectedAsianSettlementProfile(
        won, pushed, lost, matrix.total_probability, matrix.residual_mass
    )
    if won == 0.0:
        error = _error(
            ErrorCode.FAIR_ODD_UNDEFINED,
            "fair odds are undefined for zero expected won fraction",
            "fair_odds",
        )
        return AsianMarketPrice(
            market,
            selection,
            line,
            settlement_probabilities,
            profile,
            None,
            error,
            matrix.warnings,
            matrix.residual_mass,
        )
    odds = FairOdds(1.0 + lost / won)
    return AsianMarketPrice(
        market,
        selection,
        line,
        settlement_probabilities,
        profile,
        odds,
        None,
        matrix.warnings,
        matrix.residual_mass,
    )


def price_asian_handicap(
    matrix: ScoreProbabilityMatrix,
    selection: HandicapSelection,
    line: QuarterLine,
    policy: NumericPolicy | None = None,
) -> AsianMarketPrice | CalculationError:
    """Price a HOME or AWAY Asian handicap from each matrix cell exactly once."""
    return _price(
        matrix, selection, line, AsianMarketCode.HANDICAP, settle_asian_handicap, policy
    )


def price_asian_total(
    matrix: ScoreProbabilityMatrix,
    selection: AsianTotalSelection,
    line: QuarterLine,
    policy: NumericPolicy | None = None,
) -> AsianMarketPrice | CalculationError:
    """Price an OVER or UNDER Asian total from each matrix cell exactly once."""
    return _price(
        matrix, selection, line, AsianMarketCode.TOTAL, settle_asian_total, policy
    )
