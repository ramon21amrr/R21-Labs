from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from lvfi_pricing.core import CalculationError, ErrorCode
from lvfi_pricing.models.method_one import (
    MethodOneAdjustedRateResult,
    MethodOneConfiguration,
    MethodOneFinalResult,
    MethodOneMultiplierCandidate,
    MethodOnePricingResult,
    MethodOnePublicationState,
    MethodOneRequest,
    MethodOneSeriesReference,
    MethodOneSeriesRole,
    MultiplierAppliesTo,
    MultiplierCategory,
    MultiplierScope,
    price_method_one,
    run_method_one,
)
from lvfi_pricing.models.method_one import orchestration as implementation
from lvfi_pricing.models.samples import MatchPeriodCode, StatisticCode
from tests.unit.models.method_one.test_averages import sample
from tests.unit.models.method_one.test_multipliers import candidate


def request(count: int = 10) -> MethodOneRequest:
    references = tuple(
        MethodOneSeriesReference(role, sample((float(index + 1),) * count, role=role))
        for index, role in enumerate(MethodOneSeriesRole)
    )
    return MethodOneRequest(
        "target",
        "home",
        "away",
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        references,
        MethodOneConfiguration("orchestration"),
        "competition",
    )


def complete(*candidates: MethodOneMultiplierCandidate) -> MethodOneFinalResult:
    value = run_method_one(request(), candidates)
    assert isinstance(value, MethodOneFinalResult)
    return value


def failure(value: object) -> CalculationError:
    assert isinstance(value, CalculationError)
    return value


def test_runs_complete_flow_and_retains_structured_evidence() -> None:
    value = complete()
    assert value.match_id == value.request.match_id == "target"
    assert (
        value.contextual_averages.values == value.base_rates.contextual_averages.values
    )
    assert value.adjusted_rates.home_base_rate == value.base_rates.home_base_rate
    assert value.pricing.pricing_result.request == value.pricing.pricing_request
    assert value.explanation.snapshots == tuple(
        item.snapshot for item in value.request.series_references
    )
    assert value.explanation.resolutions is value.resolutions
    assert value.quality is value.adjusted_rates.quality
    assert value.publication_state is MethodOnePublicationState.PUBLISHABLE
    assert value.method_version == "1.0.0a4"
    assert (
        value.explanation.multiplier_catalog_version
        == "lvfi-method-one-adjustments@1.0.0"
    )
    assert value.explanation.explanation_schema_version == 1
    assert value.final_result_schema_version == value.orchestration_schema_version == 1


def test_candidates_are_canonical_and_equivalent_to_direct_pricing() -> None:
    match = candidate(
        MultiplierCategory.RECENT_FORM,
        1.1,
        MultiplierScope.MATCH,
        target_match_id="target",
    )
    global_candidate = candidate(MultiplierCategory.RECENT_FORM, 0.9)
    home_only = candidate(
        MultiplierCategory.HOME_FIELD_ADVANTAGE,
        1.05,
        applies_to=MultiplierAppliesTo.HOME,
    )
    first = complete(global_candidate, home_only, match)
    second = complete(match, global_candidate, home_only)
    assert first == second
    assert first.multiplier_candidates == (home_only, match, global_candidate)
    assert (
        next(item for item in first.resolutions if item.selected is match).selected
        is match
    )
    assert first.adjusted_rates.home_adjusted_rate > first.base_rates.home_base_rate
    direct = price_method_one(first.adjusted_rates)
    assert isinstance(direct, MethodOnePricingResult)
    assert first.pricing.pricing_result == direct.pricing_result


@pytest.mark.parametrize(
    ("count", "state"),
    (
        (10, MethodOnePublicationState.PUBLISHABLE),
        (5, MethodOnePublicationState.CONDITIONAL),
        (1, MethodOnePublicationState.AUDIT_ONLY),
    ),
)
def test_quality_is_preserved_without_improvement(
    count: int, state: MethodOnePublicationState
) -> None:
    value = run_method_one(request(count))
    assert isinstance(value, MethodOneFinalResult)
    assert value.publication_state is state
    assert value.quality is value.base_rates.quality is value.adjusted_rates.quality
    assert value.warnings == value.base_rates.warnings


def test_input_immutability_public_api_and_root_boundary() -> None:
    source = request()
    candidates = (candidate(),)
    result = complete(*candidates)
    import lvfi_pricing
    from lvfi_pricing.models import method_one

    assert source == request()
    assert candidates == (candidate(),)
    assert "run_method_one" in method_one.__all__
    assert not hasattr(lvfi_pricing, "run_method_one")
    with pytest.raises(FrozenInstanceError):
        cast(Any, result).match_id = "other"


def test_blocked_average_stops_before_pricing_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def never_called(value: object) -> CalculationError:
        nonlocal calls
        calls += 1
        return CalculationError(ErrorCode.SAMPLE_EMPTY, "blocked")

    monkeypatch.setattr(implementation, "price_method_one", never_called)
    value = run_method_one(request(0))
    assert failure(value).code is ErrorCode.SAMPLE_EMPTY
    assert calls == 0


@pytest.mark.parametrize(
    "stage",
    (
        "calculate_method_one_contextual_averages",
        "calculate_method_one_base_rates",
        "resolve_method_one_multipliers",
        "apply_method_one_multipliers",
        "price_method_one",
    ),
)
def test_stage_errors_propagate_without_later_execution(
    monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    error = CalculationError(ErrorCode.INCONSISTENT_DATA, "stopped")
    monkeypatch.setattr(implementation, stage, lambda *args, **kwargs: error)
    assert run_method_one(request()) is error


def test_incoherent_stage_result_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = price_method_one

    def incoherent(
        value: MethodOneAdjustedRateResult,
    ) -> MethodOnePricingResult | CalculationError:
        result = original(value)
        assert isinstance(result, MethodOnePricingResult)
        object.__setattr__(result, "match_id", "other")
        return result

    monkeypatch.setattr(implementation, "price_method_one", incoherent)
    assert failure(run_method_one(request())).code is ErrorCode.INCONSISTENT_DATA


def test_incoherent_handoff_is_typed() -> None:
    error = implementation._error("incoherent", "orchestration")
    assert error.code is ErrorCode.INCONSISTENT_DATA


def test_rejects_mutable_candidates_and_incoherent_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert (
        failure(run_method_one(request(), cast(Any, []))).code
        is ErrorCode.INVALID_MULTIPLIER
    )
    value = complete()
    object.__setattr__(value.pricing, "match_id", "other")
    assert not implementation._in_context(
        value.request,
        value.contextual_averages,
        value.base_rates,
        value.adjusted_rates,
        value.pricing,
    )
