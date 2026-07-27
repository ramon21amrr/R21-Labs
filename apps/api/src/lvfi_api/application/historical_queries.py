"""Read-only use cases for the controlled historical-data model."""

from __future__ import annotations

from typing import Protocol

from lvfi_api.domain.errors import ResourceNotFoundError, StatisticsNotFoundError
from lvfi_api.domain.historical_queries import (
    Match,
    MatchFilters,
    MatchStatistics,
    Page,
    Reference,
    Season,
)


class HistoricalQueryRepository(Protocol):
    """Persistence boundary required by historical query use cases."""

    async def list_competitions(self, page: int, page_size: int) -> Page[Reference]: ...

    async def get_competition(self, competition_id: int) -> Reference | None: ...

    async def list_seasons(
        self, competition_id: int | None, page: int, page_size: int
    ) -> Page[Season]: ...

    async def get_season(self, season_id: int) -> Season | None: ...

    async def list_teams(
        self, name: str | None, page: int, page_size: int
    ) -> Page[Reference]: ...

    async def get_team(self, team_id: int) -> Reference | None: ...

    async def list_matches(
        self, filters: MatchFilters, page: int, page_size: int
    ) -> Page[Match]: ...

    async def get_match(self, match_id: int) -> Match | None: ...

    async def get_statistics(self, match_id: int) -> MatchStatistics | None: ...


class HistoricalQueryService:
    """Expose explicit read-only application operations over a repository."""

    def __init__(self, repository: HistoricalQueryRepository) -> None:
        self._repository = repository

    async def list_competitions(self, page: int, page_size: int) -> Page[Reference]:
        return await self._repository.list_competitions(page, page_size)

    async def get_competition(self, competition_id: int) -> Reference:
        competition = await self._repository.get_competition(competition_id)
        if competition is None:
            raise ResourceNotFoundError("competition")
        return competition

    async def list_seasons(
        self, competition_id: int | None, page: int, page_size: int
    ) -> Page[Season]:
        return await self._repository.list_seasons(competition_id, page, page_size)

    async def get_season(self, season_id: int) -> Season:
        season = await self._repository.get_season(season_id)
        if season is None:
            raise ResourceNotFoundError("season")
        return season

    async def list_teams(
        self, name: str | None, page: int, page_size: int
    ) -> Page[Reference]:
        return await self._repository.list_teams(name, page, page_size)

    async def get_team(self, team_id: int) -> Reference:
        team = await self._repository.get_team(team_id)
        if team is None:
            raise ResourceNotFoundError("team")
        return team

    async def list_matches(
        self, filters: MatchFilters, page: int, page_size: int
    ) -> Page[Match]:
        return await self._repository.list_matches(filters, page, page_size)

    async def get_match(self, match_id: int) -> Match:
        match = await self._repository.get_match(match_id)
        if match is None:
            raise ResourceNotFoundError("match")
        return match

    async def get_statistics(self, match_id: int) -> MatchStatistics:
        await self.get_match(match_id)
        statistics = await self._repository.get_statistics(match_id)
        if statistics is None:
            raise StatisticsNotFoundError()
        return statistics
