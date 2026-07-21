"""Deterministic candidate catalogues and Asian main-line selection."""

from __future__ import annotations

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy, is_close
from lvfi_pricing.distributions import ScoreProbabilityMatrix
from lvfi_pricing.domain import QuarterLine
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection

from .asian import price_asian_handicap, price_asian_total
from .asian_contracts import AsianMainLine, AsianMarketCode, AsianMarketPrice

_DEFAULT_POLICY = NumericPolicy()


def _error(code: ErrorCode, message: str, field: str) -> CalculationError:
    return CalculationError(code, message, field)


def _valid_matrix(matrix: object) -> ScoreProbabilityMatrix | CalculationError:
    if not isinstance(matrix, ScoreProbabilityMatrix):
        return _error(
            ErrorCode.CONFIGURATION_ERROR,
            "matrix must be a ScoreProbabilityMatrix",
            "matrix",
        )
    return matrix


def generate_asian_handicap_candidates(
    matrix: ScoreProbabilityMatrix,
    selection: HandicapSelection = HandicapSelection.HOME,
) -> tuple[QuarterLine, ...] | CalculationError:
    """Generate all quarter lines around the observable margin support."""
    source = _valid_matrix(matrix)
    if isinstance(source, CalculationError):
        return source
    if not isinstance(selection, HandicapSelection):
        return _error(
            ErrorCode.INVALID_MARKET,
            "selection must be a HandicapSelection",
            "selection",
        )
    own, other = (
        (source.home_max_goals, source.away_max_goals)
        if selection is HandicapSelection.HOME
        else (source.away_max_goals, source.home_max_goals)
    )
    return tuple(
        QuarterLine(value) for value in range(-(own + 1) * 4, (other + 1) * 4 + 1)
    )


def generate_asian_total_candidates(
    matrix: ScoreProbabilityMatrix,
) -> tuple[QuarterLine, ...] | CalculationError:
    """Generate non-negative quarter totals through one goal beyond support."""
    source = _valid_matrix(matrix)
    if isinstance(source, CalculationError):
        return source
    return tuple(
        QuarterLine(value)
        for value in range((source.home_max_goals + source.away_max_goals + 1) * 4 + 1)
    )


def _catalogue(value: object) -> tuple[QuarterLine, ...] | CalculationError:
    if not isinstance(value, tuple) or not value:
        return _error(
            ErrorCode.CONFIGURATION_ERROR,
            "candidate lines must be a non-empty tuple",
            "candidates",
        )
    if any(not isinstance(line, QuarterLine) for line in value):
        return _error(
            ErrorCode.INVALID_ASIAN_LINE,
            "candidates must contain QuarterLine values",
            "candidates",
        )
    quarters = tuple(line.quarters for line in value)
    if quarters != tuple(sorted(quarters)) or len(set(quarters)) != len(quarters):
        return _error(
            ErrorCode.INCONSISTENT_DATA,
            "candidates must be ordered and unique",
            "candidates",
        )
    return value


def _select(
    matrix: ScoreProbabilityMatrix,
    market: AsianMarketCode,
    candidates: tuple[QuarterLine, ...] | None,
    policy: NumericPolicy | None,
) -> AsianMainLine | CalculationError:
    active_policy = _DEFAULT_POLICY if policy is None else policy
    if not isinstance(active_policy, NumericPolicy):
        return _error(
            ErrorCode.CONFIGURATION_ERROR,
            "policy must be a NumericPolicy or None",
            "policy",
        )
    generated = (
        generate_asian_handicap_candidates(matrix)
        if market is AsianMarketCode.HANDICAP
        else generate_asian_total_candidates(matrix)
    )
    lines = generated if candidates is None else _catalogue(candidates)
    if isinstance(lines, CalculationError):
        return lines
    best_line: QuarterLine | None = None
    best_price: AsianMarketPrice | None = None
    best_value = 0.0
    best_distance = 0.0
    for line in lines:
        price = (
            price_asian_handicap(matrix, HandicapSelection.HOME, line, active_policy)
            if market is AsianMarketCode.HANDICAP
            else price_asian_total(
                matrix, AsianTotalSelection.OVER, line, active_policy
            )
        )
        if isinstance(price, CalculationError):
            return price
        value = (
            2.0 * price.expected_profile.won_fraction
            + price.expected_profile.pushed_fraction
            - 1.0
        )
        distance = abs(value)
        if best_line is None:
            best_line, best_price, best_value, best_distance = (
                line,
                price,
                value,
                distance,
            )
            continue
        close = is_close(distance, best_distance, active_policy)
        if isinstance(close, CalculationError):
            return close
        if (
            distance < best_distance
            and not close
            or close
            and (abs(line.quarters), line.quarters)
            < (abs(best_line.quarters), best_line.quarters)
        ):
            best_line, best_price, best_value, best_distance = (
                line,
                price,
                value,
                distance,
            )
    assert best_line is not None and best_price is not None
    opposite_line = (
        QuarterLine(-best_line.quarters)
        if market is AsianMarketCode.HANDICAP
        else best_line
    )
    opposite = (
        price_asian_handicap(
            matrix, HandicapSelection.AWAY, opposite_line, active_policy
        )
        if market is AsianMarketCode.HANDICAP
        else price_asian_total(
            matrix, AsianTotalSelection.UNDER, opposite_line, active_policy
        )
    )
    if isinstance(opposite, CalculationError):
        return opposite
    reference = (
        HandicapSelection.HOME
        if market is AsianMarketCode.HANDICAP
        else AsianTotalSelection.OVER
    )
    return AsianMainLine(
        market,
        reference,
        best_line,
        best_price,
        opposite,
        best_value,
        best_distance,
        len(lines),
        best_price.warnings,
    )


def select_asian_handicap_main_line(
    matrix: ScoreProbabilityMatrix,
    candidates: tuple[QuarterLine, ...] | None = None,
    policy: NumericPolicy | None = None,
) -> AsianMainLine | CalculationError:
    """Select the HOME-referenced balanced Asian handicap line."""
    return _select(matrix, AsianMarketCode.HANDICAP, candidates, policy)


def select_asian_total_main_line(
    matrix: ScoreProbabilityMatrix,
    candidates: tuple[QuarterLine, ...] | None = None,
    policy: NumericPolicy | None = None,
) -> AsianMainLine | CalculationError:
    """Select the OVER-referenced balanced Asian total line."""
    return _select(matrix, AsianMarketCode.TOTAL, candidates, policy)
