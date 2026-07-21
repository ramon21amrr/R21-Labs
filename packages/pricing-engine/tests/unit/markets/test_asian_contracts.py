"""Validation paths for T10 immutable contracts."""

from collections.abc import Callable
from dataclasses import replace

import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.distributions import (
    PoissonDistribution,
    ScoreProbabilityMatrix,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.domain import FairOdds, PoissonRate, Probability, QuarterLine
from lvfi_pricing.markets import (
    AsianMainLine,
    AsianMarketCode,
    AsianMarketPrice,
    AsianSettlementProbabilities,
    ExpectedAsianSettlementProfile,
    price_asian_handicap,
    select_asian_handicap_main_line,
)
from lvfi_pricing.markets import asian as asian_module
from lvfi_pricing.markets import main_line as main_line_module
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection


def _matrix() -> ScoreProbabilityMatrix:
    built = []
    for value in (1.0, 1.5):
        rate = PoissonRate.create(value)
        assert isinstance(rate, PoissonRate)
        distribution = build_poisson_distribution(rate)
        assert isinstance(distribution, PoissonDistribution)
        built.append(distribution)
    result = build_score_probability_matrix(built[0], built[1])
    assert isinstance(result, ScoreProbabilityMatrix)
    return result


def test_price_contract_inconsistencies_are_rejected() -> None:
    value = price_asian_handicap(_matrix(), HandicapSelection.HOME, QuarterLine(0))
    assert isinstance(value, AsianMarketPrice)
    bad: tuple[Callable[[], object], ...] = (
        lambda: replace(value, market=object()),  # type: ignore[arg-type]
        lambda: replace(value, selection=AsianTotalSelection.OVER),
        lambda: replace(value, line=object()),  # type: ignore[arg-type]
        lambda: replace(value, settlement_probabilities=object()),  # type: ignore[arg-type]
        lambda: replace(value, residual_mass=-1.0),
        lambda: replace(
            value,
            expected_profile=replace(value.expected_profile, total_probability=0.0),
        ),
        lambda: replace(value, fair_odds=None),
    )
    for factory in bad:
        with pytest.raises(CalculationError):
            factory()


def test_main_line_contract_inconsistencies_are_rejected() -> None:
    value = select_asian_handicap_main_line(_matrix())
    assert isinstance(value, AsianMainLine)
    bad: tuple[Callable[[], object], ...] = (
        lambda: replace(value, market=object()),  # type: ignore[arg-type]
        lambda: replace(value, reference_selection=HandicapSelection.AWAY),
        lambda: replace(value, reference_price=object()),  # type: ignore[arg-type]
        lambda: replace(value, opposite_price=value.reference_price),
        lambda: replace(value, balance_distance=-1.0),
        lambda: replace(value, evaluated_lines=0),
        lambda: replace(value, warnings=[]),  # type: ignore[arg-type]
    )
    for factory in bad:
        with pytest.raises(CalculationError):
            factory()


def test_probability_and_profile_contract_validation_paths() -> None:
    value = price_asian_handicap(_matrix(), HandicapSelection.HOME, QuarterLine(0))
    assert isinstance(value, AsianMarketPrice)
    states = value.settlement_probabilities
    profile = value.expected_profile
    bad: tuple[Callable[[], object], ...] = (
        lambda: AsianSettlementProbabilities(
            object(),  # type: ignore[arg-type]
            states.half_win,
            states.push,
            states.half_loss,
            states.loss,
            states.total_probability,
            states.residual_mass,
        ),
        lambda: replace(states, total_probability=-1.0),
        lambda: replace(states, residual_mass=-1.0),
        lambda: replace(profile, won_fraction=-1.0),
        lambda: replace(profile, total_probability=-1.0),
        lambda: replace(profile, residual_mass=-1.0),
        lambda: replace(value, warnings=[]),  # type: ignore[arg-type]
        lambda: replace(
            value,
            settlement_probabilities=replace(states, total_probability=0.0),
        ),
        lambda: replace(
            value,
            expected_profile=ExpectedAsianSettlementProfile(
                0.0,
                profile.pushed_fraction,
                profile.lost_fraction,
                profile.total_probability,
                profile.residual_mass,
            ),
        ),
    )
    for factory in bad:
        with pytest.raises((CalculationError, TypeError)):
            factory()


def test_pricing_and_main_line_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _matrix()
    error = CalculationError(ErrorCode.CONFIGURATION_ERROR, "forced")
    assert isinstance(
        asian_module.price_asian_handicap(
            source,
            HandicapSelection.HOME,
            QuarterLine(0),
            object(),  # type: ignore[arg-type]
        ),
        CalculationError,
    )
    assert isinstance(
        asian_module._price(
            source,
            HandicapSelection.HOME,
            QuarterLine(0),
            AsianMarketCode.HANDICAP,
            lambda *_: error,
            None,
        ),
        CalculationError,
    )
    monkeypatch.setattr(asian_module, "stable_sum", lambda _: error)
    assert isinstance(
        asian_module.price_asian_handicap(
            source, HandicapSelection.HOME, QuarterLine(0)
        ),
        CalculationError,
    )
    assert isinstance(
        main_line_module.generate_asian_total_candidates(object()),  # type: ignore[arg-type]
        CalculationError,
    )
    assert isinstance(main_line_module._catalogue((object(),)), CalculationError)
    assert isinstance(
        main_line_module._select(
            source,
            AsianMarketCode.HANDICAP,
            None,
            object(),  # type: ignore[arg-type]
        ),
        CalculationError,
    )


def test_remaining_contract_and_selection_error_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _matrix()
    value = price_asian_handicap(source, HandicapSelection.HOME, QuarterLine(0))
    assert isinstance(value, AsianMarketPrice)
    main = select_asian_handicap_main_line(source)
    assert isinstance(main, AsianMainLine)
    zero_states = AsianSettlementProbabilities(
        Probability(0.0),
        Probability(0.0),
        Probability(0.0),
        Probability(0.0),
        Probability(0.0),
        0.0,
        0.0,
    )
    with pytest.raises(CalculationError) as inconsistent:
        AsianMarketPrice(
            AsianMarketCode.HANDICAP,
            HandicapSelection.HOME,
            QuarterLine(0),
            zero_states,
            ExpectedAsianSettlementProfile(1.0, 0.0, 0.0, 1.0, 0.0),
            FairOdds(1.0),
            None,
            (),
            0.0,
        )
    assert inconsistent.value.code is ErrorCode.PROBABILITY_SUM_INVALID
    with pytest.raises(CalculationError) as undefined:
        AsianMarketPrice(
            AsianMarketCode.HANDICAP,
            HandicapSelection.HOME,
            QuarterLine(0),
            AsianSettlementProbabilities(
                Probability(1.0),
                Probability(0.0),
                Probability(0.0),
                Probability(0.0),
                Probability(0.0),
                1.0,
                0.0,
            ),
            ExpectedAsianSettlementProfile(0.0, 1.0, 0.0, 1.0, 0.0),
            FairOdds(1.0),
            None,
            (),
            0.0,
        )
    assert undefined.value.code is ErrorCode.FAIR_ODD_UNDEFINED
    with pytest.raises(CalculationError):
        replace(main, reference_price=replace(value, line=QuarterLine(1)))
    error = CalculationError(ErrorCode.CONFIGURATION_ERROR, "forced")
    monkeypatch.setattr(main_line_module, "price_asian_handicap", lambda *_: error)
    assert isinstance(
        main_line_module.select_asian_handicap_main_line(source), CalculationError
    )


def test_main_line_propagates_comparison_and_opposite_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _matrix()
    error = CalculationError(ErrorCode.CONFIGURATION_ERROR, "forced")
    monkeypatch.setattr(main_line_module, "is_close", lambda *_: error)
    assert isinstance(
        main_line_module.select_asian_handicap_main_line(
            source, (QuarterLine(0), QuarterLine(1))
        ),
        CalculationError,
    )
    original = main_line_module.price_asian_handicap  # type: ignore[attr-defined]
    calls = 0

    def opposite_failure(*args: object) -> AsianMarketPrice | CalculationError:
        nonlocal calls
        calls += 1
        return original(*args) if calls == 1 else error  # type: ignore[arg-type]

    monkeypatch.setattr(main_line_module, "price_asian_handicap", opposite_failure)
    assert isinstance(
        main_line_module.select_asian_handicap_main_line(source, (QuarterLine(0),)),
        CalculationError,
    )
