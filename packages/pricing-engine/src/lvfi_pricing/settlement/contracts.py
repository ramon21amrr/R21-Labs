"""Immutable contracts for deterministic Asian-line settlement."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.domain import QuarterLine, Weight


class AsianSettlementState(StrEnum):
    """The five possible final settlement states."""

    WIN = "win"
    HALF_WIN = "half_win"
    PUSH = "push"
    HALF_LOSS = "half_loss"
    LOSS = "loss"


class ElementarySettlementState(StrEnum):
    """Settlement state of one non-quarter Asian component."""

    WIN = "win"
    PUSH = "push"
    LOSS = "loss"


class HandicapSelection(StrEnum):
    HOME = "home"
    AWAY = "away"


class AsianTotalSelection(StrEnum):
    OVER = "over"
    UNDER = "under"


def _error(message: str, field: str) -> CalculationError:
    return CalculationError(ErrorCode.INCONSISTENT_DATA, message, field)


@dataclass(frozen=True, slots=True)
class AsianLineComponent:
    """One simple line and its conceptual fraction of stake."""

    line: QuarterLine
    stake_fraction: Weight

    def __post_init__(self) -> None:
        if not isinstance(self.line, QuarterLine):
            raise _error("line must be a QuarterLine", "line")
        if self.line.quarters % 2 != 0:
            raise _error("component line must have an even number of quarters", "line")
        if not isinstance(self.stake_fraction, Weight):
            raise _error("stake_fraction must be a Weight", "stake_fraction")


@dataclass(frozen=True, slots=True)
class AsianLineSplit:
    """Canonical decomposition of an Asian line into one or two components."""

    source_line: QuarterLine
    components: tuple[AsianLineComponent, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_line, QuarterLine):
            raise _error("source_line must be a QuarterLine", "source_line")
        if not isinstance(self.components, tuple) or not self.components:
            raise _error("components must be a non-empty tuple", "components")
        if any(not isinstance(item, AsianLineComponent) for item in self.components):
            raise _error("components must be AsianLineComponent values", "components")
        expected = (
            ((self.source_line.quarters, 1.0),)
            if self.source_line.quarters % 2 == 0
            else (
                (self.source_line.quarters - 1, 0.5),
                (self.source_line.quarters + 1, 0.5),
            )
        )
        actual = tuple(
            (item.line.quarters, item.stake_fraction.value) for item in self.components
        )
        if actual != expected:
            raise _error("components are not the canonical line split", "components")


@dataclass(frozen=True, slots=True)
class AsianSettlementProfile:
    """Non-financial fractions won, pushed and lost by a settlement state."""

    won_fraction: Weight
    pushed_fraction: Weight
    lost_fraction: Weight

    def __post_init__(self) -> None:
        values = (self.won_fraction, self.pushed_fraction, self.lost_fraction)
        if any(not isinstance(value, Weight) for value in values):
            raise _error("profile fractions must be Weight values", "profile")
        if sum(value.value for value in values) != 1.0:
            raise _error("profile fractions must sum to one", "profile")

    @classmethod
    def for_state(cls, state: AsianSettlementState) -> AsianSettlementProfile:
        fractions = {
            AsianSettlementState.WIN: (1.0, 0.0, 0.0),
            AsianSettlementState.HALF_WIN: (0.5, 0.5, 0.0),
            AsianSettlementState.PUSH: (0.0, 1.0, 0.0),
            AsianSettlementState.HALF_LOSS: (0.0, 0.5, 0.5),
            AsianSettlementState.LOSS: (0.0, 0.0, 1.0),
        }
        won, pushed, lost = fractions[state]
        return cls(Weight(won), Weight(pushed), Weight(lost))


@dataclass(frozen=True, slots=True)
class AsianSettlementResult:
    """Auditable, deterministic result of settling an Asian line."""

    source_line: QuarterLine
    components: tuple[AsianLineComponent, ...]
    component_results: tuple[ElementarySettlementState, ...]
    state: AsianSettlementState
    profile: AsianSettlementProfile

    def __post_init__(self) -> None:
        if not isinstance(self.source_line, QuarterLine):
            raise _error("source_line must be a QuarterLine", "source_line")
        try:
            AsianLineSplit(self.source_line, self.components)
        except CalculationError as error:
            raise _error(error.message, "components") from error
        if (
            not isinstance(self.component_results, tuple)
            or len(self.component_results) != len(self.components)
            or any(
                not isinstance(item, ElementarySettlementState)
                for item in self.component_results
            )
        ):
            raise _error("component results are inconsistent", "component_results")
        if not isinstance(self.state, AsianSettlementState):
            raise _error("state must be an AsianSettlementState", "state")
        expected_states = {
            (ElementarySettlementState.WIN,): AsianSettlementState.WIN,
            (ElementarySettlementState.PUSH,): AsianSettlementState.PUSH,
            (ElementarySettlementState.LOSS,): AsianSettlementState.LOSS,
            (
                ElementarySettlementState.WIN,
                ElementarySettlementState.WIN,
            ): AsianSettlementState.WIN,
            (
                ElementarySettlementState.WIN,
                ElementarySettlementState.PUSH,
            ): AsianSettlementState.HALF_WIN,
            (
                ElementarySettlementState.PUSH,
                ElementarySettlementState.WIN,
            ): AsianSettlementState.HALF_WIN,
            (
                ElementarySettlementState.PUSH,
                ElementarySettlementState.PUSH,
            ): AsianSettlementState.PUSH,
            (
                ElementarySettlementState.PUSH,
                ElementarySettlementState.LOSS,
            ): AsianSettlementState.HALF_LOSS,
            (
                ElementarySettlementState.LOSS,
                ElementarySettlementState.PUSH,
            ): AsianSettlementState.HALF_LOSS,
            (
                ElementarySettlementState.LOSS,
                ElementarySettlementState.LOSS,
            ): AsianSettlementState.LOSS,
        }
        if expected_states.get(self.component_results) is not self.state:
            raise _error("state does not match component results", "state")
        if not isinstance(self.profile, AsianSettlementProfile):
            raise _error("profile must be an AsianSettlementProfile", "profile")
        if self.profile != AsianSettlementProfile.for_state(self.state):
            raise _error("profile does not match state", "profile")
