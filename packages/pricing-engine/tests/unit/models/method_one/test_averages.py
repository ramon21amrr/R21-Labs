from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest

from lvfi_pricing.core import CalculationError, ErrorCode
from lvfi_pricing.models.method_one import (
    ContextualAverage,
    MethodOneConfiguration,
    MethodOneRequest,
    MethodOneSeriesReference,
    MethodOneSeriesRole,
    RecencyPolicyCode,
    calculate_contextual_average,
    calculate_method_one_contextual_averages,
)
from lvfi_pricing.models.samples import (
    DataSnapshotMetadata,
    MatchIdentity,
    MatchObservation,
    MatchPeriodCode,
    ObservationRole,
    ObservationState,
    ObservationUnit,
    ObservationValue,
    ParticipantRole,
    SampleDefinition,
    SampleExclusion,
    SampleExclusionReason,
    SampleFilter,
    SampleQualityLevel,
    SampleSnapshot,
    SampleWindowKind,
    StatisticCode,
    VenueCondition,
)


def at(index: int) -> datetime:
    return datetime(2026, 1, 31, tzinfo=UTC) - timedelta(days=index)


def context(
    role: MethodOneSeriesRole,
) -> tuple[str, ParticipantRole, VenueCondition, ObservationRole]:
    if role is MethodOneSeriesRole.HOME_PRODUCTION:
        return (
            "home",
            ParticipantRole.HOME,
            VenueCondition.HOME,
            ObservationRole.PRODUCTION,
        )
    if role is MethodOneSeriesRole.HOME_CONCESSION:
        return (
            "home",
            ParticipantRole.HOME,
            VenueCondition.HOME,
            ObservationRole.CONCESSION,
        )
    if role is MethodOneSeriesRole.AWAY_PRODUCTION:
        return (
            "away",
            ParticipantRole.AWAY,
            VenueCondition.AWAY,
            ObservationRole.PRODUCTION,
        )
    return "away", ParticipantRole.AWAY, VenueCondition.AWAY, ObservationRole.CONCESSION


def sample(
    values: tuple[float, ...],
    *,
    role: MethodOneSeriesRole = MethodOneSeriesRole.HOME_PRODUCTION,
    exclusions: tuple[SampleExclusion, ...] = (),
) -> SampleSnapshot:
    subject, participant, venue, observation_role = context(role)
    definition = SampleDefinition(
        f"sample-{role.value}",
        subject,
        observation_role,
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        SampleFilter(
            VenueCondition.HOME
            if participant is ParticipantRole.HOME
            else VenueCondition.AWAY,
            SampleWindowKind.LAST_N,
            10 if len(values) + len(exclusions) > 5 else 5,
        ),
        at(-1),
    )
    observations = tuple(
        MatchObservation(
            MatchIdentity(
                f"match-{index}",
                at(index),
                __import__(
                    "lvfi_pricing.models.samples", fromlist=["MatchState"]
                ).MatchState.COMPLETED,
            ),
            subject,
            f"opponent-{index}",
            participant,
            venue,
            observation_role,
            StatisticCode.GOALS,
            MatchPeriodCode.REGULATION_TIME,
            ObservationValue(ObservationState.OBSERVED, value, ObservationUnit.COUNT),
        )
        for index, value in enumerate(values)
    )
    result = SampleSnapshot.create(
        definition=definition,
        data_metadata=DataSnapshotMetadata("v1", "hash", "source"),
        observations=observations,
        exclusions=exclusions,
    )
    assert isinstance(result, SampleSnapshot)
    return result


def exclusion(
    index: int, state: ObservationState, reason: SampleExclusionReason
) -> SampleExclusion:
    return SampleExclusion(
        MatchIdentity(
            f"excluded-{index}",
            at(index + 20),
            __import__(
                "lvfi_pricing.models.samples", fromlist=["MatchState"]
            ).MatchState.COMPLETED,
        ),
        reason,
        state,
        blocks_automatic_use=state is ObservationState.PENDING_REVIEW,
    )


def failure(result: object) -> CalculationError:
    assert isinstance(result, CalculationError)
    return result


def average(snapshot: SampleSnapshot) -> ContextualAverage:
    result = calculate_contextual_average(snapshot)
    assert isinstance(result, ContextualAverage)
    return result


def test_uniform_average_evidence_zero_and_immutability() -> None:
    source = sample((0.0, 1.5, 3.0))
    before = source
    result = average(source)
    assert result.value == 1.5
    assert result.numerator == 4.5
    assert result.denominator == 3.0
    assert result.effective_weights == (1.0, 1.0, 1.0)
    assert result.used_match_ids == ("match-0", "match-1", "match-2")
    assert result.evidence is not None
    assert result.evidence.used_values == (0.0, 1.5, 3.0)
    assert result.evidence.recency_policy is RecencyPolicyCode.UNIFORM_V1
    assert result.evidence.calculation_method == "math.fsum/uniform/v1"
    assert result.evidence.deterministic
    assert source == before
    with pytest.raises((AttributeError, TypeError)):
        result.value = 0.0  # type: ignore[misc]


@pytest.mark.parametrize(
    ("count", "level", "calculation", "publication"),
    (
        (1, SampleQualityLevel.INSUFFICIENT, True, False),
        (4, SampleQualityLevel.INSUFFICIENT, True, False),
        (5, SampleQualityLevel.PARTIAL, True, False),
        (9, SampleQualityLevel.PARTIAL, True, False),
        (10, SampleQualityLevel.ADEQUATE, True, True),
    ),
)
def test_quality_ranges_are_preserved(
    count: int, level: SampleQualityLevel, calculation: bool, publication: bool
) -> None:
    result = average(sample(tuple(float(index) for index in range(count))))
    assert result.evidence is not None
    assert result.evidence.quality.level is level
    assert result.evidence.quality.calculation_allowed is calculation
    assert result.evidence.quality.publication_allowed is publication
    assert bool(result.evidence.warnings) is (count < 10)


def test_empty_snapshot_returns_structured_block() -> None:
    result = calculate_contextual_average(sample(()))
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.SAMPLE_EMPTY


@pytest.mark.parametrize(
    ("state", "reason"),
    (
        (ObservationState.MISSING, SampleExclusionReason.MISSING_OBSERVATION),
        (ObservationState.NOT_APPLICABLE, SampleExclusionReason.NOT_APPLICABLE),
        (ObservationState.INVALID, SampleExclusionReason.INVALID_OBSERVATION),
        (ObservationState.SUSPECT, SampleExclusionReason.SUSPECT_OBSERVATION),
        (ObservationState.PENDING_REVIEW, SampleExclusionReason.PENDING_REVIEW),
    ),
)
def test_unusable_states_are_auditable_and_never_used(
    state: ObservationState, reason: SampleExclusionReason
) -> None:
    result = average(sample((2.0,), exclusions=(exclusion(0, state, reason),)))
    assert result.value == 2.0
    assert result.evidence is not None
    assert result.evidence.considered_match_ids == ("match-0", "excluded-0")
    assert result.evidence.exclusions[0].observation_state is state
    assert result.evidence.exclusions[0].reason is reason


def test_four_series_are_independent_and_canonical() -> None:
    references = tuple(
        MethodOneSeriesReference(role, sample((float(index + 1),), role=role))
        for index, role in enumerate(reversed(tuple(MethodOneSeriesRole)))
    )
    request = MethodOneRequest(
        "target",
        "home",
        "away",
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        references,
        MethodOneConfiguration("config"),
        "competition",
    )
    result = calculate_method_one_contextual_averages(request)
    assert not isinstance(result, CalculationError)
    assert tuple(item.role for item in result.values) == tuple(MethodOneSeriesRole)
    assert tuple(item.value for item in result.values) == (4.0, 3.0, 2.0, 1.0)
    assert (result.match_id, result.competition_id) == ("target", "competition")
    assert (
        failure(calculate_method_one_contextual_averages(cast(Any, object()))).code
        is ErrorCode.INCONSISTENT_DATA
    )


def test_validation_rejects_invalid_snapshot_shapes_and_values() -> None:
    assert (
        failure(calculate_contextual_average(cast(Any, object()))).code
        is ErrorCode.INCONSISTENT_DATA
    )
    unsupported = sample((1.0,))
    object.__setattr__(unsupported, "sample_schema_version", 2)
    assert (
        failure(calculate_contextual_average(unsupported)).code
        is ErrorCode.SCHEMA_VERSION_UNSUPPORTED
    )

    noncanonical = sample((1.0, 2.0))
    object.__setattr__(
        noncanonical, "observations", tuple(reversed(noncanonical.observations))
    )
    assert (
        failure(calculate_contextual_average(noncanonical)).code
        is ErrorCode.INCONSISTENT_DATA
    )

    duplicate = sample((1.0,))
    object.__setattr__(duplicate, "observations", (duplicate.observations[0],) * 2)
    assert (
        failure(calculate_contextual_average(duplicate)).code
        is ErrorCode.INCONSISTENT_DATA
    )

    overlap = sample(
        (1.0,),
        exclusions=(
            exclusion(
                1, ObservationState.MISSING, SampleExclusionReason.MISSING_OBSERVATION
            ),
        ),
    )
    object.__setattr__(
        overlap,
        "exclusions",
        (
            SampleExclusion(
                overlap.observations[0].identity, SampleExclusionReason.DUPLICATE
            ),
        ),
    )
    assert (
        failure(calculate_contextual_average(overlap)).code
        is ErrorCode.INCONSISTENT_DATA
    )

    state = sample((1.0,))
    object.__setattr__(state.observations[0].value, "state", ObservationState.MISSING)
    assert (
        failure(calculate_contextual_average(state)).code is ErrorCode.INCONSISTENT_DATA
    )

    nonfinite = sample((1.0,))
    object.__setattr__(nonfinite.observations[0].value, "value", float("nan"))
    assert (
        failure(calculate_contextual_average(nonfinite)).code
        is ErrorCode.INVALID_NUMBER
    )


def test_contextual_average_rejects_invalid_evidence() -> None:
    with pytest.raises(ValueError):
        ContextualAverage(
            "sample",
            MethodOneSeriesRole.HOME_PRODUCTION,
            1.0,
            1.0,
            1.0,
            1,
            ("match",),
            (1.0,),
            cast(Any, object()),
        )


def test_inferred_away_roles_and_invalid_inferred_context() -> None:
    assert average(sample((1.0,), role=MethodOneSeriesRole.AWAY_PRODUCTION)).role is (
        MethodOneSeriesRole.AWAY_PRODUCTION
    )
    assert average(sample((1.0,), role=MethodOneSeriesRole.AWAY_CONCESSION)).role is (
        MethodOneSeriesRole.AWAY_CONCESSION
    )
    incoherent = sample((1.0,), role=MethodOneSeriesRole.AWAY_PRODUCTION)
    object.__setattr__(incoherent.observations[0], "subject_role", ParticipantRole.HOME)
    assert (
        failure(calculate_contextual_average(incoherent)).code
        is ErrorCode.INCONSISTENT_DATA
    )


def test_count_sum_and_zero_divisor_failures_are_structured() -> None:
    inconsistent = sample((1.0,))
    object.__setattr__(inconsistent, "counts", sample(()).counts)
    assert (
        failure(calculate_contextual_average(inconsistent)).code
        is ErrorCode.INCONSISTENT_DATA
    )

    overflow = sample((1e308, 1e308))
    assert (
        failure(calculate_contextual_average(overflow)).code is ErrorCode.INVALID_NUMBER
    )

    impossible = sample(())
    object.__setattr__(impossible.quality, "calculation_allowed", True)
    assert (
        failure(calculate_contextual_average(impossible)).code
        is ErrorCode.DIVISION_BY_ZERO
    )


def test_four_series_returns_the_first_calculation_error() -> None:
    references = tuple(
        MethodOneSeriesReference(
            role,
            sample((), role=role)
            if role is MethodOneSeriesRole.HOME_PRODUCTION
            else sample((1.0,), role=role),
        )
        for role in MethodOneSeriesRole
    )
    request = MethodOneRequest(
        "target",
        "home",
        "away",
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        references,
        MethodOneConfiguration("config"),
        "competition",
    )
    assert (
        failure(calculate_method_one_contextual_averages(request)).code
        is ErrorCode.SAMPLE_EMPTY
    )
