"""Unit tests for T10 Asian probabilistic prices."""

import math
from dataclasses import FrozenInstanceError

import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.distributions import (
    PoissonDistribution,
    ScoreProbabilityMatrix,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.domain import PoissonRate, Probability, QuarterLine
from lvfi_pricing.markets import (
    AsianMarketCode,
    AsianMarketPrice,
    AsianSettlementProbabilities,
    ExpectedAsianSettlementProfile,
    price_asian_handicap,
    price_asian_total,
)
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection


def matrix(home: float = 1.0, away: float = 1.5) -> ScoreProbabilityMatrix:
    distributions = []
    for value in (home, away):
        rate = PoissonRate.create(value)
        assert isinstance(rate, PoissonRate)
        distribution = build_poisson_distribution(rate)
        assert isinstance(distribution, PoissonDistribution)
        distributions.append(distribution)
    result = build_score_probability_matrix(distributions[0], distributions[1])
    assert isinstance(result, ScoreProbabilityMatrix)
    return result


@pytest.mark.parametrize("quarters", range(-8, 9))
def test_handicap_prices_each_state_without_renormalization(quarters: int) -> None:
    source = matrix()
    line = QuarterLine(quarters)
    price = price_asian_handicap(source, HandicapSelection.HOME, line)
    assert isinstance(price, AsianMarketPrice)
    states = price.settlement_probabilities
    assert math.isclose(
        sum(
            item.value
            for item in (
                states.win,
                states.half_win,
                states.push,
                states.half_loss,
                states.loss,
            )
        ),
        source.total_probability,
        abs_tol=1e-12,
    )
    profile = price.expected_profile
    assert math.isclose(
        profile.won_fraction + profile.pushed_fraction + profile.lost_fraction,
        source.total_probability,
        abs_tol=1e-12,
    )
    if profile.won_fraction:
        assert price.fair_odds is not None
        assert math.isclose(
            price.fair_odds.value,
            1.0 + profile.lost_fraction / profile.won_fraction,
            abs_tol=1e-12,
        )
    assert price.residual_mass == source.residual_mass


@pytest.mark.parametrize("quarters", range(0, 25))
def test_total_prices_each_state_without_renormalization(quarters: int) -> None:
    source = matrix()
    price = price_asian_total(source, AsianTotalSelection.OVER, QuarterLine(quarters))
    assert isinstance(price, AsianMarketPrice)
    assert price.market is AsianMarketCode.TOTAL
    assert price.settlement_probabilities.total_probability == source.total_probability
    assert price.expected_profile.residual_mass == source.residual_mass


def test_half_states_and_undefined_odds_are_explicit() -> None:
    source = matrix(0.0, 0.0)
    half_win = price_asian_handicap(source, HandicapSelection.HOME, QuarterLine(1))
    assert isinstance(half_win, AsianMarketPrice)
    assert half_win.settlement_probabilities.half_win.value == 1.0
    assert half_win.expected_profile.won_fraction == 0.5
    undefined = price_asian_handicap(source, HandicapSelection.HOME, QuarterLine(-1))
    assert isinstance(undefined, AsianMarketPrice)
    assert undefined.fair_odds is None
    assert undefined.error is not None
    assert undefined.error.code is ErrorCode.FAIR_ODD_UNDEFINED


def test_normative_fair_odds_excludes_push_and_residual() -> None:
    no_residual = matrix(0.0, 0.0)
    half_win = price_asian_handicap(no_residual, HandicapSelection.HOME, QuarterLine(1))
    assert isinstance(half_win, AsianMarketPrice)
    profile = half_win.expected_profile
    assert no_residual.residual_mass == 0.0
    assert half_win.fair_odds is not None
    assert (
        1.0 + profile.lost_fraction / profile.won_fraction
        == (1.0 - profile.pushed_fraction) / profile.won_fraction
    )

    with_residual = matrix(10.0, 10.0)
    price = price_asian_total(with_residual, AsianTotalSelection.OVER, QuarterLine(10))
    assert isinstance(price, AsianMarketPrice)
    assert price.fair_odds is not None
    profile = price.expected_profile
    normative = 1.0 + profile.lost_fraction / profile.won_fraction
    legacy = (1.0 - profile.pushed_fraction) / profile.won_fraction
    assert with_residual.residual_mass > 0.0
    assert price.fair_odds.value == normative
    assert legacy != normative
    assert math.isclose(
        legacy - normative,
        with_residual.residual_mass / profile.won_fraction,
        rel_tol=1e-3,
        abs_tol=1e-15,
    )


def test_partial_states_contribute_exactly_half_to_expected_fractions() -> None:
    source = matrix(0.0, 0.0)
    cases = (
        (
            price_asian_handicap(source, HandicapSelection.HOME, QuarterLine(1)),
            (0.5, 0.5, 0.0),
        ),
        (
            price_asian_handicap(source, HandicapSelection.HOME, QuarterLine(-1)),
            (0.0, 0.5, 0.5),
        ),
        (
            price_asian_total(source, AsianTotalSelection.UNDER, QuarterLine(1)),
            (0.5, 0.5, 0.0),
        ),
        (
            price_asian_total(source, AsianTotalSelection.OVER, QuarterLine(1)),
            (0.0, 0.5, 0.5),
        ),
    )
    for price, expected in cases:
        assert isinstance(price, AsianMarketPrice)
        profile = price.expected_profile
        assert (
            profile.won_fraction,
            profile.pushed_fraction,
            profile.lost_fraction,
        ) == expected


@pytest.mark.parametrize("quarters", (0, 2, 1))
@pytest.mark.parametrize("selection", tuple(HandicapSelection))
def test_handicap_line_kinds_and_sides_use_normative_odds(
    quarters: int, selection: HandicapSelection
) -> None:
    price = price_asian_handicap(matrix(), selection, QuarterLine(quarters))
    assert isinstance(price, AsianMarketPrice)
    profile = price.expected_profile
    assert price.fair_odds is not None
    assert math.isfinite(price.fair_odds.value)
    assert price.fair_odds.value == 1.0 + profile.lost_fraction / profile.won_fraction


@pytest.mark.parametrize("quarters", (4, 2, 1))
@pytest.mark.parametrize("selection", tuple(AsianTotalSelection))
def test_total_line_kinds_and_sides_use_normative_odds(
    quarters: int, selection: AsianTotalSelection
) -> None:
    price = price_asian_total(matrix(), selection, QuarterLine(quarters))
    assert isinstance(price, AsianMarketPrice)
    profile = price.expected_profile
    assert price.fair_odds is not None
    assert math.isfinite(price.fair_odds.value)
    assert price.fair_odds.value == 1.0 + profile.lost_fraction / profile.won_fraction


def test_prices_are_symmetric_and_immutable() -> None:
    source = matrix(1.5, 1.0)
    home = price_asian_handicap(source, HandicapSelection.HOME, QuarterLine(-3))
    away = price_asian_handicap(source, HandicapSelection.AWAY, QuarterLine(3))
    assert isinstance(home, AsianMarketPrice) and isinstance(away, AsianMarketPrice)
    assert home.settlement_probabilities.win == away.settlement_probabilities.loss
    assert (
        home.settlement_probabilities.half_win
        == away.settlement_probabilities.half_loss
    )
    with pytest.raises(FrozenInstanceError):
        home.line = QuarterLine(0)  # type: ignore[misc]


def test_contract_validation_and_invalid_inputs() -> None:
    probability = Probability(0.0)
    with pytest.raises(CalculationError):
        AsianSettlementProbabilities(
            probability, probability, probability, probability, probability, 1.0, 0.0
        )
    with pytest.raises(CalculationError):
        ExpectedAsianSettlementProfile(0.0, 0.0, 0.0, 1.0, 0.0)
    assert isinstance(
        price_asian_handicap(object(), HandicapSelection.HOME, QuarterLine(0)),  # type: ignore[arg-type]
        CalculationError,
    )
    assert isinstance(
        price_asian_handicap(matrix(), object(), QuarterLine(0)),  # type: ignore[arg-type]
        CalculationError,
    )
    assert isinstance(
        price_asian_total(matrix(), AsianTotalSelection.OVER, object()),  # type: ignore[arg-type]
        CalculationError,
    )
