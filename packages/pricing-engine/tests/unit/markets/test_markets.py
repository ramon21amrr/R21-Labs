"""Testes dos mercados básicos T08."""

import math
from dataclasses import FrozenInstanceError

import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy
from lvfi_pricing.distributions import (
    GoalDifferenceDistribution,
    PoissonDistribution,
    ScoreProbabilityMatrix,
    build_goal_difference_distribution,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.domain import FairOdds, PoissonRate, Probability
from lvfi_pricing.markets import (
    BttsSelection,
    DoubleChanceSelection,
    HalfGoalLine,
    MarketCode,
    MarketPrices,
    PricedSelection,
    ThreeWaySelection,
    TotalSelection,
    price_btts,
    price_double_chance,
    price_three_way_result,
    price_total_goals,
)
from lvfi_pricing.markets import basic as basic_module
from lvfi_pricing.markets import totals as totals_module


def matrix(home: float = 1.0, away: float = 1.5) -> ScoreProbabilityMatrix:
    rates = [PoissonRate.create(value) for value in (home, away)]
    assert all(isinstance(rate, PoissonRate) for rate in rates)
    assert all(isinstance(rate, PoissonRate) for rate in rates)
    typed_rates = [rate for rate in rates if isinstance(rate, PoissonRate)]
    distributions = [build_poisson_distribution(rate) for rate in typed_rates]
    assert all(isinstance(item, PoissonDistribution) for item in distributions)
    typed_distributions = [
        item for item in distributions if isinstance(item, PoissonDistribution)
    ]
    result = build_score_probability_matrix(
        typed_distributions[0], typed_distributions[1]
    )
    assert isinstance(result, ScoreProbabilityMatrix)
    return result


def difference() -> GoalDifferenceDistribution:
    result = build_goal_difference_distribution(matrix())
    assert isinstance(result, GoalDifferenceDistribution)
    return result


def test_contracts_and_odds_are_typed_and_immutable() -> None:
    positive = PricedSelection.create(ThreeWaySelection.HOME, Probability.create(0.5))
    assert isinstance(positive, PricedSelection)
    assert positive.fair_odds is not None and positive.fair_odds.value == 2.0
    zero = PricedSelection.create(ThreeWaySelection.DRAW, Probability.create(0.0))
    assert isinstance(zero, PricedSelection)
    assert zero.fair_odds is None
    assert zero.error is not None and zero.error.code is ErrorCode.FAIR_ODD_UNDEFINED
    assert str(ThreeWaySelection.HOME) == "home"
    with pytest.raises(FrozenInstanceError):
        positive.probability = zero.probability  # type: ignore[misc]


def test_three_way_and_double_chance() -> None:
    result = price_three_way_result(difference())
    assert isinstance(result, MarketPrices)
    assert result.market is MarketCode.THREE_WAY_RESULT
    assert tuple(item.selection for item in result.selections) == (
        ThreeWaySelection.HOME,
        ThreeWaySelection.DRAW,
        ThreeWaySelection.AWAY,
    )
    assert math.isclose(
        sum(item.probability.value for item in result.selections),
        result.total_probability,
        abs_tol=1e-12,
    )
    double = price_double_chance(result)
    assert isinstance(double, MarketPrices)
    assert tuple(item.selection for item in double.selections) == (
        DoubleChanceSelection.HOME_OR_DRAW,
        DoubleChanceSelection.HOME_OR_AWAY,
        DoubleChanceSelection.DRAW_OR_AWAY,
    )
    assert math.isclose(
        sum(item.probability.value for item in double.selections),
        2.0 * result.total_probability,
        abs_tol=1e-12,
    )
    assert isinstance(price_double_chance(object()), CalculationError)  # type: ignore[arg-type]


def test_btts_and_totals_preserve_mass() -> None:
    source = matrix()
    btts = price_btts(source)
    assert isinstance(btts, MarketPrices)
    assert tuple(item.selection for item in btts.selections) == (
        BttsSelection.YES,
        BttsSelection.NO,
    )
    assert math.isclose(
        sum(item.probability.value for item in btts.selections),
        source.total_probability,
        abs_tol=1e-12,
    )
    for units in (1, 3, 5, 7, 9, 11):
        line = HalfGoalLine.create(units)
        assert isinstance(line, HalfGoalLine)
        total = price_total_goals(source, line)
        assert isinstance(total, MarketPrices)
        assert tuple(item.selection for item in total.selections) == (
            TotalSelection.OVER,
            TotalSelection.UNDER,
        )
        assert math.isclose(
            sum(item.probability.value for item in total.selections),
            source.total_probability,
            abs_tol=1e-12,
        )


@pytest.mark.parametrize("value", [True, 0, 2, 4, 6, 8, 10, 13, -1, 0.5, "1"])
def test_total_line_validation(value: object) -> None:
    result = HalfGoalLine.create(value)
    assert isinstance(result, CalculationError)
    assert result.code in (ErrorCode.INVALID_NUMBER, ErrorCode.INVALID_MARKET)


def test_zero_rates_and_invalid_inputs() -> None:
    source = matrix(0.0, 0.0)
    btts = price_btts(source)
    assert isinstance(btts, MarketPrices)
    assert btts.selections[0].probability.value == 0.0
    assert btts.selections[0].fair_odds is None
    assert btts.selections[1].probability.value == 1.0
    difference_result = build_goal_difference_distribution(source)
    assert isinstance(difference_result, GoalDifferenceDistribution)
    result = price_three_way_result(difference_result)
    assert isinstance(result, MarketPrices)
    assert result.selections[0].probability.value == 0.0
    assert result.selections[1].probability.value == 1.0
    assert isinstance(price_btts(object()), CalculationError)  # type: ignore[arg-type]
    assert isinstance(price_total_goals(source, object()), CalculationError)  # type: ignore[arg-type]


def test_contract_validation_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    probability = Probability.create(0.5)
    assert isinstance(probability, Probability)
    assert isinstance(PricedSelection.create(object(), probability), CalculationError)
    assert isinstance(
        PricedSelection.create(ThreeWaySelection.HOME, object()), CalculationError
    )
    assert isinstance(
        PricedSelection.create(ThreeWaySelection.HOME, probability, []),  # type: ignore[arg-type]
        CalculationError,
    )
    monkeypatch.setattr(
        FairOdds,
        "from_probability",
        classmethod(lambda cls, _: CalculationError(ErrorCode.INVALID_ODD, "bad")),
    )
    assert isinstance(
        PricedSelection.create(ThreeWaySelection.HOME, probability), CalculationError
    )
    monkeypatch.undo()
    valid = PricedSelection.create(ThreeWaySelection.HOME, probability)
    assert isinstance(valid, PricedSelection)
    with pytest.raises(CalculationError):
        MarketPrices(object(), (), 0.0, 0.0)  # type: ignore[arg-type]
    with pytest.raises(CalculationError):
        MarketPrices(MarketCode.THREE_WAY_RESULT, (object(),), 0.0, 0.0)  # type: ignore[arg-type]
    with pytest.raises(CalculationError):
        MarketPrices(MarketCode.THREE_WAY_RESULT, (), math.nan, 0.0)
    with pytest.raises(CalculationError):
        MarketPrices(MarketCode.THREE_WAY_RESULT, (), 1.1, 0.0)
    with pytest.raises(CalculationError):
        MarketPrices(MarketCode.THREE_WAY_RESULT, (), 0.0, -1.0)
    with pytest.raises(CalculationError):
        MarketPrices(MarketCode.THREE_WAY_RESULT, (), 0.0, 0.0, (object(),))  # type: ignore[arg-type]
    good = PricedSelection.create(ThreeWaySelection.HOME, Probability.create(0.0))
    assert isinstance(good, PricedSelection)
    with pytest.raises(CalculationError):
        MarketPrices(MarketCode.THREE_WAY_RESULT, (good,), 0.5, 0.0)


def test_market_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    source = matrix()
    difference_source = difference()
    assert isinstance(price_three_way_result(object()), CalculationError)  # type: ignore[arg-type]
    assert isinstance(
        price_three_way_result(difference_source, object()),  # type: ignore[arg-type]
        CalculationError,
    )
    result = price_three_way_result(difference_source)
    assert isinstance(result, MarketPrices)
    assert isinstance(price_double_chance(result, object()), CalculationError)  # type: ignore[arg-type]
    assert isinstance(price_btts(source, object()), CalculationError)  # type: ignore[arg-type]
    monkeypatch.setattr(
        basic_module,
        "stable_sum",
        lambda _: CalculationError(ErrorCode.INVALID_NUMBER, "bad"),
    )
    assert isinstance(price_double_chance(result), CalculationError)
    assert isinstance(price_btts(source), CalculationError)
    monkeypatch.setattr(
        basic_module,
        "stable_sum",
        lambda _: 0.0,
    )
    assert isinstance(price_btts(source), CalculationError)
    monkeypatch.setattr(
        basic_module,
        "stable_sum",
        lambda _: 0.0,
    )
    assert isinstance(
        basic_module._market(
            MarketCode.THREE_WAY_RESULT, (), math.nan, 0.0, (), NumericPolicy()
        ),
        CalculationError,
    )
    monkeypatch.undo()
    assert isinstance(
        basic_module._market(
            MarketCode.THREE_WAY_RESULT,
            ((ThreeWaySelection.HOME, -1.0),),
            -1.0,
            0.0,
            (),
            NumericPolicy(),
        ),
        CalculationError,
    )
    assert isinstance(
        basic_module._market(
            MarketCode.THREE_WAY_RESULT,
            ((object(), 1.0),),
            1.0,
            0.0,
            (),
            NumericPolicy(),
        ),
        CalculationError,
    )
    assert isinstance(
        basic_module._market(
            MarketCode.THREE_WAY_RESULT, (), 1.0, 0.0, (), NumericPolicy()
        ),
        CalculationError,
    )
    assert isinstance(
        basic_module._market(
            MarketCode.THREE_WAY_RESULT,
            ((ThreeWaySelection.HOME, -1.0),),
            -1.0,
            0.0,
            (),
            NumericPolicy(),
        ),
        CalculationError,
    )


def test_total_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    source = matrix()
    line = HalfGoalLine.create(1)
    assert isinstance(line, HalfGoalLine)
    assert line.decimal_value == 0.5
    assert isinstance(price_total_goals(object(), line), CalculationError)  # type: ignore[arg-type]
    assert isinstance(price_total_goals(source, object()), CalculationError)  # type: ignore[arg-type]
    assert isinstance(price_total_goals(source, line, object()), CalculationError)  # type: ignore[arg-type]
    monkeypatch.setattr(
        totals_module,
        "stable_sum",
        lambda _: CalculationError(ErrorCode.INVALID_NUMBER, "bad"),
    )
    assert isinstance(price_total_goals(source, line), CalculationError)
