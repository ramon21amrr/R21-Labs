# ruff: noqa: F403, F405
from datetime import UTC, datetime
from typing import Any, cast

import pytest

from lvfi_pricing.core import CalculationError, ErrorCode
from lvfi_pricing.models.method_one import *  # noqa: F403
from lvfi_pricing.models.method_one import __all__ as public_api
from lvfi_pricing.models.samples import (
    DataSnapshotMetadata,
    MatchPeriodCode,
    ObservationRole,
    SampleDefinition,
    SampleFilter,
    SampleSnapshot,
    SampleWindowKind,
    StatisticCode,
    VenueCondition,
)


def at(hour: int = 0) -> datetime:
    return datetime(2026, 1, 1, hour, tzinfo=UTC)


def snapshot(role: MethodOneSeriesRole) -> SampleSnapshot:  # noqa: F405
    home = role in (
        MethodOneSeriesRole.HOME_PRODUCTION,  # noqa: F405
        MethodOneSeriesRole.HOME_CONCESSION,  # noqa: F405
    )
    production = role in (
        MethodOneSeriesRole.HOME_PRODUCTION,  # noqa: F405
        MethodOneSeriesRole.AWAY_PRODUCTION,  # noqa: F405
    )
    definition = SampleDefinition(
        f"sample-{role.value}",
        "home" if home else "away",
        ObservationRole.PRODUCTION if production else ObservationRole.CONCESSION,
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        SampleFilter(
            VenueCondition.HOME if home else VenueCondition.AWAY,
            SampleWindowKind.LAST_N,
            5,
        ),
        at(),
    )
    result = SampleSnapshot.create(
        definition=definition,
        data_metadata=DataSnapshotMetadata("v1", "hash", "source"),
        observations=(),
        exclusions=(),
    )
    assert isinstance(result, SampleSnapshot)
    return result


def request() -> MethodOneRequest:  # noqa: F405
    result = MethodOneRequest.create(  # noqa: F405
        target_match_id="target",
        home_team_id="home",
        away_team_id="away",
        statistic=StatisticCode.GOALS,
        period=MatchPeriodCode.REGULATION_TIME,
        series_references=tuple(
            MethodOneSeriesReference(role, snapshot(role))  # noqa: F405
            for role in reversed(tuple(MethodOneSeriesRole))  # noqa: F405
        ),
        configuration=MethodOneConfiguration("config"),  # noqa: F405
        data_cutoff_at=at(1),
    )
    assert isinstance(result, MethodOneRequest)  # noqa: F405
    return result


def averages() -> tuple[ContextualAverage, ...]:  # noqa: F405
    return tuple(
        ContextualAverage(  # noqa: F405
            f"sample-{role.value}", role, 1.0, 1.0, 1.0, 1, ("match",), (1.0,)
        )
        for role in MethodOneSeriesRole  # noqa: F405
    )


def test_public_api_versions_enums_and_root_namespace() -> None:
    assert public_api == (
        "MethodOneStatisticPeriod",
        "MethodOneSeriesRole",
        "RecencyPolicyCode",
        "MultiplierScope",
        "MultiplierCategory",
        "MethodOneWeightConfiguration",
        "MethodOneRecencyConfiguration",
        "MethodOneMultiplierCandidate",
        "MethodOneMultiplierResolution",
        "MethodOneConfiguration",
        "MethodOneRequest",
        "MethodOneSeriesReference",
        "ContextualAverage",
        "ContextualAverageEvidence",
        "MethodOneContextualAverages",
        "MethodOneRateExplanation",
        "MethodOneMetadata",
        "MethodOneResult",
        "calculate_contextual_average",
        "calculate_method_one_contextual_averages",
        "MethodOneWeightedComponent",
        "MethodOneParticipantBaseRateExplanation",
        "MethodOneBaseRateExplanation",
        "MethodOneBaseRateResult",
        "calculate_method_one_base_rates",
    )
    assert MethodOneStatisticPeriod.GOALS_FIRST_HALF.value == "goals/first_half"  # noqa: F405
    assert RecencyPolicyCode.UNIFORM_V1.value == "uniform/v1"  # noqa: F405
    import lvfi_pricing

    assert lvfi_pricing.__all__ == ()


def test_weights_recency_and_multiplier_contracts() -> None:
    assert MethodOneWeightConfiguration().weight_own == 0.5  # noqa: F405
    assert MethodOneWeightConfiguration(-0.0, 1.0).weight_own == 0.0  # noqa: F405
    assert isinstance(
        MethodOneWeightConfiguration.create(weight_own=True), CalculationError
    )  # noqa: F405
    for value in (-0.1, 1.1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            MethodOneWeightConfiguration(value, 1 - value)  # noqa: F405
    assert MethodOneRecencyConfiguration().code is RecencyPolicyCode.UNIFORM_V1  # noqa: F405
    assert isinstance(
        MethodOneRecencyConfiguration.create(code=object()), CalculationError
    )  # noqa: F405
    global_ = MethodOneMultiplierCandidate(MultiplierCategory.FORM, 1.0)  # noqa: F405
    match = MethodOneMultiplierCandidate(  # noqa: F405
        MultiplierCategory.FORM, 1.01, MultiplierScope.MATCH, "match"
    )
    resolution = MethodOneMultiplierResolution(
        MultiplierCategory.FORM, match, (global_,)
    )  # noqa: F405
    assert resolution.discarded == (global_,)
    assert isinstance(
        MethodOneMultiplierCandidate.create(category=object()), CalculationError
    )  # noqa: F405
    with pytest.raises(ValueError):
        MethodOneMultiplierCandidate(MultiplierCategory.PACE, 1.2)  # noqa: F405
    with pytest.raises(ValueError):
        MethodOneMultiplierResolution(MultiplierCategory.FORM, global_, (match,))  # noqa: F405


def test_request_series_are_canonical_immutable_and_validated() -> None:
    value = request()
    assert tuple(item.role for item in value.series_references) == tuple(
        MethodOneSeriesRole
    )  # noqa: F405
    with pytest.raises((AttributeError, TypeError)):
        value.home_team_id = "other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        hash(value)
    assert isinstance(MethodOneRequest.create(home_team_id="home"), CalculationError)  # noqa: F405
    with pytest.raises(ValueError):
        MethodOneRequest(  # noqa: F405
            "target",
            "same",
            "same",
            StatisticCode.GOALS,
            MatchPeriodCode.REGULATION_TIME,
            value.series_references,
            value.configuration,
        )
    with pytest.raises(ValueError):
        MethodOneRequest(  # noqa: F405
            "target",
            "home",
            "away",
            StatisticCode.CORNERS,
            MatchPeriodCode.REGULATION_TIME,
            value.series_references,
            value.configuration,
        )


def test_explanation_metadata_result_are_structural_only() -> None:
    explanation = MethodOneRateExplanation(  # noqa: F405
        tuple(reversed(averages())), 1.2, 0.8, 1.2, 0.8
    )
    assert tuple(item.role for item in explanation.averages) == tuple(
        MethodOneSeriesRole
    )  # noqa: F405
    metadata = MethodOneMetadata(  # noqa: F405
        sample_ids=tuple(item.sample_id for item in explanation.averages),
        sample_hashes=("a", "b", "c", "d"),
    )
    result = MethodOneResult(request(), explanation, metadata)  # noqa: F405
    assert result.errors == ()
    with pytest.raises(TypeError):
        hash(result)
    assert isinstance(ContextualAverage.create(sample_id="x"), CalculationError)  # noqa: F405
    with pytest.raises(ValueError):
        ContextualAverage("x", cast(Any, object()), 1, 1, 1, 1, ("m",), (1.0,))  # noqa: F405
    with pytest.raises(ValueError):
        ContextualAverage(
            "x", MethodOneSeriesRole.HOME_PRODUCTION, 1, 1, 1, 2, ("m",), (1.0,)
        )  # noqa: F405
    with pytest.raises(ValueError):
        ContextualAverage(
            "x", MethodOneSeriesRole.HOME_PRODUCTION, 1, 1, 0, 1, ("m",), (1.0,)
        )  # noqa: F405
    with pytest.raises(ValueError):
        MethodOneMetadata(sample_ids=("a",), sample_hashes=("a",))  # noqa: F405


def test_factories_and_rejected_shapes_cover_contract_boundaries() -> None:
    from lvfi_pricing.models.method_one import contracts

    with pytest.raises(ValueError):
        contracts._code("bad code", "field")
    with pytest.raises(ValueError):
        contracts._number(True, "field")
    with pytest.raises(ValueError):
        contracts._schema(2, "field")
    with pytest.raises(ValueError):
        contracts._items([], "field", str)
    assert contracts._period(StatisticCode.GOALS, MatchPeriodCode.FIRST_HALF)
    with pytest.raises(ValueError):
        MethodOneWeightConfiguration(0.5, 0.5, source_scope=cast(Any, object()))  # noqa: F405
    candidate = MethodOneMultiplierCandidate(  # noqa: F405
        MultiplierCategory.PACE, justification_code="reason"
    )
    assert candidate.justification_code == "reason"
    assert isinstance(MethodOneMultiplierResolution.create(), CalculationError)  # noqa: F405
    with pytest.raises(ValueError):
        MethodOneMultiplierResolution(  # noqa: F405
            MultiplierCategory.PACE, candidate, cast(Any, (object(),))
        )
    with pytest.raises(ValueError):
        MethodOneMultiplierResolution(cast(Any, object()), candidate)  # noqa: F405
    resolution = MethodOneMultiplierResolution(MultiplierCategory.PACE, candidate)  # noqa: F405
    assert isinstance(
        MethodOneConfiguration.create(  # noqa: F405
            configuration_id="x", multiplier_resolutions=(resolution, resolution)
        ),
        CalculationError,
    )
    with pytest.raises(ValueError):
        MethodOneConfiguration("x", home_weights=cast(Any, object()))  # noqa: F405
    ref = MethodOneSeriesReference(
        MethodOneSeriesRole.HOME_PRODUCTION,
        snapshot(MethodOneSeriesRole.HOME_PRODUCTION),
    )  # noqa: F405
    with pytest.raises(TypeError):
        hash(ref)
    with pytest.raises(ValueError):
        MethodOneSeriesReference(cast(Any, object()), ref.snapshot)  # noqa: F405
    assert isinstance(MethodOneSeriesReference.create(), CalculationError)  # noqa: F405
    base = request()
    with pytest.raises(ValueError):
        MethodOneRequest(  # noqa: F405
            base.target_match_id,
            base.home_team_id,
            base.away_team_id,
            base.statistic,
            base.period,
            base.series_references[:3],
            base.configuration,
        )
    with pytest.raises(ValueError):
        MethodOneRequest(  # noqa: F405
            base.target_match_id,
            base.home_team_id,
            base.away_team_id,
            base.statistic,
            base.period,
            base.series_references,
            base.configuration,
            datetime(2026, 1, 1),
        )
    with pytest.raises(ValueError):
        MethodOneRequest(  # noqa: F405
            base.target_match_id,
            base.home_team_id,
            base.away_team_id,
            base.statistic,
            base.period,
            base.series_references,
            base.configuration,
            method_version="2",
        )
    assert isinstance(MethodOneRateExplanation.create(), CalculationError)  # noqa: F405
    with pytest.raises(ValueError):
        MethodOneRateExplanation(averages()[:3], 1, 1, 1, 1)  # noqa: F405
    assert isinstance(
        MethodOneMetadata.create(sample_ids=("x",), sample_hashes=("x",)),
        CalculationError,
    )  # noqa: F405
    with pytest.raises(ValueError):
        MethodOneResult(cast(Any, object()), cast(Any, object()), cast(Any, object()))  # noqa: F405
    assert isinstance(MethodOneResult.create(), CalculationError)  # noqa: F405
    with pytest.raises(ValueError):
        MethodOneResult(
            base,
            MethodOneRateExplanation(averages(), 1, 1, 1, 1),
            MethodOneMetadata(),
            errors=(CalculationError(ErrorCode.INCONSISTENT_DATA, "x"),),
        )  # noqa: F405


def test_request_rejects_context_and_cutoff_after_snapshot() -> None:
    base = request()
    inconsistent = (
        MethodOneSeriesReference(  # noqa: F405
            MethodOneSeriesRole.HOME_PRODUCTION,  # noqa: F405
            snapshot(MethodOneSeriesRole.AWAY_PRODUCTION),  # noqa: F405
        ),
        *base.series_references[1:],
    )
    with pytest.raises(ValueError):
        MethodOneRequest(  # noqa: F405
            "target",
            "home",
            "away",
            base.statistic,
            base.period,
            inconsistent,
            base.configuration,
        )
    with pytest.raises(ValueError):
        MethodOneRequest(  # noqa: F405
            "target",
            "home",
            "away",
            base.statistic,
            base.period,
            base.series_references,
            base.configuration,
            datetime(2025, 1, 1, tzinfo=UTC),
        )
