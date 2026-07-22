"""Pure calculation of Method One uniform contextual averages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from lvfi_pricing.core import CalculationError, ErrorCode, stable_sum, validate_finite
from lvfi_pricing.models.samples import (
    MatchObservation,
    ObservationRole,
    ObservationState,
    ParticipantRole,
    SampleSnapshot,
    VenueCondition,
)
from lvfi_pricing.models.samples.contracts import COMMON_CONTRACT_VERSION

from .contracts import (
    ContextualAverage,
    ContextualAverageEvidence,
    MethodOneRequest,
    MethodOneSeriesRole,
    RecencyPolicyCode,
)


@dataclass(frozen=True, slots=True)
class MethodOneContextualAverages:
    """The four independently calculated contextual averages of one request."""

    home_production: ContextualAverage
    home_concession: ContextualAverage
    away_production: ContextualAverage
    away_concession: ContextualAverage

    @property
    def values(self) -> tuple[ContextualAverage, ...]:
        return (
            self.home_production,
            self.home_concession,
            self.away_production,
            self.away_concession,
        )


def _error(code: ErrorCode, message: str, field: str) -> CalculationError:
    return CalculationError(code, message, field)


def _canonical(
    observations: tuple[MatchObservation, ...],
) -> tuple[MatchObservation, ...]:
    return tuple(
        sorted(
            observations,
            key=lambda item: (
                -item.identity.occurred_at.timestamp(),
                item.identity.match_id,
            ),
        )
    )


def _infer_role(snapshot: SampleSnapshot) -> MethodOneSeriesRole | None:
    observation = snapshot.observations[0]
    if (
        observation.subject_role is ParticipantRole.HOME
        and observation.venue_condition is VenueCondition.HOME
    ):
        return (
            MethodOneSeriesRole.HOME_PRODUCTION
            if observation.observation_role is ObservationRole.PRODUCTION
            else MethodOneSeriesRole.HOME_CONCESSION
        )
    if (
        observation.subject_role is ParticipantRole.AWAY
        and observation.venue_condition is VenueCondition.AWAY
    ):
        return (
            MethodOneSeriesRole.AWAY_PRODUCTION
            if observation.observation_role is ObservationRole.PRODUCTION
            else MethodOneSeriesRole.AWAY_CONCESSION
        )
    return None


def _validate_snapshot(snapshot: object) -> CalculationError | None:
    if not isinstance(snapshot, SampleSnapshot):
        return _error(
            ErrorCode.INCONSISTENT_DATA, "invalid sample snapshot", "snapshot"
        )
    if (
        snapshot.common_contract_version != COMMON_CONTRACT_VERSION
        or snapshot.sample_schema_version != 1
    ):
        return _error(
            ErrorCode.SCHEMA_VERSION_UNSUPPORTED,
            "unsupported sample contract or schema",
            "snapshot",
        )
    observations = snapshot.observations
    exclusions = snapshot.exclusions
    if observations != _canonical(observations):
        return _error(
            ErrorCode.INCONSISTENT_DATA,
            "observations are not canonical",
            "observations",
        )
    used_ids = tuple(item.identity.match_id for item in observations)
    excluded_ids = tuple(item.identity.match_id for item in exclusions)
    if len(set(used_ids)) != len(used_ids):
        return _error(
            ErrorCode.INCONSISTENT_DATA, "duplicate used match id", "observations"
        )
    if set(used_ids) & set(excluded_ids):
        return _error(
            ErrorCode.INCONSISTENT_DATA,
            "match id is both used and excluded",
            "snapshot",
        )
    counts = snapshot.counts
    if (
        counts.found_count != len(observations) + len(exclusions)
        or counts.observed_valid_count != len(observations)
        or counts.excluded_count != len(exclusions)
        or snapshot.quality.counts != counts
    ):
        return _error(
            ErrorCode.INCONSISTENT_DATA, "snapshot counts do not reconcile", "counts"
        )
    definition = snapshot.definition
    for observation in observations:
        if (
            observation.value.state is not ObservationState.OBSERVED
            or observation.value.value is None
            or observation.statistic is not definition.statistic
            or observation.period is not definition.period
            or observation.observation_role is not definition.observation_role
            or observation.venue_condition
            is not definition.sample_filter.venue_condition
            or observation.subject_id != definition.subject_id
        ):
            return _error(
                ErrorCode.INCONSISTENT_DATA,
                "inconsistent usable observation",
                "observations",
            )
        if (
            error := validate_finite(observation.value.value, field="observations")
        ) is not None:
            return error
    return None


def calculate_contextual_average(
    snapshot: SampleSnapshot,
    *,
    role: MethodOneSeriesRole | None = None,
) -> ContextualAverage | CalculationError:
    """Calculate one deterministic `uniform/v1` mean without mutating the snapshot."""
    if (error := _validate_snapshot(snapshot)) is not None:
        return error
    if not snapshot.quality.calculation_allowed:
        return next(
            iter(snapshot.quality.errors),
            _error(
                ErrorCode.SAMPLE_EMPTY, "sample has no valid observations", "snapshot"
            ),
        )
    observations = snapshot.observations
    values = tuple(float(cast(float, item.value.value)) for item in observations)
    numerator = stable_sum(values)
    if isinstance(numerator, CalculationError):
        return numerator
    denominator = float(len(values))
    if denominator == 0.0:
        return _error(
            ErrorCode.DIVISION_BY_ZERO, "average divisor is zero", "observations"
        )
    value = numerator / denominator
    average_role = _infer_role(snapshot) if role is None else role
    if average_role is None:
        return _error(ErrorCode.INCONSISTENT_DATA, "series role is incoherent", "role")
    definition = snapshot.definition
    evidence = ContextualAverageEvidence(
        snapshot.considered_match_ids,
        snapshot.exclusions,
        snapshot.quality,
        definition.statistic,
        definition.period,
        definition.subject_id,
        tuple(item.opponent_id for item in observations),
        definition.sample_filter.venue_condition,
        snapshot.common_contract_version,
        RecencyPolicyCode.UNIFORM_V1,
        "math.fsum/uniform/v1",
        True,
        values,
        snapshot.quality.warnings,
        snapshot.quality.errors,
    )
    return ContextualAverage(
        definition.sample_id,
        average_role,
        value,
        numerator,
        denominator,
        len(values),
        snapshot.included_match_ids,
        tuple(1.0 for _ in values),
        evidence,
    )


def calculate_method_one_contextual_averages(
    request: MethodOneRequest,
) -> MethodOneContextualAverages | CalculationError:
    """Calculate the four required averages independently, with no rate combination."""
    if not isinstance(request, MethodOneRequest):
        return _error(
            ErrorCode.INCONSISTENT_DATA, "invalid method one request", "request"
        )
    calculated: dict[MethodOneSeriesRole, ContextualAverage] = {}
    for reference in request.series_references:
        result = calculate_contextual_average(reference.snapshot, role=reference.role)
        if isinstance(result, CalculationError):
            return result
        calculated[reference.role] = result
    return MethodOneContextualAverages(
        calculated[MethodOneSeriesRole.HOME_PRODUCTION],
        calculated[MethodOneSeriesRole.HOME_CONCESSION],
        calculated[MethodOneSeriesRole.AWAY_PRODUCTION],
        calculated[MethodOneSeriesRole.AWAY_CONCESSION],
    )
