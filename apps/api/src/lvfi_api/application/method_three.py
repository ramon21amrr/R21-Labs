"""Deterministic Method Three orchestration over APP-013 statistics samples."""

from __future__ import annotations

from datetime import date
from typing import Literal, Protocol, cast

from lvfi_api.domain.errors import InvalidQueryError, ResourceNotFoundError
from lvfi_api.domain.method_three import (
    METHOD_THREE_NAME,
    METHOD_THREE_VERSION,
    MethodThreeConfiguration,
    MethodThreeResult,
    MethodThreeSideResult,
    ObservedFrequency,
)
from lvfi_api.domain.statistics import (
    StatisticsSample,
    StatisticsSampleRequest,
    StatisticsTarget,
)


class StatisticsSamples(Protocol):
    """APP-013 target and sample capabilities required by Method Three."""

    async def get_target(self, match_id: int) -> StatisticsTarget | None: ...

    async def get_sample(
        self, match_id: int, request: StatisticsSampleRequest
    ) -> StatisticsSample: ...


class MethodThreeObservedFrequencyService:
    """Build home, away and pooled observed frequencies without missing-as-zero."""

    def __init__(self, samples: StatisticsSamples) -> None:
        self._samples = samples

    async def execute(
        self, match_id: int, configuration: MethodThreeConfiguration
    ) -> MethodThreeResult:
        _validate_configuration(configuration)
        target = await self._samples.get_target(match_id)
        if target is None:
            raise ResourceNotFoundError("match")
        home_sample = await self._samples.get_sample(
            match_id, _request(target.home_team_id, "home", configuration)
        )
        away_sample = await self._samples.get_sample(
            match_id, _request(target.away_team_id, "away", configuration)
        )
        home_values = _validated_values(home_sample, target.match_id, target.played_on)
        away_values = _validated_values(away_sample, target.match_id, target.played_on)
        home = MethodThreeSideResult(
            _frequency(home_values, configuration), home_sample
        )
        away = MethodThreeSideResult(
            _frequency(away_values, configuration), away_sample
        )
        combined = _combined(home.frequency, away.frequency)
        return MethodThreeResult(
            method=METHOD_THREE_NAME,
            method_version=METHOD_THREE_VERSION,
            target=target,
            configuration=configuration,
            nominal_sample_size=configuration.sample_size,
            home=home,
            away=away,
            combined=combined,
            warnings=_warnings(home, away, combined),
        )


def _validate_configuration(configuration: MethodThreeConfiguration) -> None:
    if configuration.sample_size not in {5, 10, 15, 20}:
        raise InvalidQueryError("unsupported sample size")
    if configuration.competition_scope not in {"target_competition", "all_eligible"}:
        raise InvalidQueryError("unsupported competition scope")
    if configuration.season_scope not in {"current", "current_and_previous"}:
        raise InvalidQueryError("unsupported season scope")
    if configuration.metric not in {
        "goals_scored",
        "goals_conceded",
        "result_win",
        "corners",
        "shots_on_target",
        "shots",
        "cards",
        "fouls",
    }:
        raise InvalidQueryError("unsupported metric")
    if configuration.comparator not in {"at_least", "at_most", "equal"}:
        raise InvalidQueryError("unsupported comparator")
    if configuration.season_scope == "current" and configuration.previous_season_id:
        raise InvalidQueryError("previous season is unsupported")
    if (
        configuration.season_scope == "current_and_previous"
        and configuration.previous_season_id is None
    ):
        raise InvalidQueryError("previous season is required")
    if configuration.achievement_target < 0:
        raise InvalidQueryError("achievement target must be nonnegative")


def _request(
    team_id: int,
    venue: Literal["home", "away"],
    configuration: MethodThreeConfiguration,
) -> StatisticsSampleRequest:
    return StatisticsSampleRequest(
        team_id=team_id,
        sample_size=configuration.sample_size,
        venue=venue,
        competition_scope=configuration.competition_scope,
        season_scope=configuration.season_scope,
        previous_season_id=configuration.previous_season_id,
        metric=configuration.metric,
        comparator=configuration.comparator,
        achievement_target=configuration.achievement_target,
    )


def _validated_values(
    sample: StatisticsSample, target_id: int, target_date: date
) -> tuple[int, ...]:
    if sample.target.match_id != target_id or sample.target.played_on != target_date:
        raise InvalidQueryError("sample target is inconsistent")
    for candidate in sample.candidates:
        if candidate.played_on > target_date or (
            candidate.played_on == target_date and candidate.match_id >= target_id
        ):
            raise InvalidQueryError("sample contains observation after cutoff")
    used_matches = tuple(
        candidate for candidate in sample.candidates if candidate.value is not None
    )
    values = tuple(cast(int, candidate.value) for candidate in used_matches)
    if (
        sample.candidate_match_ids
        != tuple(candidate.match_id for candidate in sample.candidates)
        or sample.used_matches != used_matches
        or sample.used_match_ids
        != tuple(candidate.match_id for candidate in used_matches)
        or sample.valid_values != values
        or sample.candidate_count != len(sample.candidates)
        or sample.used_count != len(used_matches)
        or sample.available_count != len(values)
    ):
        raise InvalidQueryError("sample evidence is inconsistent")
    return values


def _frequency(
    values: tuple[int, ...], configuration: MethodThreeConfiguration
) -> ObservedFrequency:
    if configuration.comparator == "at_least":
        event_count = sum(value >= configuration.achievement_target for value in values)
    elif configuration.comparator == "at_most":
        event_count = sum(value <= configuration.achievement_target for value in values)
    else:
        event_count = sum(value == configuration.achievement_target for value in values)
    valid_count = len(values)
    return ObservedFrequency(
        event_count=event_count,
        valid_observation_count=valid_count,
        frequency=event_count / valid_count if valid_count else None,
    )


def _combined(home: ObservedFrequency, away: ObservedFrequency) -> ObservedFrequency:
    event_count = home.event_count + away.event_count
    valid_count = home.valid_observation_count + away.valid_observation_count
    return ObservedFrequency(
        event_count=event_count,
        valid_observation_count=valid_count,
        frequency=event_count / valid_count if valid_count else None,
    )


def _warnings(
    home: MethodThreeSideResult,
    away: MethodThreeSideResult,
    combined: ObservedFrequency,
) -> tuple[str, ...]:
    warnings = [f"home:{warning}" for warning in home.sample.warnings]
    if home.frequency.frequency is None:
        warnings.append("home:frequency_unavailable_no_valid_observations")
    warnings.extend(f"away:{warning}" for warning in away.sample.warnings)
    if away.frequency.frequency is None:
        warnings.append("away:frequency_unavailable_no_valid_observations")
    if combined.frequency is None:
        warnings.append("combined:frequency_unavailable_no_valid_observations")
    return tuple(warnings)
