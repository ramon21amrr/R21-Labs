"""Pure settlement functions for Asian handicap and totals."""

from __future__ import annotations

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.domain import QuarterLine, Weight

from .contracts import (
    AsianLineComponent,
    AsianLineSplit,
    AsianSettlementProfile,
    AsianSettlementResult,
    AsianSettlementState,
    AsianTotalSelection,
    ElementarySettlementState,
    HandicapSelection,
)


def _invalid(
    message: str, field: str, code: ErrorCode = ErrorCode.INVALID_STATISTIC
) -> CalculationError:
    return CalculationError(code, message, field)


def _score(value: object, field: str) -> int | CalculationError:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return _invalid("score must be a non-negative integer", field)
    return value


def split_asian_line(line: object) -> AsianLineSplit | CalculationError:
    """Return the exact canonical component split for ``line``."""
    if not isinstance(line, QuarterLine):
        return _invalid(
            "line must be a QuarterLine", "line", ErrorCode.INVALID_ASIAN_LINE
        )
    values = (
        ((line.quarters, 1.0),)
        if line.quarters % 2 == 0
        else ((line.quarters - 1, 0.5), (line.quarters + 1, 0.5))
    )
    components = tuple(
        AsianLineComponent(QuarterLine(quarters), Weight(fraction))
        for quarters, fraction in values
    )
    return AsianLineSplit(line, components)


def settle_asian_margin(
    observed_margin: object, line: QuarterLine
) -> ElementarySettlementState | CalculationError:
    """Settle a simple line using exact integer arithmetic in quarters."""
    if isinstance(observed_margin, bool) or not isinstance(observed_margin, int):
        return _invalid("observed_margin must be an integer", "observed_margin")
    if not isinstance(line, QuarterLine):
        return _invalid(
            "line must be a QuarterLine", "line", ErrorCode.INVALID_ASIAN_LINE
        )
    if line.quarters % 2 != 0:
        return _invalid(
            "elementary line must have an even number of quarters",
            "line",
            ErrorCode.INVALID_ASIAN_LINE,
        )
    adjusted_quarters = observed_margin * 4 + line.quarters
    if adjusted_quarters > 0:
        return ElementarySettlementState.WIN
    if adjusted_quarters == 0:
        return ElementarySettlementState.PUSH
    return ElementarySettlementState.LOSS


def _combine(
    results: tuple[ElementarySettlementState, ...],
) -> AsianSettlementState | CalculationError:
    if len(results) == 1:
        single_mapping = {
            ElementarySettlementState.WIN: AsianSettlementState.WIN,
            ElementarySettlementState.PUSH: AsianSettlementState.PUSH,
            ElementarySettlementState.LOSS: AsianSettlementState.LOSS,
        }
        return single_mapping[results[0]]
    if len(results) != 2 or any(
        not isinstance(item, ElementarySettlementState) for item in results
    ):
        return _invalid(
            "component results must contain one or two states",
            "component_results",
            ErrorCode.INCONSISTENT_DATA,
        )
    pair = frozenset(results)
    mapping: dict[frozenset[ElementarySettlementState], AsianSettlementState] = {
        frozenset((ElementarySettlementState.WIN,)): AsianSettlementState.WIN,
        frozenset((ElementarySettlementState.PUSH,)): AsianSettlementState.PUSH,
        frozenset((ElementarySettlementState.LOSS,)): AsianSettlementState.LOSS,
        frozenset(
            (ElementarySettlementState.WIN, ElementarySettlementState.PUSH)
        ): AsianSettlementState.HALF_WIN,
        frozenset(
            (ElementarySettlementState.PUSH, ElementarySettlementState.LOSS)
        ): AsianSettlementState.HALF_LOSS,
    }
    state = mapping.get(pair)
    if state is None:
        return _invalid(
            "component combination is impossible",
            "component_results",
            ErrorCode.INCONSISTENT_DATA,
        )
    return state


def _settle(
    base_quarters: int, line: QuarterLine, line_sign: int = 1
) -> AsianSettlementResult | CalculationError:
    split = split_asian_line(line)
    if isinstance(split, CalculationError):
        return split
    results = tuple(
        ElementarySettlementState.WIN
        if base_quarters + line_sign * component.line.quarters > 0
        else ElementarySettlementState.PUSH
        if base_quarters + line_sign * component.line.quarters == 0
        else ElementarySettlementState.LOSS
        for component in split.components
    )
    state = _combine(results)
    if isinstance(state, CalculationError):
        return state
    return AsianSettlementResult(
        line, split.components, results, state, AsianSettlementProfile.for_state(state)
    )


def settle_asian_handicap(
    home_goals: object,
    away_goals: object,
    line: object,
    selection: object,
) -> AsianSettlementResult | CalculationError:
    """Settle a HOME or AWAY Asian handicap from a realised score."""
    home = _score(home_goals, "home_goals")
    away = _score(away_goals, "away_goals")
    if isinstance(home, CalculationError):
        return home
    if isinstance(away, CalculationError):
        return away
    if not isinstance(line, QuarterLine):
        return _invalid(
            "line must be a QuarterLine", "line", ErrorCode.INVALID_ASIAN_LINE
        )
    if not isinstance(selection, HandicapSelection):
        return _invalid(
            "selection must be a HandicapSelection",
            "selection",
            ErrorCode.INVALID_MARKET,
        )
    margin = home - away if selection is HandicapSelection.HOME else away - home
    return _settle(margin * 4, line)


def settle_asian_total(
    home_goals: object,
    away_goals: object,
    line: object,
    selection: object,
) -> AsianSettlementResult | CalculationError:
    """Settle an OVER or UNDER Asian total from a realised score."""
    home = _score(home_goals, "home_goals")
    away = _score(away_goals, "away_goals")
    if isinstance(home, CalculationError):
        return home
    if isinstance(away, CalculationError):
        return away
    if not isinstance(line, QuarterLine):
        return _invalid(
            "line must be a QuarterLine", "line", ErrorCode.INVALID_ASIAN_LINE
        )
    if not isinstance(selection, AsianTotalSelection):
        return _invalid(
            "selection must be an AsianTotalSelection",
            "selection",
            ErrorCode.INVALID_MARKET,
        )
    total = home + away
    if selection is AsianTotalSelection.OVER:
        return _settle(total * 4, line, -1)
    return _settle(-total * 4, line)
