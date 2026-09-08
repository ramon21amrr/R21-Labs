"""Public, reusable statistics-sample endpoint without pricing behavior."""
# ruff: noqa: B008

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Literal, cast

from fastapi import APIRouter, Depends, Path, Query, Request
from pydantic import BaseModel, ConfigDict

from lvfi_api.application.statistics import StatisticsSampleService
from lvfi_api.domain.errors import InvalidQueryError, PersistenceUnavailableError
from lvfi_api.domain.statistics import (
    AchievementComparator,
    CompetitionScope,
    Metric,
    SeasonScope,
    StatisticsCandidate,
    StatisticsSample,
    StatisticsSampleRequest,
    StatisticsTarget,
    UnavailableValue,
    ValueFrequency,
    Venue,
)
from lvfi_api.persistence.statistics import SqlAlchemyStatisticsSampleRepository

router = APIRouter(tags=["statistics"])


class TargetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    match_id: int
    played_on: str
    competition_id: int
    competition_name: str
    season_id: int
    season_label: str
    home_team_id: int
    home_team_name: str
    away_team_id: int
    away_team_name: str

    @classmethod
    def from_contract(cls, value: StatisticsTarget) -> TargetResponse:
        return cls(
            match_id=value.match_id,
            played_on=str(value.played_on),
            competition_id=value.competition_id,
            competition_name=value.competition_name,
            season_id=value.season_id,
            season_label=value.season_label,
            home_team_id=value.home_team_id,
            home_team_name=value.home_team_name,
            away_team_id=value.away_team_id,
            away_team_name=value.away_team_name,
        )


class CandidateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    match_id: int
    played_on: str
    competition_id: int
    competition_name: str
    season_id: int
    season_label: str
    home_team_id: int
    home_team_name: str
    away_team_id: int
    away_team_name: str
    venue: Literal["home", "away"]
    value: int | None
    unavailable_reason: str | None

    @classmethod
    def from_contract(cls, value: StatisticsCandidate) -> CandidateResponse:
        return cls(
            match_id=value.match_id,
            played_on=str(value.played_on),
            competition_id=value.competition_id,
            competition_name=value.competition_name,
            season_id=value.season_id,
            season_label=value.season_label,
            home_team_id=value.home_team_id,
            home_team_name=value.home_team_name,
            away_team_id=value.away_team_id,
            away_team_name=value.away_team_name,
            venue=value.venue,
            value=value.value,
            unavailable_reason=value.unavailable_reason,
        )


class FrequencyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: int
    count: int

    @classmethod
    def from_contract(cls, value: ValueFrequency) -> FrequencyResponse:
        return cls(value=value.value, count=value.count)


class UnavailableValueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    match_id: int
    reason: str

    @classmethod
    def from_contract(cls, value: UnavailableValue) -> UnavailableValueResponse:
        return cls(match_id=value.match_id, reason=value.reason)


class StatisticsSampleFiltersResponse(BaseModel):
    """Explicit, typed public representation of the sample configuration."""

    model_config = ConfigDict(extra="forbid")
    team_id: int
    sample_size: Literal[5, 10, 15, 20]
    venue: Venue
    competition_scope: CompetitionScope
    season_scope: SeasonScope
    previous_season_id: int | None
    metric: Metric
    comparator: AchievementComparator | None
    achievement_target: int | None

    @classmethod
    def from_contract(
        cls, value: StatisticsSampleRequest
    ) -> StatisticsSampleFiltersResponse:
        return cls(
            team_id=value.team_id,
            sample_size=value.sample_size,
            venue=value.venue,
            competition_scope=value.competition_scope,
            season_scope=value.season_scope,
            previous_season_id=value.previous_season_id,
            metric=value.metric,
            comparator=value.comparator,
            achievement_target=value.achievement_target,
        )


class StatisticsSampleResponse(BaseModel):
    """Complete public evidence for one configured historical sample."""

    model_config = ConfigDict(extra="forbid")
    target_match: TargetResponse
    filters: StatisticsSampleFiltersResponse
    ordering: str
    candidate_count: int
    used_count: int
    candidate_match_ids: list[int]
    used_match_ids: list[int]
    candidates: list[CandidateResponse]
    used_matches: list[CandidateResponse]
    valid_values: list[int]
    unavailable_values: list[UnavailableValueResponse]
    available_count: int
    mean: float | None
    standard_deviation: float | None
    coefficient_of_variation: float | None
    frequencies: list[FrequencyResponse]
    achievement_count: int | None
    achievement_rate: float | None
    warnings: list[str]

    @classmethod
    def from_contract(cls, value: StatisticsSample) -> StatisticsSampleResponse:
        return cls(
            target_match=TargetResponse.from_contract(value.target),
            filters=StatisticsSampleFiltersResponse.from_contract(value.request),
            ordering=value.ordering,
            candidate_count=value.candidate_count,
            used_count=value.used_count,
            candidate_match_ids=list(value.candidate_match_ids),
            used_match_ids=list(value.used_match_ids),
            candidates=[
                CandidateResponse.from_contract(item) for item in value.candidates
            ],
            used_matches=[
                CandidateResponse.from_contract(item) for item in value.used_matches
            ],
            valid_values=list(value.valid_values),
            unavailable_values=[
                UnavailableValueResponse.from_contract(item)
                for item in value.unavailable_values
            ],
            available_count=value.available_count,
            mean=value.mean,
            standard_deviation=value.population_standard_deviation,
            coefficient_of_variation=value.coefficient_of_variation,
            frequencies=[
                FrequencyResponse.from_contract(item) for item in value.frequencies
            ],
            achievement_count=value.achievement_count,
            achievement_rate=value.achievement_rate,
            warnings=list(value.warnings),
        )


async def get_statistics_sample_service(request: Request) -> StatisticsSampleService:
    injected = getattr(request.app.state, "statistics_sample_service", None)
    if injected is not None:
        return cast(StatisticsSampleService, injected)
    database = request.app.state.database
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("database query session unavailable")
    return StatisticsSampleService(SqlAlchemyStatisticsSampleRepository(database))


def _only_query_parameters(*allowed: str) -> Callable[[Request], Awaitable[None]]:
    allowed_parameters = frozenset(allowed)

    async def validate(request: Request) -> None:
        if set(request.query_params) - allowed_parameters:
            raise InvalidQueryError("unsupported query parameter")

    return validate


@router.get(
    "/matches/{match_id}/statistics/sample",
    response_model=StatisticsSampleResponse,
    summary="Build a configurable reusable historical statistics sample",
    responses={
        404: {"description": "Target match not found."},
        422: {"description": "Invalid sample configuration."},
    },
    dependencies=[
        Depends(
            _only_query_parameters(
                "team_id",
                "sample_size",
                "venue",
                "competition_scope",
                "season_scope",
                "previous_season_id",
                "metric",
                "comparator",
                "achievement_target",
            )
        )
    ],
)
async def get_statistics_sample(
    match_id: int = Path(ge=1, description="Stable target match identifier."),
    team_id: int = Query(ge=1),
    sample_size: int = Query(default=10, ge=5, le=20),
    venue: Literal["home", "away", "overall"] = Query(default="overall"),
    competition_scope: Literal["target_competition", "all_eligible"] = Query(
        default="target_competition"
    ),
    season_scope: Literal["current", "current_and_previous"] = Query(
        default="current"
    ),
    previous_season_id: int | None = Query(default=None, ge=1),
    metric: Literal[
        "goals_scored",
        "goals_conceded",
        "result_win",
        "corners",
        "shots_on_target",
        "shots",
        "cards",
        "fouls",
    ] = Query(default="goals_scored"),
    comparator: Literal["at_least", "at_most", "equal"] | None = Query(default=None),
    achievement_target: int | None = Query(default=None, ge=0),
    service: StatisticsSampleService = Depends(get_statistics_sample_service),
) -> StatisticsSampleResponse:
    if sample_size not in {5, 10, 15, 20}:
        raise InvalidQueryError("unsupported sample size")
    if (comparator is None) != (achievement_target is None):
        raise InvalidQueryError("achievement fields must be paired")
    if season_scope == "current_and_previous" and previous_season_id is None:
        raise InvalidQueryError("previous season is required")
    if season_scope == "current" and previous_season_id is not None:
        raise InvalidQueryError("previous season is unsupported")
    return StatisticsSampleResponse.from_contract(
        await service.get_sample(
            match_id,
            StatisticsSampleRequest(
                team_id=team_id,
                sample_size=cast(Literal[5, 10, 15, 20], sample_size),
                venue=venue,
                competition_scope=competition_scope,
                season_scope=season_scope,
                previous_season_id=previous_season_id,
                metric=metric,
                comparator=comparator,
                achievement_target=achievement_target,
            ),
        )
    )
