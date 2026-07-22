# ruff: noqa: F403, F405
from datetime import UTC, datetime
from typing import Any, cast

import pytest

from lvfi_pricing.core import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.models.samples import *  # noqa: F403
from lvfi_pricing.models.samples import __all__ as public_api


def at(hour: int = 0) -> datetime:
    return datetime(2026, 1, 1, hour, tzinfo=UTC)


def identity(match_id: str = "match-1") -> MatchIdentity:  # noqa: F405
    return MatchIdentity(match_id, at(), MatchState.COMPLETED)  # noqa: F405


def observation(match_id: str = "match-1") -> MatchObservation:  # noqa: F405
    return MatchObservation(  # noqa: F405
        identity(match_id),
        "subject",
        "opponent",
        ParticipantRole.HOME,  # noqa: F405
        VenueCondition.HOME,
        ObservationRole.PRODUCTION,
        StatisticCode.GOALS,  # noqa: F405
        MatchPeriodCode.REGULATION_TIME,
        ObservationValue(ObservationState.OBSERVED, 0, ObservationUnit.COUNT),  # noqa: F405
    )


def definition() -> SampleDefinition:  # noqa: F405
    return SampleDefinition(
        "sample-1",
        "subject",
        ObservationRole.PRODUCTION,
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        SampleFilter(VenueCondition.HOME, SampleWindowKind.LAST_N, 5),
        at(2),
    )  # noqa: F405


def metadata() -> DataSnapshotMetadata:  # noqa: F405
    return DataSnapshotMetadata("v1", "abc", "source", (("key", "value"),))  # noqa: F405


def test_exact_public_api_and_no_root_aliases() -> None:
    assert public_api == (
        "StatisticCode",
        "ObservationUnit",
        "MatchPeriodCode",
        "ParticipantRole",
        "VenueCondition",
        "ObservationRole",
        "ObservationState",
        "MatchState",
        "SampleWindowKind",
        "SampleExclusionReason",
        "SampleQualityLevel",
        "MatchIdentity",
        "ObservationValue",
        "MatchObservation",
        "SampleFilter",
        "SampleDefinition",
        "SampleExclusion",
        "DataSnapshotMetadata",
        "SampleCounts",
        "SampleQuality",
        "SampleSnapshot",
    )
    import lvfi_pricing

    assert lvfi_pricing.__all__ == ()


def test_observation_value_rules_and_utc_normalization() -> None:
    assert (
        ObservationValue(ObservationState.OBSERVED, -0.0, ObservationUnit.COUNT).value
        == 0.0
    )  # noqa: F405
    assert (
        MatchIdentity(
            "m",
            datetime(2026, 1, 1, 3, tzinfo=UTC).astimezone(UTC),
            MatchState.COMPLETED,
        ).occurred_at.tzinfo
        is UTC
    )  # noqa: F405
    for value in (True, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            ObservationValue(ObservationState.OBSERVED, value, ObservationUnit.COUNT)  # noqa: F405
    with pytest.raises(ValueError):
        ObservationValue(ObservationState.MISSING, 1, ObservationUnit.COUNT, "why")  # noqa: F405
    assert isinstance(
        ObservationValue.create(
            state=ObservationState.MISSING, value=None, unit=ObservationUnit.COUNT
        ),
        CalculationError,
    )  # noqa: F405


def test_filters_and_metadata_are_immutable_and_canonical() -> None:
    sample_filter = SampleFilter(
        VenueCondition.OVERALL, SampleWindowKind.FULL_SEASON, season_ids=("b", "a")
    )  # noqa: F405
    assert sample_filter.season_ids == ("a", "b")
    custom = SampleFilter(
        VenueCondition.HOME,
        SampleWindowKind.CUSTOM_PERIOD,
        starts_at=at(),
        ends_at=at(1),
    )  # noqa: F405
    assert custom.ends_at == at(1)
    with pytest.raises(ValueError):
        SampleFilter(VenueCondition.HOME, SampleWindowKind.LAST_N, 6)  # noqa: F405
    with pytest.raises(ValueError):
        DataSnapshotMetadata("v", "h", "s", (("x", []),))  # type: ignore[arg-type] # noqa: F405


def test_snapshot_derives_counts_quality_and_order() -> None:
    excluded = SampleExclusion(
        identity("match-2"),
        SampleExclusionReason.MISSING_OBSERVATION,
        ObservationState.MISSING,
    )  # noqa: F405
    snapshot = SampleSnapshot.create(
        definition=definition(),
        data_metadata=metadata(),
        observations=(observation(),),
        exclusions=(excluded,),
    )  # noqa: F405
    assert isinstance(snapshot, SampleSnapshot)  # noqa: F405
    assert snapshot.counts.found_count == 2
    assert snapshot.quality.level is SampleQualityLevel.INSUFFICIENT  # noqa: F405
    assert snapshot.included_match_ids == ("match-1",)
    assert snapshot.excluded_match_ids == ("match-2",)
    with pytest.raises(TypeError):
        hash(snapshot)


def test_limit_duplicate_and_context_errors() -> None:
    many = tuple(observation(f"m-{index}") for index in range(1001))
    assert isinstance(
        SampleSnapshot.create(
            definition=definition(),
            data_metadata=metadata(),
            observations=many,
            exclusions=(),
        ),
        CalculationError,
    )  # noqa: F405
    duplicate = (observation(), observation())
    assert isinstance(
        SampleSnapshot.create(
            definition=definition(),
            data_metadata=metadata(),
            observations=duplicate,
            exclusions=(),
        ),
        CalculationError,
    )  # noqa: F405
    assert SampleExclusion(
        identity(), SampleExclusionReason.DUPLICATE
    ).blocks_calculation  # noqa: F405


def observation_kwargs() -> dict[str, object]:
    return {
        "identity": identity(),
        "subject_id": "subject",
        "opponent_id": "opponent",
        "subject_role": ParticipantRole.HOME,
        "venue_condition": VenueCondition.HOME,
        "observation_role": ObservationRole.PRODUCTION,
        "statistic": StatisticCode.GOALS,
        "period": MatchPeriodCode.REGULATION_TIME,
        "value": ObservationValue(ObservationState.OBSERVED, 1, ObservationUnit.COUNT),
    }


def count_contract(observed: int, requested: int | None = None) -> SampleCounts:
    return SampleCounts(requested, observed, observed, 0, 0, 0, 0, 0, 0)


def observations(count: int) -> tuple[MatchObservation, ...]:
    return tuple(observation(f"match-{index}") for index in range(count))


def snapshot_for_count(count: int, requested: int) -> SampleSnapshot:
    source_definition = SampleDefinition(
        "sample-quality",
        "subject",
        ObservationRole.PRODUCTION,
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        SampleFilter(VenueCondition.HOME, SampleWindowKind.LAST_N, requested),
        at(2),
    )
    result = SampleSnapshot.create(
        definition=source_definition,
        data_metadata=metadata(),
        observations=observations(count),
        exclusions=(),
    )
    assert isinstance(result, SampleSnapshot)
    return result


def test_identity_and_observation_factories_cover_validation_contracts() -> None:
    assert isinstance(
        MatchIdentity.create(
            match_id="valid", occurred_at=at(), match_state=MatchState.COMPLETED
        ),
        MatchIdentity,
    )
    invalid_identities = (
        {"match_id": "", "occurred_at": at(), "match_state": MatchState.COMPLETED},
        {
            "match_id": "valid",
            "occurred_at": datetime(2026, 1, 1),
            "match_state": MatchState.COMPLETED,
        },
        {"match_id": "valid", "occurred_at": at(), "match_state": object()},
        {
            "match_id": "valid",
            "occurred_at": at(),
            "match_state": MatchState.COMPLETED,
            "regulation_segments_validated": 1,
        },
    )
    for identity_args in invalid_identities:
        assert isinstance(MatchIdentity.create(**identity_args), CalculationError)

    base_value = {
        "state": ObservationState.OBSERVED,
        "value": 1,
        "unit": ObservationUnit.COUNT,
    }
    invalid_values = (
        {**base_value, "state": object()},
        {**base_value, "unit": object()},
        {**base_value, "reason_code": "unexpected"},
        {
            "state": ObservationState.MISSING,
            "value": None,
            "unit": ObservationUnit.COUNT,
            "reason_code": "bad reason",
        },
    )
    for value_args in invalid_values:
        assert isinstance(ObservationValue.create(**value_args), CalculationError)

    assert isinstance(MatchObservation.create(**observation_kwargs()), MatchObservation)
    invalid_observations = []
    for field, value in (
        ("identity", object()),
        ("subject_role", object()),
        ("venue_condition", object()),
        ("observation_role", object()),
        ("statistic", object()),
        ("period", object()),
        ("value", object()),
        ("observation_schema_version", 2),
    ):
        kwargs = observation_kwargs()
        kwargs[field] = value
        invalid_observations.append(kwargs)
    equal = observation_kwargs()
    equal["opponent_id"] = "subject"
    invalid_observations.append(equal)
    for observation_args in invalid_observations:
        assert isinstance(MatchObservation.create(**observation_args), CalculationError)


@pytest.mark.parametrize(
    "kwargs",
    (
        {
            "venue_condition": object(),
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": object(),
            "requested_count": 5,
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "include_previous_season": 1,
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "allow_validated_regulation_segments": 1,
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "competition_ids": ["league"],
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "competition_ids": tuple(f"c-{index}" for index in range(65)),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "competition_ids": (1,),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "competition_ids": ("bad code",),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "competition_ids": ("same", "same"),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "included_match_states": ("completed",),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "included_match_states": (MatchState.COMPLETED, MatchState.COMPLETED),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "filter_schema_version": False,
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "starts_at": datetime(2026, 1, 1),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": None,
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "starts_at": at(),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.LAST_N,
            "requested_count": 5,
            "ends_at": at(),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.FULL_SEASON,
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.FULL_SEASON,
            "season_ids": ("season",),
            "requested_count": 5,
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.FULL_SEASON,
            "season_ids": ("season",),
            "starts_at": at(),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.FULL_SEASON,
            "season_ids": ("season",),
            "ends_at": at(),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.CUSTOM_PERIOD,
            "requested_count": 5,
            "starts_at": at(),
            "ends_at": at(1),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.CUSTOM_PERIOD,
            "ends_at": at(1),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.CUSTOM_PERIOD,
            "starts_at": at(),
        },
        {
            "venue_condition": VenueCondition.HOME,
            "window_kind": SampleWindowKind.CUSTOM_PERIOD,
            "starts_at": at(1),
            "ends_at": at(),
        },
    ),
)
def test_filter_factory_rejects_every_invalid_shape(kwargs: dict[str, object]) -> None:
    assert isinstance(SampleFilter.create(**kwargs), CalculationError)


def test_filter_valid_optional_fields_are_canonical() -> None:
    result = SampleFilter.create(
        venue_condition=VenueCondition.OVERALL,
        window_kind=SampleWindowKind.FULL_SEASON,
        season_ids=("season-b", "season-a"),
        competition_ids=("league-b", "league-a"),
        include_previous_season=True,
        included_match_states=(
            MatchState.COMPLETED_AFTER_EXTRA_TIME,
            MatchState.COMPLETED,
        ),
        excluded_competition_type_codes=("friendly",),
        allow_validated_regulation_segments=True,
    )
    assert isinstance(result, SampleFilter)
    assert result.competition_ids == ("league-a", "league-b")


def test_definition_exclusion_and_metadata_factories_validate_all_fields() -> None:
    base_definition: dict[str, object] = {
        "sample_id": "sample",
        "subject_id": "subject",
        "observation_role": ObservationRole.PRODUCTION,
        "statistic": StatisticCode.GOALS,
        "period": MatchPeriodCode.REGULATION_TIME,
        "sample_filter": SampleFilter(VenueCondition.HOME, SampleWindowKind.LAST_N, 5),
        "cutoff_at": at(2),
    }
    assert isinstance(SampleDefinition.create(**base_definition), SampleDefinition)
    for field, value in (
        ("sample_id", ""),
        ("subject_id", "bad id"),
        ("observation_role", object()),
        ("statistic", object()),
        ("period", object()),
        ("sample_filter", object()),
        ("cutoff_at", datetime(2026, 1, 1)),
        ("definition_schema_version", 2),
    ):
        definition_args = dict(base_definition)
        definition_args[field] = value
        assert isinstance(SampleDefinition.create(**definition_args), CalculationError)
    custom = dict(base_definition)
    custom["sample_filter"] = SampleFilter(
        VenueCondition.HOME,
        SampleWindowKind.CUSTOM_PERIOD,
        starts_at=at(),
        ends_at=at(2),
    )
    custom["cutoff_at"] = at(1)
    assert isinstance(SampleDefinition.create(**custom), CalculationError)

    valid_exclusion = SampleExclusion.create(
        identity=identity(),
        reason=SampleExclusionReason.FILTER_MISMATCH,
        field="statistic",
    )
    assert isinstance(valid_exclusion, SampleExclusion)
    assert not valid_exclusion.blocks_calculation
    invalid_exclusions = (
        {"identity": object(), "reason": SampleExclusionReason.FILTER_MISMATCH},
        {"identity": identity(), "reason": object()},
        {
            "identity": identity(),
            "reason": SampleExclusionReason.FILTER_MISMATCH,
            "observation_state": object(),
        },
        {
            "identity": identity(),
            "reason": SampleExclusionReason.FILTER_MISMATCH,
            "field": "bad field",
        },
    )
    for kwargs in invalid_exclusions:
        assert isinstance(SampleExclusion.create(**kwargs), CalculationError)

    valid_metadata = DataSnapshotMetadata(
        "v1", "hash", "source", (("z", -0.0), ("a", None), ("b", True))
    )
    assert valid_metadata.attributes == (("a", None), ("b", True), ("z", 0.0))
    invalid_attributes: tuple[object, ...] = (
        [],
        tuple((f"k{index}", index) for index in range(17)),
        ("not-a-pair",),
        (("a", 1, 2),),
        ((1, "value"),),
        (("", "value"),),
        (("bad key", "value"),),
        (("key", object()),),
        (("key", float("nan")),),
        (("key", "x" * 129),),
        (("key", 1), ("key", 2)),
    )
    for attributes in invalid_attributes:
        assert isinstance(
            DataSnapshotMetadata.create(
                data_version="v1",
                data_hash="hash",
                logical_source_code="source",
                attributes=attributes,
            ),
            CalculationError,
        )
    for field, value in (
        ("data_version", ""),
        ("data_hash", "bad hash"),
        ("logical_source_code", ""),
        ("metadata_schema_version", 2),
    ):
        metadata_args: dict[str, object] = {
            "data_version": "v1",
            "data_hash": "hash",
            "logical_source_code": "source",
        }
        metadata_args[field] = value
        assert isinstance(
            DataSnapshotMetadata.create(**metadata_args), CalculationError
        )


def counts_kwargs() -> dict[str, object]:
    return {
        "requested_count": None,
        "found_count": 0,
        "observed_valid_count": 0,
        "missing_count": 0,
        "not_applicable_count": 0,
        "invalid_count": 0,
        "suspect_count": 0,
        "pending_review_count": 0,
        "excluded_count": 0,
    }


def test_counts_and_quality_factories_reject_invalid_contracts() -> None:
    assert isinstance(SampleCounts.create(**counts_kwargs()), SampleCounts)
    for field, value in (
        ("requested_count", True),
        ("found_count", 1.0),
        ("missing_count", -1),
    ):
        kwargs = counts_kwargs()
        kwargs[field] = value
        assert isinstance(SampleCounts.create(**kwargs), CalculationError)
    inconsistent = counts_kwargs()
    inconsistent["found_count"] = 1
    assert isinstance(SampleCounts.create(**inconsistent), CalculationError)

    counts = count_contract(0)
    base: dict[str, object] = {
        "level": SampleQualityLevel.EMPTY,
        "counts": counts,
        "calculation_allowed": False,
        "approval_allowed": False,
        "publication_allowed": False,
    }
    quality = SampleQuality.create(**base)
    assert isinstance(quality, SampleQuality)
    with pytest.raises(TypeError):
        hash(quality)
    invalid_quality = (
        ("level", object()),
        ("counts", object()),
        ("calculation_allowed", 0),
        ("approval_allowed", 0),
        ("publication_allowed", 0),
        ("reason_codes", (object(),)),
        ("warnings", (object(),)),
        ("errors", (object(),)),
    )
    for quality_field, quality_value in invalid_quality:
        quality_args = dict(base)
        quality_args[quality_field] = quality_value
        assert isinstance(SampleQuality.create(**quality_args), CalculationError)
    warning = CalculationWarning(ErrorCode.SAMPLE_INSUFFICIENT, "warning")
    error = CalculationError(ErrorCode.SAMPLE_EMPTY, "error")
    canonical = SampleQuality(
        SampleQualityLevel.EMPTY,
        counts,
        False,
        False,
        False,
        (ErrorCode.SAMPLE_EMPTY, ErrorCode.SAMPLE_EMPTY),
        (warning,),
        (error,),
    )
    assert canonical.reason_codes == (ErrorCode.SAMPLE_EMPTY,)


def test_quality_levels_requested_shortfall_and_exclusion_codes() -> None:
    empty = snapshot_for_count(0, 5)
    insufficient = snapshot_for_count(1, 5)
    partial = snapshot_for_count(5, 5)
    adequate = snapshot_for_count(10, 10)
    shortfall = snapshot_for_count(10, 15)
    assert empty.quality.level is SampleQualityLevel.EMPTY
    assert insufficient.quality.level is SampleQualityLevel.INSUFFICIENT
    assert partial.quality.level is SampleQualityLevel.PARTIAL
    assert adequate.quality.level is SampleQualityLevel.ADEQUATE
    assert shortfall.quality.reason_codes == (ErrorCode.SAMPLE_INSUFFICIENT,)

    states = (
        (ObservationState.MISSING, SampleExclusionReason.MISSING_OBSERVATION),
        (ObservationState.NOT_APPLICABLE, SampleExclusionReason.NOT_APPLICABLE),
        (ObservationState.INVALID, SampleExclusionReason.INVALID_OBSERVATION),
        (ObservationState.SUSPECT, SampleExclusionReason.SUSPECT_OBSERVATION),
        (ObservationState.PENDING_REVIEW, SampleExclusionReason.PENDING_REVIEW),
    )
    exclusions = tuple(
        SampleExclusion(identity(f"excluded-{index}"), reason, state)
        for index, (state, reason) in enumerate(states)
    ) + (SampleExclusion(identity("duplicate"), SampleExclusionReason.DUPLICATE),)
    result = SampleSnapshot.create(
        definition=definition(),
        data_metadata=metadata(),
        observations=(),
        exclusions=exclusions,
    )
    assert isinstance(result, SampleSnapshot)
    assert ErrorCode.MISSING_STATISTIC in result.quality.reason_codes
    assert ErrorCode.INVALID_STATISTIC in result.quality.reason_codes
    assert ErrorCode.INCONSISTENT_DATA in result.quality.reason_codes
    assert result.quality.errors


def test_snapshot_member_versions_context_counts_and_order_are_enforced() -> None:
    bad_version_values = (
        {"common_contract_version": object()},
        {"common_contract_version": "2.0.0"},
        {"sample_schema_version": True},
        {"sample_schema_version": "1"},
        {"sample_schema_version": 2},
    )
    for changes in bad_version_values:
        result = SampleSnapshot.create(
            definition=definition(),
            data_metadata=metadata(),
            observations=(),
            exclusions=(),
            **changes,
        )
        assert isinstance(result, CalculationError)

    for members in ((cast(Any, object()),),):
        assert isinstance(
            SampleSnapshot.create(
                definition=definition(),
                data_metadata=metadata(),
                observations=members,
                exclusions=(),
            ),
            CalculationError,
        )
        assert isinstance(
            SampleSnapshot.create(
                definition=definition(),
                data_metadata=metadata(),
                observations=(),
                exclusions=members,
            ),
            CalculationError,
        )
    non_observed = MatchObservation(
        identity("missing"),
        "subject",
        "opponent",
        ParticipantRole.HOME,
        VenueCondition.HOME,
        ObservationRole.PRODUCTION,
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        ObservationValue(
            ObservationState.MISSING, None, ObservationUnit.COUNT, "missing"
        ),
    )
    assert isinstance(
        SampleSnapshot.create(
            definition=definition(),
            data_metadata=metadata(),
            observations=(non_observed,),
            exclusions=(),
        ),
        CalculationError,
    )

    home = observation("same-context")
    away = MatchObservation(
        home.identity,
        home.subject_id,
        home.opponent_id,
        home.subject_role,
        VenueCondition.AWAY,
        home.observation_role,
        home.statistic,
        home.period,
        home.value,
    )
    assert isinstance(
        SampleSnapshot.create(
            definition=definition(),
            data_metadata=metadata(),
            observations=(home, away),
            exclusions=(),
        ),
        CalculationError,
    )

    valid_counts = count_contract(1, 5)
    valid_quality = SampleQuality(
        SampleQualityLevel.INSUFFICIENT,
        valid_counts,
        True,
        False,
        False,
    )
    with pytest.raises(ValueError):
        SampleSnapshot(
            definition(),
            metadata(),
            (observation(),),
            (),
            count_contract(0, 5),
            valid_quality,
        )
    other_counts = count_contract(1)
    other_quality = SampleQuality(
        SampleQualityLevel.INSUFFICIENT,
        other_counts,
        True,
        False,
        False,
    )
    with pytest.raises(ValueError):
        SampleSnapshot(
            definition(),
            metadata(),
            (observation(),),
            (),
            valid_counts,
            other_quality,
        )

    later = MatchObservation(
        identity("later"),
        "subject",
        "opponent",
        ParticipantRole.HOME,
        VenueCondition.HOME,
        ObservationRole.PRODUCTION,
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        ObservationValue(ObservationState.OBSERVED, 1, ObservationUnit.COUNT),
    )
    result = SampleSnapshot.create(
        definition=definition(),
        data_metadata=metadata(),
        observations=(later, observation("earlier")),
        exclusions=(),
    )
    assert isinstance(result, SampleSnapshot)
    assert result.considered_match_ids == ("earlier", "later")


def test_snapshot_constructor_rejects_each_top_level_type() -> None:
    counts = count_contract(0)
    quality = SampleQuality(SampleQualityLevel.EMPTY, counts, False, False, False)
    base: dict[str, Any] = {
        "definition": definition(),
        "data_metadata": metadata(),
        "observations": (),
        "exclusions": (),
        "counts": counts,
        "quality": quality,
    }
    for field in base:
        kwargs = dict(base)
        kwargs[field] = object()
        with pytest.raises((TypeError, ValueError)):
            SampleSnapshot(**kwargs)
