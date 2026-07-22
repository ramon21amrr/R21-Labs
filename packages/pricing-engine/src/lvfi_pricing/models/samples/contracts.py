"""Stdlib-only, immutable contracts shared by LVFI sampling methods."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, auto
from typing import Self

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode

COMMON_CONTRACT_VERSION = "1.0.0"
_SCHEMA_VERSION = 1
_SAFE_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
type SafeScalar = None | bool | int | float | str


class StatisticCode(StrEnum):
    GOALS = auto()
    CORNERS = auto()
    SHOTS = auto()
    SHOTS_ON_TARGET = auto()
    CARDS = auto()
    FOULS = auto()


class ObservationUnit(StrEnum):
    COUNT = auto()


class MatchPeriodCode(StrEnum):
    FIRST_HALF = auto()
    REGULATION_TIME = auto()


class ParticipantRole(StrEnum):
    HOME = auto()
    AWAY = auto()


class VenueCondition(StrEnum):
    HOME = auto()
    AWAY = auto()
    OVERALL = auto()


class ObservationRole(StrEnum):
    PRODUCTION = auto()
    CONCESSION = auto()


class ObservationState(StrEnum):
    OBSERVED = auto()
    MISSING = auto()
    NOT_APPLICABLE = auto()
    INVALID = auto()
    SUSPECT = auto()
    PENDING_REVIEW = auto()


class MatchState(StrEnum):
    COMPLETED = auto()
    COMPLETED_AFTER_EXTRA_TIME = auto()
    CANCELLED = auto()
    ANNULLED = auto()
    INTERRUPTED = auto()
    WALKOVER = auto()
    PENALTY_SHOOTOUT = auto()
    PENDING_REVIEW = auto()


class SampleWindowKind(StrEnum):
    LAST_N = auto()
    FULL_SEASON = auto()
    CUSTOM_PERIOD = auto()


class SampleExclusionReason(StrEnum):
    FILTER_MISMATCH = auto()
    AFTER_CUTOFF = auto()
    WINDOW_LIMIT = auto()
    INELIGIBLE_MATCH_STATE = auto()
    EXTRA_TIME_INCLUDED = auto()
    MISSING_OBSERVATION = auto()
    NOT_APPLICABLE = auto()
    INVALID_OBSERVATION = auto()
    SUSPECT_OBSERVATION = auto()
    PENDING_REVIEW = auto()
    DUPLICATE = auto()
    INCONSISTENT_CONTEXT = auto()


class SampleQualityLevel(StrEnum):
    EMPTY = auto()
    INSUFFICIENT = auto()
    PARTIAL = auto()
    ADEQUATE = auto()


def _error(message: str, field: str | None = None) -> CalculationError:
    return CalculationError(ErrorCode.INCONSISTENT_DATA, message, field)


def _code(value: object, field: str, maximum: int = 64) -> str:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= maximum
        or not _SAFE_CODE.fullmatch(value)
    ):
        raise ValueError(f"invalid {field}")
    return value


def _time(value: object, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(f"invalid {field}")
    return value.astimezone(UTC)


def _number(value: object, field: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"invalid {field}")
    result = float(value)
    if not math.isfinite(result) or (nonnegative and result < 0):
        raise ValueError(f"invalid {field}")
    return 0.0 if result == 0 else result


def _version(value: object, field: str) -> int:
    if isinstance(value, bool) or value != _SCHEMA_VERSION:
        raise ValueError(f"unsupported {field}")
    return _SCHEMA_VERSION


def _tuple_codes(
    value: object, field: str, limit: int, enum: type[StrEnum] | None = None
) -> tuple[object, ...]:
    if not isinstance(value, tuple) or len(value) > limit:
        raise ValueError(f"invalid {field}")
    values = tuple(value)
    if enum is None:
        if any(not isinstance(item, str) for item in values):
            raise ValueError(f"invalid {field}")
        checked = tuple(_code(item, field, 128) for item in values)
    else:
        if any(not isinstance(item, enum) for item in values):
            raise ValueError(f"invalid {field}")
        checked = values
    if len(set(checked)) != len(checked):
        raise ValueError(f"duplicate {field}")
    return tuple(sorted(checked))


@dataclass(frozen=True, slots=True)
class MatchIdentity:
    match_id: str
    occurred_at: datetime
    match_state: MatchState
    regulation_segments_validated: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "match_id", _code(self.match_id, "match_id", 128))
        object.__setattr__(self, "occurred_at", _time(self.occurred_at, "occurred_at"))
        if not isinstance(self.match_state, MatchState) or not isinstance(
            self.regulation_segments_validated, bool
        ):
            raise ValueError("invalid match identity")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        try:
            return cls(**kwargs)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return _error("invalid match identity")


@dataclass(frozen=True, slots=True)
class ObservationValue:
    state: ObservationState
    value: float | None
    unit: ObservationUnit
    reason_code: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.state, ObservationState) or not isinstance(
            self.unit, ObservationUnit
        ):
            raise ValueError("invalid observation value")
        if self.state is ObservationState.OBSERVED:
            if self.reason_code is not None:
                raise ValueError("observed value has reason")
            object.__setattr__(
                self, "value", _number(self.value, "value", nonnegative=True)
            )
        else:
            if self.value is not None or self.reason_code is None:
                raise ValueError("state requires reason")
            object.__setattr__(
                self, "reason_code", _code(self.reason_code, "reason_code")
            )

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        try:
            return cls(**kwargs)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return CalculationError(
                ErrorCode.INVALID_STATISTIC, "invalid observation value"
            )


@dataclass(frozen=True, slots=True)
class MatchObservation:
    identity: MatchIdentity
    subject_id: str
    opponent_id: str
    subject_role: ParticipantRole
    venue_condition: VenueCondition
    observation_role: ObservationRole
    statistic: StatisticCode
    period: MatchPeriodCode
    value: ObservationValue
    observation_schema_version: int = 1

    def __post_init__(self) -> None:
        if (
            not isinstance(self.identity, MatchIdentity)
            or not isinstance(self.subject_role, ParticipantRole)
            or not isinstance(self.venue_condition, VenueCondition)
            or not isinstance(self.observation_role, ObservationRole)
            or not isinstance(self.statistic, StatisticCode)
            or not isinstance(self.period, MatchPeriodCode)
            or not isinstance(self.value, ObservationValue)
        ):
            raise ValueError("invalid observation")
        object.__setattr__(
            self, "subject_id", _code(self.subject_id, "subject_id", 128)
        )
        object.__setattr__(
            self, "opponent_id", _code(self.opponent_id, "opponent_id", 128)
        )
        _version(self.observation_schema_version, "observation schema")
        if self.subject_id == self.opponent_id:
            raise ValueError("equal participants")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        try:
            return cls(**kwargs)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return _error("invalid match observation")


@dataclass(frozen=True, slots=True)
class SampleFilter:
    venue_condition: VenueCondition
    window_kind: SampleWindowKind
    requested_count: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    competition_ids: tuple[str, ...] = ()
    season_ids: tuple[str, ...] = ()
    include_previous_season: bool = False
    included_match_states: tuple[MatchState, ...] = (MatchState.COMPLETED,)
    excluded_competition_type_codes: tuple[str, ...] = ()
    allow_validated_regulation_segments: bool = False
    filter_schema_version: int = 1

    def __post_init__(self) -> None:
        if (
            not isinstance(self.venue_condition, VenueCondition)
            or not isinstance(self.window_kind, SampleWindowKind)
            or not isinstance(self.include_previous_season, bool)
            or not isinstance(self.allow_validated_regulation_segments, bool)
        ):
            raise ValueError("invalid filter")
        object.__setattr__(
            self,
            "competition_ids",
            _tuple_codes(self.competition_ids, "competition_ids", 64),
        )
        object.__setattr__(
            self, "season_ids", _tuple_codes(self.season_ids, "season_ids", 32)
        )
        object.__setattr__(
            self,
            "excluded_competition_type_codes",
            _tuple_codes(
                self.excluded_competition_type_codes,
                "excluded_competition_type_codes",
                64,
            ),
        )
        object.__setattr__(
            self,
            "included_match_states",
            _tuple_codes(
                self.included_match_states, "included_match_states", 8, MatchState
            ),
        )
        _version(self.filter_schema_version, "filter schema")
        if self.starts_at is not None:
            object.__setattr__(self, "starts_at", _time(self.starts_at, "starts_at"))
        if self.ends_at is not None:
            object.__setattr__(self, "ends_at", _time(self.ends_at, "ends_at"))
        if self.window_kind is SampleWindowKind.LAST_N:
            if (
                self.requested_count not in (5, 10, 15, 20)
                or self.starts_at is not None
                or self.ends_at is not None
            ):
                raise ValueError("invalid last n filter")
        elif self.window_kind is SampleWindowKind.FULL_SEASON:
            if (
                not self.season_ids
                or self.requested_count is not None
                or self.starts_at is not None
                or self.ends_at is not None
            ):
                raise ValueError("invalid full season filter")
        elif (
            self.requested_count is not None
            or self.starts_at is None
            or self.ends_at is None
            or self.starts_at > self.ends_at
        ):
            raise ValueError("invalid custom period filter")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        try:
            return cls(**kwargs)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return _error("invalid sample filter")


@dataclass(frozen=True, slots=True)
class SampleDefinition:
    sample_id: str
    subject_id: str
    observation_role: ObservationRole
    statistic: StatisticCode
    period: MatchPeriodCode
    sample_filter: SampleFilter
    cutoff_at: datetime
    definition_schema_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "sample_id", _code(self.sample_id, "sample_id", 128))
        object.__setattr__(
            self, "subject_id", _code(self.subject_id, "subject_id", 128)
        )
        object.__setattr__(self, "cutoff_at", _time(self.cutoff_at, "cutoff_at"))
        _version(self.definition_schema_version, "definition schema")
        if (
            not isinstance(self.observation_role, ObservationRole)
            or not isinstance(self.statistic, StatisticCode)
            or not isinstance(self.period, MatchPeriodCode)
            or not isinstance(self.sample_filter, SampleFilter)
        ):
            raise ValueError("invalid definition")
        if (
            self.sample_filter.window_kind is SampleWindowKind.CUSTOM_PERIOD
            and self.sample_filter.ends_at is not None
            and self.sample_filter.ends_at > self.cutoff_at
        ):
            raise ValueError("custom period exceeds cutoff")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        try:
            return cls(**kwargs)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return _error("invalid sample definition")


_BLOCKING = frozenset(
    (
        SampleExclusionReason.DUPLICATE,
        SampleExclusionReason.INCONSISTENT_CONTEXT,
        SampleExclusionReason.PENDING_REVIEW,
    )
)


@dataclass(frozen=True, slots=True)
class SampleExclusion:
    identity: MatchIdentity
    reason: SampleExclusionReason
    observation_state: ObservationState | None = None
    field: str | None = None
    blocks_calculation: bool = False
    blocks_automatic_use: bool = False

    def __post_init__(self) -> None:
        if (
            not isinstance(self.identity, MatchIdentity)
            or not isinstance(self.reason, SampleExclusionReason)
            or (
                self.observation_state is not None
                and not isinstance(self.observation_state, ObservationState)
            )
        ):
            raise ValueError("invalid exclusion")
        if self.field is not None:
            object.__setattr__(self, "field", _code(self.field, "field"))
        block = self.reason in _BLOCKING
        object.__setattr__(self, "blocks_calculation", block)
        object.__setattr__(self, "blocks_automatic_use", block)

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        try:
            return cls(**kwargs)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return _error("invalid exclusion")


@dataclass(frozen=True, slots=True)
class DataSnapshotMetadata:
    data_version: str
    data_hash: str
    logical_source_code: str
    attributes: tuple[tuple[str, SafeScalar], ...] = ()
    metadata_schema_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "data_version", _code(self.data_version, "data_version")
        )
        object.__setattr__(self, "data_hash", _code(self.data_hash, "data_hash"))
        object.__setattr__(
            self,
            "logical_source_code",
            _code(self.logical_source_code, "logical_source_code"),
        )
        _version(self.metadata_schema_version, "metadata schema")
        if not isinstance(self.attributes, tuple) or len(self.attributes) > 16:
            raise ValueError("invalid attributes")
        checked: list[tuple[str, SafeScalar]] = []
        for item in self.attributes:
            if not isinstance(item, tuple) or len(item) != 2:
                raise ValueError("invalid attributes")
            key, value = item
            if (
                not isinstance(key, str)
                or not 1 <= len(key) <= 64
                or not _SAFE_CODE.fullmatch(key)
                or not (value is None or isinstance(value, (bool, int, float, str)))
                or (isinstance(value, float) and not math.isfinite(value))
                or (isinstance(value, str) and len(value) > 128)
            ):
                raise ValueError("invalid attributes")
            checked.append((key, 0.0 if value == 0.0 else value))
        if len({item[0] for item in checked}) != len(checked):
            raise ValueError("duplicate attributes")
        object.__setattr__(self, "attributes", tuple(sorted(checked)))

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        try:
            return cls(**kwargs)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return _error("invalid metadata")


@dataclass(frozen=True, slots=True)
class SampleCounts:
    requested_count: int | None
    found_count: int
    observed_valid_count: int
    missing_count: int
    not_applicable_count: int
    invalid_count: int
    suspect_count: int
    pending_review_count: int
    excluded_count: int

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if name == "requested_count" and value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("invalid count")
        if self.found_count != self.observed_valid_count + self.excluded_count:
            raise ValueError("counts do not reconcile")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        try:
            return cls(**kwargs)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return _error("invalid counts")


@dataclass(frozen=True, slots=True)
class SampleQuality:
    level: SampleQualityLevel
    counts: SampleCounts
    calculation_allowed: bool
    approval_allowed: bool
    publication_allowed: bool
    reason_codes: tuple[ErrorCode, ...] = ()
    warnings: tuple[CalculationWarning, ...] = ()
    errors: tuple[CalculationError, ...] = ()

    def __hash__(self) -> int:
        raise TypeError("SampleQuality is not hashable")

    def __post_init__(self) -> None:
        if (
            not isinstance(self.level, SampleQualityLevel)
            or not isinstance(self.counts, SampleCounts)
            or not all(
                isinstance(value, bool)
                for value in (
                    self.calculation_allowed,
                    self.approval_allowed,
                    self.publication_allowed,
                )
            )
            or not all(isinstance(item, ErrorCode) for item in self.reason_codes)
            or not all(isinstance(item, CalculationWarning) for item in self.warnings)
            or not all(isinstance(item, CalculationError) for item in self.errors)
        ):
            raise ValueError("invalid quality")
        object.__setattr__(self, "reason_codes", tuple(sorted(set(self.reason_codes))))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "errors", tuple(self.errors))

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        try:
            return cls(**kwargs)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return _error("invalid quality")


def _quality(
    counts: SampleCounts, exclusions: tuple[SampleExclusion, ...]
) -> SampleQuality:
    n = counts.observed_valid_count
    warnings: list[CalculationWarning] = []
    errors: list[CalculationError] = []
    codes: list[ErrorCode] = []
    if n == 0:
        level = SampleQualityLevel.EMPTY
        allowed = (False, False, False)
        errors.append(
            CalculationError(ErrorCode.SAMPLE_EMPTY, "sample has no valid observations")
        )
        codes.append(ErrorCode.SAMPLE_EMPTY)
    elif n < 5:
        level = SampleQualityLevel.INSUFFICIENT
        allowed = (True, False, False)
        warnings.append(
            CalculationWarning(ErrorCode.SAMPLE_INSUFFICIENT, "sample is insufficient")
        )
        codes.append(ErrorCode.SAMPLE_INSUFFICIENT)
    elif n < 10:
        level = SampleQualityLevel.PARTIAL
        allowed = (True, True, False)
        warnings.append(
            CalculationWarning(ErrorCode.SAMPLE_INSUFFICIENT, "sample is partial")
        )
        codes.append(ErrorCode.SAMPLE_INSUFFICIENT)
    else:
        level = SampleQualityLevel.ADEQUATE
        allowed = (True, True, True)
    if (
        counts.requested_count is not None
        and counts.found_count < counts.requested_count
        and ErrorCode.SAMPLE_INSUFFICIENT not in codes
    ):
        warnings.append(
            CalculationWarning(
                ErrorCode.SAMPLE_INSUFFICIENT, "requested sample was not found"
            )
        )
        codes.append(ErrorCode.SAMPLE_INSUFFICIENT)
    state_codes = {
        ObservationState.MISSING: ErrorCode.MISSING_STATISTIC,
        ObservationState.INVALID: ErrorCode.INVALID_STATISTIC,
        ObservationState.SUSPECT: ErrorCode.INCONSISTENT_DATA,
        ObservationState.PENDING_REVIEW: ErrorCode.INCONSISTENT_DATA,
    }
    for exclusion in exclusions:
        code = (
            state_codes.get(exclusion.observation_state)
            if exclusion.observation_state is not None
            else None
        )
        if code is not None:
            codes.append(code)
        if exclusion.blocks_calculation:
            errors.append(
                CalculationError(
                    ErrorCode.INCONSISTENT_DATA, "sample contains blocking exclusion"
                )
            )
            codes.append(ErrorCode.INCONSISTENT_DATA)
    return SampleQuality(
        level,
        counts,
        *allowed,
        tuple(sorted(set(codes))),
        tuple(warnings),
        tuple(errors),
    )


@dataclass(frozen=True, slots=True)
class SampleSnapshot:
    definition: SampleDefinition
    data_metadata: DataSnapshotMetadata
    observations: tuple[MatchObservation, ...]
    exclusions: tuple[SampleExclusion, ...]
    counts: SampleCounts
    quality: SampleQuality
    common_contract_version: str = COMMON_CONTRACT_VERSION
    sample_schema_version: int = 1

    def __hash__(self) -> int:
        raise TypeError("SampleSnapshot is not hashable")

    def __post_init__(self) -> None:
        if (
            not isinstance(self.definition, SampleDefinition)
            or not isinstance(self.data_metadata, DataSnapshotMetadata)
            or not isinstance(self.observations, tuple)
            or not isinstance(self.exclusions, tuple)
            or not isinstance(self.counts, SampleCounts)
            or not isinstance(self.quality, SampleQuality)
        ):
            raise ValueError("invalid snapshot")
        if self.common_contract_version != COMMON_CONTRACT_VERSION:
            raise ValueError("unsupported common contract version")
        _version(self.sample_schema_version, "sample schema")
        if (
            len(self.observations) + len(self.exclusions) > 1000
            or any(
                not isinstance(item, MatchObservation)
                or item.value.state is not ObservationState.OBSERVED
                for item in self.observations
            )
            or any(not isinstance(item, SampleExclusion) for item in self.exclusions)
        ):
            raise ValueError("invalid snapshot members")
        observations = tuple(
            sorted(
                self.observations,
                key=lambda item: (
                    -item.identity.occurred_at.timestamp(),
                    item.identity.match_id,
                ),
            )
        )
        exclusions = tuple(
            sorted(
                self.exclusions,
                key=lambda item: (
                    -item.identity.occurred_at.timestamp(),
                    item.identity.match_id,
                    item.reason,
                ),
            )
        )
        keys = set()
        for item in observations:
            duplicate_key = (
                item.identity.match_id,
                item.subject_id,
                item.statistic,
                item.period,
                item.observation_role,
                item.venue_condition,
            )
            if duplicate_key in keys:
                raise ValueError("duplicate observation")
            keys.add(duplicate_key)
        context: dict[
            tuple[str, str, StatisticCode, MatchPeriodCode, ObservationRole],
            VenueCondition,
        ] = {}
        for item in observations:
            context_key = (
                item.identity.match_id,
                item.subject_id,
                item.statistic,
                item.period,
                item.observation_role,
            )
            if (
                context_key in context
                and context[context_key] is not item.venue_condition
            ):
                raise ValueError("inconsistent context")
            context[context_key] = item.venue_condition
        derived = SampleCounts(
            self.counts.requested_count,
            len(observations) + len(exclusions),
            len(observations),
            sum(
                item.observation_state is ObservationState.MISSING
                for item in exclusions
            ),
            sum(
                item.observation_state is ObservationState.NOT_APPLICABLE
                for item in exclusions
            ),
            sum(
                item.observation_state is ObservationState.INVALID
                for item in exclusions
            ),
            sum(
                item.observation_state is ObservationState.SUSPECT
                for item in exclusions
            ),
            sum(
                item.observation_state is ObservationState.PENDING_REVIEW
                for item in exclusions
            ),
            len(exclusions),
        )
        if derived != self.counts or self.quality.counts != self.counts:
            raise ValueError("snapshot counts do not reconcile")
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "exclusions", exclusions)

    @property
    def included_match_ids(self) -> tuple[str, ...]:
        return tuple(item.identity.match_id for item in self.observations)

    @property
    def excluded_match_ids(self) -> tuple[str, ...]:
        return tuple(item.identity.match_id for item in self.exclusions)

    @property
    def considered_match_ids(self) -> tuple[str, ...]:
        return self.included_match_ids + self.excluded_match_ids

    @classmethod
    def create(
        cls,
        *,
        definition: SampleDefinition,
        data_metadata: DataSnapshotMetadata,
        observations: tuple[MatchObservation, ...],
        exclusions: tuple[SampleExclusion, ...],
        common_contract_version: object = COMMON_CONTRACT_VERSION,
        sample_schema_version: object = _SCHEMA_VERSION,
    ) -> Self | CalculationError:
        try:
            if (
                not isinstance(common_contract_version, str)
                or isinstance(sample_schema_version, bool)
                or not isinstance(sample_schema_version, int)
            ):
                raise ValueError("invalid snapshot version")
            ordered_observations = tuple(observations)
            ordered_exclusions = tuple(exclusions)
            if any(
                not isinstance(item, MatchObservation) for item in ordered_observations
            ) or any(
                not isinstance(item, SampleExclusion) for item in ordered_exclusions
            ):
                raise ValueError("invalid snapshot members")
            counts = SampleCounts(
                definition.sample_filter.requested_count,
                len(ordered_observations) + len(ordered_exclusions),
                len(ordered_observations),
                sum(
                    item.observation_state is ObservationState.MISSING
                    for item in ordered_exclusions
                ),
                sum(
                    item.observation_state is ObservationState.NOT_APPLICABLE
                    for item in ordered_exclusions
                ),
                sum(
                    item.observation_state is ObservationState.INVALID
                    for item in ordered_exclusions
                ),
                sum(
                    item.observation_state is ObservationState.SUSPECT
                    for item in ordered_exclusions
                ),
                sum(
                    item.observation_state is ObservationState.PENDING_REVIEW
                    for item in ordered_exclusions
                ),
                len(ordered_exclusions),
            )
            quality = _quality(counts, ordered_exclusions)
            return cls(
                definition,
                data_metadata,
                ordered_observations,
                ordered_exclusions,
                counts,
                quality,
                common_contract_version,
                sample_schema_version,
            )
        except (TypeError, ValueError):
            return _error("invalid sample snapshot")
