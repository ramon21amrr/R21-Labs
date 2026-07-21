"""Properties for exact Asian-line settlement."""

from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.domain import QuarterLine
from lvfi_pricing.settlement import (
    AsianSettlementState,
    AsianTotalSelection,
    HandicapSelection,
    settle_asian_handicap,
    settle_asian_total,
    split_asian_line,
)


@given(st.integers(-10_000, 10_000))
def test_split_preserves_exact_quarter_structure(quarters: int) -> None:
    line = QuarterLine(quarters)
    split = split_asian_line(line)
    assert not isinstance(split, Exception)
    assert sum(component.stake_fraction.value for component in split.components) == 1.0
    if quarters % 2 == 0:
        assert len(split.components) == 1
    else:
        lower, upper = split.components
        assert (lower.line.quarters, upper.line.quarters) == (
            quarters - 1,
            quarters + 1,
        )


@given(st.integers(0, 20), st.integers(0, 20), st.integers(-20, 20))
def test_handicap_symmetry_and_states(home: int, away: int, quarters: int) -> None:
    home_result = settle_asian_handicap(
        home, away, QuarterLine(quarters), HandicapSelection.HOME
    )
    away_result = settle_asian_handicap(
        away, home, QuarterLine(quarters), HandicapSelection.AWAY
    )
    assert not isinstance(home_result, Exception)
    assert home_result == away_result
    assert home_result.state in AsianSettlementState


@given(st.integers(0, 20), st.integers(0, 20), st.integers(-20, 20))
def test_total_is_deterministic(home: int, away: int, quarters: int) -> None:
    first = settle_asian_total(
        home, away, QuarterLine(quarters), AsianTotalSelection.OVER
    )
    second = settle_asian_total(
        home, away, QuarterLine(quarters), AsianTotalSelection.OVER
    )
    assert first == second
