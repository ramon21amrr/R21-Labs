"""Public HTTP schemas and routes for historical football queries."""
# ruff: noqa: B008

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, Path, Query, Request
from pydantic import BaseModel

from lvfi_api.application.historical_queries import HistoricalQueryService
from lvfi_api.domain.errors import InvalidQueryError, PersistenceUnavailableError
from lvfi_api.domain.historical_queries import (
    Match,
    MatchFilters,
    MatchStatistics,
    Page,
    Reference,
    Season,
    StatisticsPeriod,
    TeamStatistics,
)
from lvfi_api.persistence.historical_queries import SqlAlchemyHistoricalQueryRepository

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

router = APIRouter(tags=["historical data"])


class PaginationResponse(BaseModel):
    """Stable offset-page metadata for every historical list response."""

    page: int
    page_size: int
    total: int


class ReferenceResponse(BaseModel):
    """Safe public representation of a competition or team."""

    id: int
    display_name: str
    created_at: datetime

    @classmethod
    def from_contract(cls, value: Reference) -> ReferenceResponse:
        return cls(
            id=value.id, display_name=value.display_name, created_at=value.created_at
        )


class SeasonResponse(BaseModel):
    """Safe public representation of a competition season."""

    id: int
    competition: ReferenceResponse
    label: str
    created_at: datetime

    @classmethod
    def from_contract(cls, value: Season) -> SeasonResponse:
        return cls(
            id=value.id,
            competition=ReferenceResponse.from_contract(value.competition),
            label=value.label,
            created_at=value.created_at,
        )


class MatchResponse(BaseModel):
    """Product-facing match data without import or source-record details."""

    id: int
    played_on: date
    competition: ReferenceResponse
    season: SeasonResponse
    home_team: ReferenceResponse
    away_team: ReferenceResponse
    has_statistics: bool
    created_at: datetime

    @classmethod
    def from_contract(cls, value: Match) -> MatchResponse:
        return cls(
            id=value.id,
            played_on=value.played_on,
            competition=ReferenceResponse.from_contract(value.competition),
            season=SeasonResponse.from_contract(value.season),
            home_team=ReferenceResponse.from_contract(value.home_team),
            away_team=ReferenceResponse.from_contract(value.away_team),
            has_statistics=value.has_statistics,
            created_at=value.created_at,
        )


class StatisticsPeriodResponse(BaseModel):
    """Observed values for one team in one period; absent fields were not imported."""

    goals: int
    shots: int
    shots_on_target: int
    corners: int
    fouls: int | None
    cards: int | None

    @classmethod
    def from_contract(cls, value: StatisticsPeriod) -> StatisticsPeriodResponse:
        return cls(
            goals=value.goals,
            shots=value.shots,
            shots_on_target=value.shots_on_target,
            corners=value.corners,
            fouls=value.fouls,
            cards=value.cards,
        )


class TeamStatisticsResponse(BaseModel):
    """First-half and full-match observations for one team."""

    first_half: StatisticsPeriodResponse
    full_match: StatisticsPeriodResponse

    @classmethod
    def from_contract(cls, value: TeamStatistics) -> TeamStatisticsResponse:
        return cls(
            first_half=StatisticsPeriodResponse.from_contract(value.first_half),
            full_match=StatisticsPeriodResponse.from_contract(value.full_match),
        )


class MatchStatisticsResponse(BaseModel):
    """Canonical statistics split by home/away team and period."""

    match_id: int
    home: TeamStatisticsResponse
    away: TeamStatisticsResponse

    @classmethod
    def from_contract(cls, value: MatchStatistics) -> MatchStatisticsResponse:
        return cls(
            match_id=value.match_id,
            home=TeamStatisticsResponse.from_contract(value.home),
            away=TeamStatisticsResponse.from_contract(value.away),
        )


class CompetitionPageResponse(PaginationResponse):
    items: list[ReferenceResponse]


class SeasonPageResponse(PaginationResponse):
    items: list[SeasonResponse]


class TeamPageResponse(PaginationResponse):
    items: list[ReferenceResponse]


class MatchPageResponse(PaginationResponse):
    items: list[MatchResponse]


def _page_response(page: Page[Any], mapper: Callable[[Any], Any]) -> dict[str, Any]:
    return {
        "items": [mapper(item) for item in page.items],
        "page": page.page,
        "page_size": page.page_size,
        "total": page.total,
    }


def _only_query_parameters(*allowed: str) -> Callable[[Request], None]:
    allowed_parameters = frozenset(allowed)

    async def validate(request: Request) -> None:
        if set(request.query_params) - allowed_parameters:
            raise InvalidQueryError("unsupported query parameter")

    return validate


async def get_service(request: Request) -> HistoricalQueryService:
    """Obtain an injected service or the PostgreSQL-backed implementation."""

    injected = getattr(request.app.state, "historical_query_service", None)
    if injected is not None:
        return cast(HistoricalQueryService, injected)
    database = request.app.state.database
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("database query session unavailable")
    return HistoricalQueryService(SqlAlchemyHistoricalQueryRepository(database))


PageNumber = int
PageSize = int


@router.get(
    "/competitions",
    response_model=CompetitionPageResponse,
    summary="List competitions",
    description=(
        "Lists normalized competitions in deterministic name and identifier order."
    ),
    responses={422: {"description": "Invalid query parameter."}},
    dependencies=[Depends(_only_query_parameters("page", "page_size"))],
)
async def list_competitions(
    service: HistoricalQueryService = Depends(get_service),
    page: PageNumber = Query(default=1, ge=1, description="One-based page number."),
    page_size: PageSize = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Items per page; at most 100.",
    ),
) -> CompetitionPageResponse:
    page_result = await service.list_competitions(page, page_size)
    return CompetitionPageResponse(
        **_page_response(page_result, ReferenceResponse.from_contract)
    )


@router.get(
    "/competitions/{competition_id}",
    response_model=ReferenceResponse,
    summary="Get a competition",
    responses={404: {"description": "Competition not found."}},
)
async def get_competition(
    competition_id: int = Path(ge=1, description="Stable competition identifier."),
    service: HistoricalQueryService = Depends(get_service),
) -> ReferenceResponse:
    return ReferenceResponse.from_contract(
        await service.get_competition(competition_id)
    )


@router.get(
    "/seasons",
    response_model=SeasonPageResponse,
    summary="List seasons",
    description="Lists seasons, optionally constrained to one competition.",
    dependencies=[
        Depends(_only_query_parameters("competition_id", "page", "page_size"))
    ],
)
async def list_seasons(
    competition_id: int | None = Query(default=None, ge=1),
    service: HistoricalQueryService = Depends(get_service),
    page: PageNumber = Query(default=1, ge=1),
    page_size: PageSize = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> SeasonPageResponse:
    page_result = await service.list_seasons(competition_id, page, page_size)
    return SeasonPageResponse(
        **_page_response(page_result, SeasonResponse.from_contract)
    )


@router.get(
    "/seasons/{season_id}",
    response_model=SeasonResponse,
    summary="Get a season",
    responses={404: {"description": "Season not found."}},
)
async def get_season(
    season_id: int = Path(ge=1, description="Stable season identifier."),
    service: HistoricalQueryService = Depends(get_service),
) -> SeasonResponse:
    return SeasonResponse.from_contract(await service.get_season(season_id))


@router.get(
    "/teams",
    response_model=TeamPageResponse,
    summary="List teams",
    description=(
        "Lists normalized teams; name is an exact, case-sensitive display-name filter."
    ),
    dependencies=[Depends(_only_query_parameters("name", "page", "page_size"))],
)
async def list_teams(
    name: str | None = Query(default=None, min_length=1, max_length=255),
    service: HistoricalQueryService = Depends(get_service),
    page: PageNumber = Query(default=1, ge=1),
    page_size: PageSize = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> TeamPageResponse:
    page_result = await service.list_teams(name, page, page_size)
    return TeamPageResponse(
        **_page_response(page_result, ReferenceResponse.from_contract)
    )


@router.get(
    "/teams/{team_id}",
    response_model=ReferenceResponse,
    summary="Get a team",
    responses={404: {"description": "Team not found."}},
)
async def get_team(
    team_id: int = Path(ge=1, description="Stable team identifier."),
    service: HistoricalQueryService = Depends(get_service),
) -> ReferenceResponse:
    return ReferenceResponse.from_contract(await service.get_team(team_id))


@router.get(
    "/matches",
    response_model=MatchPageResponse,
    summary="List historical matches",
    description=(
        "Lists historical matches in stable ascending date and identifier order. "
        "All filters are exact; team_id includes home and away participation."
    ),
    dependencies=[
        Depends(
            _only_query_parameters(
                "competition_id",
                "season_id",
                "home_team_id",
                "away_team_id",
                "team_id",
                "date_from",
                "date_to",
                "page",
                "page_size",
            )
        )
    ],
)
async def list_matches(
    competition_id: int | None = Query(default=None, ge=1),
    season_id: int | None = Query(default=None, ge=1),
    home_team_id: int | None = Query(default=None, ge=1),
    away_team_id: int | None = Query(default=None, ge=1),
    team_id: int | None = Query(default=None, ge=1),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    service: HistoricalQueryService = Depends(get_service),
    page: PageNumber = Query(default=1, ge=1),
    page_size: PageSize = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> MatchPageResponse:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise InvalidQueryError("date range is invalid")
    page_result = await service.list_matches(
        MatchFilters(
            competition_id=competition_id,
            season_id=season_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            team_id=team_id,
            date_from=date_from,
            date_to=date_to,
        ),
        page,
        page_size,
    )
    return MatchPageResponse(**_page_response(page_result, MatchResponse.from_contract))


@router.get(
    "/matches/{match_id}",
    response_model=MatchResponse,
    summary="Get a historical match",
    responses={404: {"description": "Match not found."}},
)
async def get_match(
    match_id: int = Path(ge=1, description="Stable match identifier."),
    service: HistoricalQueryService = Depends(get_service),
) -> MatchResponse:
    return MatchResponse.from_contract(await service.get_match(match_id))


@router.get(
    "/matches/{match_id}/statistics",
    response_model=MatchStatisticsResponse,
    summary="Get canonical historical match statistics",
    description="Returns imported observations without derived metrics.",
    responses={404: {"description": "Match or statistics not found."}},
)
async def get_match_statistics(
    match_id: int = Path(ge=1, description="Stable match identifier."),
    service: HistoricalQueryService = Depends(get_service),
) -> MatchStatisticsResponse:
    return MatchStatisticsResponse.from_contract(await service.get_statistics(match_id))
