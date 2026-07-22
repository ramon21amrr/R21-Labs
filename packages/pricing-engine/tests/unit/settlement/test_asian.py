"""Tests for deterministic Asian settlement."""

from collections.abc import Callable
from dataclasses import FrozenInstanceError

import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.domain import QuarterLine, Weight
from lvfi_pricing.settlement import (
    AsianLineComponent,
    AsianSettlementProfile,
    AsianSettlementResult,
    AsianSettlementState,
    AsianTotalSelection,
    ElementarySettlementState,
    HandicapSelection,
    settle_asian_handicap,
    settle_asian_margin,
    settle_asian_total,
    split_asian_line,
)
from lvfi_pricing.settlement import asian as asian_module


def line(quarters: int) -> QuarterLine:
    return QuarterLine(quarters)


def invoke(factory: Callable[..., object], *args: object) -> object:
    return factory(*args)


@pytest.mark.parametrize(
    ("quarters", "expected"),
    [
        (0, (0,)),
        (1, (0, 2)),
        (-1, (-2, 0)),
        (2, (2,)),
        (-2, (-2,)),
        (3, (2, 4)),
        (-3, (-4, -2)),
        (5, (4, 6)),
        (-5, (-6, -4)),
        (101, (100, 102)),
        (-101, (-102, -100)),
    ],
)
def test_canonical_split(quarters: int, expected: tuple[int, ...]) -> None:
    result = split_asian_line(line(quarters))
    assert not isinstance(result, CalculationError)
    assert tuple(item.line.quarters for item in result.components) == expected
    assert sum(item.stake_fraction.value for item in result.components) == 1.0
    assert result == split_asian_line(line(quarters))


@pytest.mark.parametrize("value", [True, 1, 1.0, "1", object()])
def test_invalid_lines_are_rejected(value: object) -> None:
    result = split_asian_line(value)
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.INVALID_ASIAN_LINE


def test_profiles_enums_and_immutability() -> None:
    assert tuple(state.value for state in AsianSettlementState) == (
        "win",
        "half_win",
        "push",
        "half_loss",
        "loss",
    )
    assert str(HandicapSelection.HOME) == "home"
    assert str(AsianTotalSelection.UNDER) == "under"
    for state in AsianSettlementState:
        profile = AsianSettlementProfile.for_state(state)
        assert (
            sum(
                (
                    profile.won_fraction.value,
                    profile.pushed_fraction.value,
                    profile.lost_fraction.value,
                )
            )
            == 1.0
        )
    component = AsianLineComponent(line(0), Weight(1.0))
    with pytest.raises(FrozenInstanceError):
        component.__setattr__("line", line(2))


@pytest.mark.parametrize(
    ("margin", "quarters", "state"),
    [
        (1, 0, ElementarySettlementState.WIN),
        (0, 0, ElementarySettlementState.PUSH),
        (-1, 0, ElementarySettlementState.LOSS),
    ],
)
def test_elementary_settlement(
    margin: int, quarters: int, state: ElementarySettlementState
) -> None:
    assert settle_asian_margin(margin, line(quarters)) is state
    assert isinstance(settle_asian_margin(True, line(0)), CalculationError)
    assert isinstance(settle_asian_margin(0, line(1)), CalculationError)


@pytest.mark.parametrize(
    ("home", "away", "quarters", "selection", "state"),
    [
        (1, 0, 0, HandicapSelection.HOME, AsianSettlementState.WIN),
        (1, 1, 0, HandicapSelection.HOME, AsianSettlementState.PUSH),
        (0, 1, 0, HandicapSelection.HOME, AsianSettlementState.LOSS),
        (1, 1, -1, HandicapSelection.HOME, AsianSettlementState.HALF_LOSS),
        (1, 1, 1, HandicapSelection.HOME, AsianSettlementState.HALF_WIN),
        (2, 1, -3, HandicapSelection.HOME, AsianSettlementState.HALF_WIN),
        (0, 1, 3, HandicapSelection.HOME, AsianSettlementState.HALF_LOSS),
        (0, 1, 0, HandicapSelection.AWAY, AsianSettlementState.WIN),
    ],
)
def test_handicap(
    home: int,
    away: int,
    quarters: int,
    selection: HandicapSelection,
    state: AsianSettlementState,
) -> None:
    result = settle_asian_handicap(home, away, line(quarters), selection)
    assert isinstance(result, AsianSettlementResult)
    assert result.state is state


@pytest.mark.parametrize(
    ("home", "away", "quarters", "selection", "state"),
    [
        (2, 1, 8, AsianTotalSelection.OVER, AsianSettlementState.WIN),
        (1, 1, 8, AsianTotalSelection.OVER, AsianSettlementState.PUSH),
        (1, 0, 8, AsianTotalSelection.OVER, AsianSettlementState.LOSS),
        (1, 1, 9, AsianTotalSelection.OVER, AsianSettlementState.HALF_LOSS),
        (1, 0, 9, AsianTotalSelection.UNDER, AsianSettlementState.WIN),
        (1, 1, 9, AsianTotalSelection.UNDER, AsianSettlementState.HALF_WIN),
        (2, 1, 11, AsianTotalSelection.OVER, AsianSettlementState.HALF_WIN),
        (2, 1, 11, AsianTotalSelection.UNDER, AsianSettlementState.HALF_LOSS),
    ],
)
def test_totals(
    home: int,
    away: int,
    quarters: int,
    selection: AsianTotalSelection,
    state: AsianSettlementState,
) -> None:
    result = settle_asian_total(home, away, line(quarters), selection)
    assert isinstance(result, AsianSettlementResult)
    assert result.state is state


@pytest.mark.parametrize("bad", [-1, True, 1.0, "1"])
def test_validation_and_impossible_combination(bad: object) -> None:
    assert isinstance(
        settle_asian_handicap(bad, 0, line(0), HandicapSelection.HOME), CalculationError
    )
    assert isinstance(
        settle_asian_total(0, bad, line(0), AsianTotalSelection.OVER), CalculationError
    )
    assert isinstance(
        settle_asian_handicap(0, bad, line(0), HandicapSelection.HOME),
        CalculationError,
    )
    assert isinstance(
        settle_asian_total(bad, 0, line(0), AsianTotalSelection.OVER),
        CalculationError,
    )
    assert isinstance(
        settle_asian_handicap(0, 0, object(), HandicapSelection.HOME), CalculationError
    )
    assert isinstance(settle_asian_total(0, 0, line(0), object()), CalculationError)
    assert isinstance(settle_asian_handicap(0, 0, line(0), object()), CalculationError)
    assert isinstance(
        settle_asian_total(0, 0, object(), AsianTotalSelection.OVER), CalculationError
    )
    assert isinstance(invoke(settle_asian_margin, 0, object()), CalculationError)
    result = asian_module._combine(
        (ElementarySettlementState.WIN, ElementarySettlementState.LOSS)
    )
    assert isinstance(result, CalculationError)


def test_contract_rejections_and_internal_error_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert AsianLineComponent(line(0), Weight(1.0)).line == line(0)
    split = split_asian_line(line(0))
    assert not isinstance(split, CalculationError)
    profile = AsianSettlementProfile.for_state(AsianSettlementState.PUSH)
    with pytest.raises(CalculationError):
        invoke(AsianLineComponent, object(), Weight(1.0))
    with pytest.raises(CalculationError):
        AsianLineComponent(line(1), Weight(1.0))
    with pytest.raises(CalculationError):
        invoke(AsianLineComponent, line(0), object())
    with pytest.raises(CalculationError):
        invoke(type(split), object(), split.components)
    with pytest.raises(CalculationError):
        type(split)(line(0), ())
    with pytest.raises(CalculationError):
        invoke(type(split), line(0), (object(),))
    with pytest.raises(CalculationError):
        type(split)(line(0), (AsianLineComponent(line(2), Weight(1.0)),))
    with pytest.raises(CalculationError):
        invoke(AsianSettlementProfile, object(), Weight(0.0), Weight(0.0))
    with pytest.raises(CalculationError):
        AsianSettlementProfile(Weight(0.5), Weight(0.0), Weight(0.0))
    with pytest.raises(CalculationError):
        invoke(
            AsianSettlementResult,
            object(),
            split.components,
            (ElementarySettlementState.PUSH,),
            AsianSettlementState.PUSH,
            profile,
        )
    with pytest.raises(CalculationError):
        AsianSettlementResult(line(0), (), (), AsianSettlementState.PUSH, profile)
    with pytest.raises(CalculationError):
        AsianSettlementResult(
            line(0), split.components, (), AsianSettlementState.PUSH, profile
        )
    with pytest.raises(CalculationError):
        invoke(
            AsianSettlementResult,
            line(0),
            split.components,
            (ElementarySettlementState.PUSH,),
            object(),
            profile,
        )
    with pytest.raises(CalculationError):
        invoke(
            AsianSettlementResult,
            line(0),
            split.components,
            (ElementarySettlementState.PUSH,),
            AsianSettlementState.PUSH,
            object(),
        )
    with pytest.raises(CalculationError):
        AsianSettlementResult(
            line(0),
            split.components,
            (ElementarySettlementState.PUSH,),
            AsianSettlementState.PUSH,
            AsianSettlementProfile.for_state(AsianSettlementState.WIN),
        )
    with pytest.raises(CalculationError):
        AsianSettlementResult(
            line(0),
            split.components,
            (ElementarySettlementState.PUSH,),
            AsianSettlementState.WIN,
            AsianSettlementProfile.for_state(AsianSettlementState.WIN),
        )
    assert isinstance(
        asian_module._combine(
            (),
        ),
        CalculationError,
    )
    assert (
        asian_module._combine((ElementarySettlementState.WIN,))
        is AsianSettlementState.WIN
    )
    assert (
        asian_module._combine(
            (ElementarySettlementState.PUSH, ElementarySettlementState.WIN)
        )
        is AsianSettlementState.HALF_WIN
    )
    assert (
        asian_module._combine(
            (ElementarySettlementState.PUSH, ElementarySettlementState.LOSS)
        )
        is AsianSettlementState.HALF_LOSS
    )
    assert isinstance(invoke(asian_module._settle, 0, object()), CalculationError)
    monkeypatch.setattr(
        asian_module,
        "_combine",
        lambda _: CalculationError(ErrorCode.INCONSISTENT_DATA, "bad"),
    )
    assert isinstance(asian_module._settle(0, line(0)), CalculationError)
    with pytest.raises(CalculationError):
        asian_module._settle_asian_state(0, 0)


def test_internal_state_path_matches_complete_settlement_over_supported_domain() -> (
    None
):
    for margin in range(-42, 43):
        home, away = max(margin, 0), max(-margin, 0)
        for quarters in range(-172, 173):
            source_line = line(quarters)
            for handicap_selection in HandicapSelection:
                complete = settle_asian_handicap(
                    home, away, source_line, handicap_selection
                )
                assert isinstance(complete, AsianSettlementResult)
                assert (
                    asian_module._settle_asian_handicap_state(
                        home, away, source_line, handicap_selection
                    )
                    is complete.state
                )
    for total in range(85):
        for quarters in range(341):
            source_line = line(quarters)
            for total_selection in AsianTotalSelection:
                complete = settle_asian_total(total, 0, source_line, total_selection)
                assert isinstance(complete, AsianSettlementResult)
                assert (
                    asian_module._settle_asian_total_state(
                        total, 0, source_line, total_selection
                    )
                    is complete.state
                )
