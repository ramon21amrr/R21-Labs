from typing import Any, cast

import pytest

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy
from lvfi_pricing.distributions import build_poisson_distribution
from lvfi_pricing.domain import PoissonRate, QuarterLine
from lvfi_pricing.engine import (
    AsianHandicapMainLineRequest,
    AsianHandicapRequest,
    AsianTotalMainLineRequest,
    AsianTotalRequest,
    BothTeamsToScoreRequest,
    DoubleChanceRequest,
    PricingRequest,
    PricingResult,
    ThreeWayResultRequest,
    TotalGoalsRequest,
    orchestrator,
    run_pricing_engine,
)
from lvfi_pricing.markets import HalfGoalLine
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection


def _request(markets: tuple[object, ...]) -> PricingRequest:
    request = PricingRequest.create(
        PoissonRate(1.5), PoissonRate(1.0), markets, NumericPolicy()
    )
    assert isinstance(request, PricingRequest)
    return request


def test_runs_requested_markets_once_in_canonical_order() -> None:
    result = run_pricing_engine(
        _request(
            (
                AsianTotalMainLineRequest(),
                TotalGoalsRequest(HalfGoalLine(5)),
                ThreeWayResultRequest(),
                BothTeamsToScoreRequest(),
                DoubleChanceRequest(),
                AsianHandicapRequest(HandicapSelection.HOME, QuarterLine(0)),
            )
        )
    )
    assert isinstance(result, PricingResult)
    assert result.success
    assert (
        tuple(item.code for item in result.request.requested_markets)
        == result.metadata.calculated_markets
    )
    assert len(result.market_results) == 6
    assert result.metadata.score_matrix_dimensions == (
        result.home_distribution.max_count + 1,
        result.away_distribution.max_count + 1,
    )


def test_invalid_request_stops_before_calculation() -> None:
    request = PricingRequest(PoissonRate(1.0), PoissonRate(1.0), (), NumericPolicy())
    result = run_pricing_engine(request)
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.INVALID_MARKET


def test_remaining_market_paths() -> None:
    result = run_pricing_engine(
        _request(
            (
                AsianTotalRequest(AsianTotalSelection.UNDER, QuarterLine(5)),
                AsianHandicapMainLineRequest(),
            )
        )
    )
    assert isinstance(result, PricingResult)
    assert len(result.market_results) == 2


def test_orchestrator_error_helpers_and_fail_fast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = CalculationError(ErrorCode.CONFIGURATION_ERROR, "failure")
    invalid_result = orchestrator.run_pricing_engine(cast(PricingRequest, object()))
    assert isinstance(invalid_result, CalculationError)
    warning = CalculationWarning(
        ErrorCode.CONFIGURATION_ERROR, "warning", field="field"
    )
    assert orchestrator._warning_key(warning) == orchestrator._warning_key(warning)
    assert orchestrator._warnings((object(),)) == ()
    with pytest.raises(TypeError, match="incompatible request"):
        orchestrator._price_market(
            cast(Any, object()),
            cast(Any, object()),
            cast(Any, object()),
            cast(Any, object()),
            None,
        )
    request = _request((ThreeWayResultRequest(),))
    monkeypatch.setattr(
        "lvfi_pricing.engine.orchestrator.build_poisson_distribution", lambda *_: error
    )
    assert orchestrator.run_pricing_engine(request) is error


def test_dependent_fail_fast_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request((ThreeWayResultRequest(),))
    error = CalculationError(ErrorCode.CONFIGURATION_ERROR, "failure")
    original_poisson = build_poisson_distribution
    calls = 0

    def second_poisson(*args: object) -> object:
        nonlocal calls
        calls += 1
        return (
            original_poisson(cast(PoissonRate, args[0]), cast(NumericPolicy, args[1]))
            if calls == 1
            else error
        )

    monkeypatch.setattr(
        "lvfi_pricing.engine.orchestrator.build_poisson_distribution", second_poisson
    )
    assert orchestrator.run_pricing_engine(request) is error
    assert calls == 2


def test_matrix_and_difference_fail_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request((ThreeWayResultRequest(),))
    error = CalculationError(ErrorCode.CONFIGURATION_ERROR, "failure")
    monkeypatch.setattr(
        "lvfi_pricing.engine.orchestrator.build_score_probability_matrix",
        lambda *_: error,
    )
    assert orchestrator.run_pricing_engine(request) is error


def test_warning_consolidation_and_market_fail_fast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    warning_a = CalculationWarning(ErrorCode.CONFIGURATION_ERROR, "a")
    warning_b = CalculationWarning(ErrorCode.INVALID_MARKET, "b")
    warning_c = CalculationWarning(ErrorCode.INVALID_LAMBDA, "c")

    class Source:
        warnings = (warning_a, warning_b, warning_a, warning_c)

    class UntypedSource:
        warnings: list[CalculationWarning] = []

    warnings = orchestrator._warnings((Source(), UntypedSource()))
    canonical_warnings = tuple(
        sorted((warning_a, warning_b, warning_c), key=orchestrator._warning_key)
    )
    assert warnings == canonical_warnings
    assert tuple(map(orchestrator._warning_key, warnings)) == tuple(
        sorted(map(orchestrator._warning_key, canonical_warnings))
    )
    request = _request((ThreeWayResultRequest(), BothTeamsToScoreRequest()))
    error = CalculationError(ErrorCode.INVALID_MARKET, "failure", "market")
    calls = 0

    def broken(*args: object) -> CalculationError:
        nonlocal calls
        calls += 1
        return error

    monkeypatch.setattr(
        "lvfi_pricing.engine.orchestrator.price_three_way_result", broken
    )
    assert orchestrator.run_pricing_engine(request) is error
    assert calls == 1
    monkeypatch.undo()
    monkeypatch.setattr(
        "lvfi_pricing.engine.orchestrator.build_goal_difference_distribution",
        lambda *_: error,
    )
    assert orchestrator.run_pricing_engine(request) is error
