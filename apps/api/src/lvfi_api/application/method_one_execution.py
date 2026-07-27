"""Application orchestration for one deterministic Method One execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, time
from typing import Protocol

from lvfi_pricing.models.method_one import (
    MethodOneConfiguration,
    MethodOneFinalResult,
    MethodOnePayload,
    MethodOneRequest,
    MethodOneSeriesReference,
    MethodOneSeriesRole,
)
from lvfi_pricing.models.samples import (
    DataSnapshotMetadata,
    MatchIdentity,
    MatchObservation,
    MatchPeriodCode,
    MatchState,
    ObservationRole,
    ObservationState,
    ObservationUnit,
    ObservationValue,
    ParticipantRole,
    SampleDefinition,
    SampleFilter,
    SampleSnapshot,
    SampleWindowKind,
    StatisticCode,
    VenueCondition,
)

from lvfi_api.domain.errors import (
    MethodOneEngineError,
    MethodOneSampleIncompleteError,
    MethodOneSampleInvalidError,
)
from lvfi_api.domain.historical_queries import (
    Match,
    MethodOneSample,
    MethodOneSampleMatch,
    MethodOneTeamSample,
)
from lvfi_api.infrastructure.pricing_engine import public_method_one

_REQUESTED_COUNT = 10
_DATA_VERSION = "historical-data-model-v1"
_LOGICAL_SOURCE = "postgresql-normalized"
_CONFIGURATION_ID = "lvfi-app-006-default"


class MethodOneSampleProvider(Protocol):
    async def get_sample(self, match_id: int) -> MethodOneSample: ...


class MethodOnePublicFacade(Protocol):
    def run(self, request: MethodOneRequest) -> object: ...

    def serialize(self, result: MethodOneFinalResult) -> object: ...

    def sha256(self, value: object) -> object: ...


@dataclass(frozen=True, slots=True)
class MethodOneExecution:
    """Returned engine payload; this task never persists it."""

    payload: MethodOnePayload


class MethodOneExecutionService:
    """Validate APP-005 samples, build public contracts, then call the engine once."""

    def __init__(
        self,
        samples: MethodOneSampleProvider,
        engine: MethodOnePublicFacade = public_method_one,
    ) -> None:
        self._samples = samples
        self._engine = engine

    async def execute(self, match_id: int) -> MethodOneExecution:
        request = build_method_one_request(
            await self._samples.get_sample(match_id), self._engine
        )
        result = self._engine.run(request)
        if not isinstance(result, MethodOneFinalResult):
            raise MethodOneEngineError()  # pragma: no cover
        payload = self._engine.serialize(result)
        if not isinstance(payload, MethodOnePayload):  # pragma: no branch
            raise MethodOneEngineError()  # pragma: no cover
        return MethodOneExecution(payload)


def build_method_one_request(
    sample: MethodOneSample, engine: MethodOnePublicFacade = public_method_one
) -> MethodOneRequest:
    """Convert two APP-005 series exactly into four public Method One series."""
    _validate_sample(sample)
    target = sample.target_match
    references = (
        _reference(
            MethodOneSeriesRole.HOME_PRODUCTION,
            target,
            sample.home_sample.matches,
            ObservationRole.PRODUCTION,
            ParticipantRole.HOME,
            VenueCondition.HOME,
            engine,
            lambda item: item.statistics.home.full_match.goals,
            lambda item: item.match.away_team.id,
        ),
        _reference(
            MethodOneSeriesRole.HOME_CONCESSION,
            target,
            sample.home_sample.matches,
            ObservationRole.CONCESSION,
            ParticipantRole.HOME,
            VenueCondition.HOME,
            engine,
            lambda item: item.statistics.away.full_match.goals,
            lambda item: item.match.away_team.id,
        ),
        _reference(
            MethodOneSeriesRole.AWAY_PRODUCTION,
            target,
            sample.away_sample.matches,
            ObservationRole.PRODUCTION,
            ParticipantRole.AWAY,
            VenueCondition.AWAY,
            engine,
            lambda item: item.statistics.away.full_match.goals,
            lambda item: item.match.home_team.id,
        ),
        _reference(
            MethodOneSeriesRole.AWAY_CONCESSION,
            target,
            sample.away_sample.matches,
            ObservationRole.CONCESSION,
            ParticipantRole.AWAY,
            VenueCondition.AWAY,
            engine,
            lambda item: item.statistics.home.full_match.goals,
            lambda item: item.match.home_team.id,
        ),
    )
    return MethodOneRequest(
        str(target.id),
        str(target.home_team.id),
        str(target.away_team.id),
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        references,
        MethodOneConfiguration(_CONFIGURATION_ID),
        str(target.competition.id),
        _occurred_at(target),
    )


def _validate_sample(sample: MethodOneSample) -> None:
    if (  # pragma: no branch
        sample.parameters.requested_count != _REQUESTED_COUNT
        or sample.parameters.include_previous_season
        or sample.parameters.statistic_periods
        != ("goals_first_half", "goals_regulation_time")
    ):
        raise MethodOneSampleInvalidError()  # pragma: no cover
    _validate_team_sample(sample.target_match, sample.home_sample, "home")
    _validate_team_sample(sample.target_match, sample.away_sample, "away")


def _validate_team_sample(
    target: Match, team_sample: MethodOneTeamSample, expected_venue: str
) -> None:
    if team_sample.venue_condition != expected_venue:  # pragma: no branch
        raise MethodOneSampleInvalidError()  # pragma: no cover
    if not team_sample.complete:  # pragma: no branch
        raise MethodOneSampleIncompleteError()
    if (  # pragma: no branch
        team_sample.expected_count != _REQUESTED_COUNT
        or team_sample.found_count != _REQUESTED_COUNT
        or len(team_sample.matches) != _REQUESTED_COUNT
        or team_sample.insufficient_reason is not None
    ):
        raise MethodOneSampleInvalidError()  # pragma: no cover
    for item in team_sample.matches:
        _validate_sample_match(target, item, expected_venue)


def _validate_sample_match(
    target: Match, item: MethodOneSampleMatch, expected_venue: str
) -> None:
    match = item.match
    if (  # pragma: no branch
        item.statistics.match_id != match.id
        or match.competition.id != target.competition.id
        or match.season.id != target.season.id
        or not _is_before(match, target)
        or expected_venue == "home"
        and match.home_team.id != target.home_team.id
        or expected_venue == "away"
        and match.away_team.id != target.away_team.id
    ):
        raise MethodOneSampleInvalidError()  # pragma: no cover
    for value in (
        item.statistics.home.first_half.goals,
        item.statistics.home.full_match.goals,
        item.statistics.away.first_half.goals,
        item.statistics.away.full_match.goals,
    ):
        if (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):  # pragma: no branch
            raise MethodOneSampleInvalidError()  # pragma: no cover


def _is_before(candidate: Match, target: Match) -> bool:
    return candidate.played_on < target.played_on or (
        candidate.played_on == target.played_on and candidate.id < target.id
    )


def _reference(
    role: MethodOneSeriesRole,
    target: Match,
    matches: tuple[MethodOneSampleMatch, ...],
    observation_role: ObservationRole,
    participant_role: ParticipantRole,
    venue: VenueCondition,
    engine: MethodOnePublicFacade,
    goals: Callable[[MethodOneSampleMatch], int],
    opponent_id: Callable[[MethodOneSampleMatch], int],
) -> MethodOneSeriesReference:
    subject_id = (
        str(target.home_team.id)
        if participant_role is ParticipantRole.HOME
        else str(target.away_team.id)
    )
    observations = tuple(
        MatchObservation(
            MatchIdentity(
                str(item.match.id), _occurred_at(item.match), MatchState.COMPLETED
            ),
            subject_id,
            str(opponent_id(item)),
            participant_role,
            venue,
            observation_role,
            StatisticCode.GOALS,
            MatchPeriodCode.REGULATION_TIME,
            ObservationValue(
                ObservationState.OBSERVED, goals(item), ObservationUnit.COUNT
            ),
        )
        for item in matches
    )
    data_hash = engine.sha256(observations)
    if not isinstance(data_hash, str):  # pragma: no branch
        raise MethodOneEngineError()  # pragma: no cover
    snapshot = SampleSnapshot.create(
        definition=SampleDefinition(
            f"{target.id}:{role.value}",
            subject_id,
            observation_role,
            StatisticCode.GOALS,
            MatchPeriodCode.REGULATION_TIME,
            SampleFilter(
                venue,
                SampleWindowKind.LAST_N,
                _REQUESTED_COUNT,
                competition_ids=(str(target.competition.id),),
                season_ids=(str(target.season.id),),
                include_previous_season=False,
            ),
            _occurred_at(target),
        ),
        data_metadata=DataSnapshotMetadata(_DATA_VERSION, data_hash, _LOGICAL_SOURCE),
        observations=observations,
        exclusions=(),
    )
    if not isinstance(snapshot, SampleSnapshot):  # pragma: no branch
        raise MethodOneEngineError()  # pragma: no cover
    return MethodOneSeriesReference(role, snapshot)


def _occurred_at(match: Match) -> datetime:
    return datetime.combine(match.played_on, time.min, UTC)
