"""Synthetic end-to-end and repository coverage for historical query API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.application.historical_queries import HistoricalQueryService
from lvfi_api.domain.errors import (
    PersistenceUnavailableError,
    ResourceNotFoundError,
    StatisticsNotFoundError,
)
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
from lvfi_api.main import create_app
from lvfi_api.persistence.historical_queries import SqlAlchemyHistoricalQueryRepository

from .conftest import FakeDatabase

NOW = datetime(2026, 1, 2, tzinfo=UTC)
COMPETITION = Reference(1, "League", NOW)
HOME = Reference(2, "Home", NOW)
AWAY = Reference(3, "Away", NOW)
SEASON = Season(4, COMPETITION, "2026", NOW)
MATCH = Match(5, date(2026, 1, 2), COMPETITION, SEASON, HOME, AWAY, True, NOW)
PERIOD = StatisticsPeriod(1, 2, 1, 3, None, None)
FULL_PERIOD = StatisticsPeriod(2, 4, 2, 5, 6, 1)
STATISTICS = MatchStatistics(
    5, TeamStatistics(PERIOD, FULL_PERIOD), TeamStatistics(PERIOD, FULL_PERIOD)
)


class RepositoryFake:
    async def list_competitions(self, page: int, page_size: int) -> Page[Reference]:
        return Page((COMPETITION,), page, page_size, 1)

    async def get_competition(self, identifier: int) -> Reference | None:
        return COMPETITION if identifier == 1 else None

    async def list_seasons(
        self, competition_id: int | None, page: int, page_size: int
    ) -> Page[Season]:
        return Page(
            (SEASON,) if competition_id in (None, 1) else (), page, page_size, 1
        )

    async def get_season(self, identifier: int) -> Season | None:
        return SEASON if identifier == 4 else None

    async def list_teams(
        self, name: str | None, page: int, page_size: int
    ) -> Page[Reference]:
        items = (HOME, AWAY) if name is None else ((HOME,) if name == "Home" else ())
        return Page(items, page, page_size, len(items))

    async def get_team(self, identifier: int) -> Reference | None:
        return {2: HOME, 3: AWAY}.get(identifier)

    async def list_matches(
        self, filters: MatchFilters, page: int, page_size: int
    ) -> Page[Match]:
        requested = (
            filters.competition_id,
            filters.season_id,
            filters.home_team_id,
            filters.away_team_id,
            filters.team_id,
        )
        return Page(
            (MATCH,) if all(value in (None, 1, 2, 3, 4) for value in requested) else (),
            page,
            page_size,
            1,
        )

    async def get_match(self, identifier: int) -> Match | None:
        return MATCH if identifier in (5, 6) else None

    async def get_statistics(self, identifier: int) -> MatchStatistics | None:
        return STATISTICS if identifier == 5 else None


@pytest.fixture
def query_client(settings: Any) -> TestClient:
    app = create_app(settings, FakeDatabase())
    app.state.historical_query_service = HistoricalQueryService(RepositoryFake())  # type: ignore[arg-type]
    with TestClient(app) as client:
        yield client


def test_historical_endpoints_public_contract_and_openapi(
    query_client: TestClient,
) -> None:
    responses = [
        query_client.get("/competitions"),
        query_client.get("/competitions/1"),
        query_client.get("/seasons?competition_id=1"),
        query_client.get("/seasons/4"),
        query_client.get("/teams?name=Home"),
        query_client.get("/teams/2"),
        query_client.get(
            "/matches?competition_id=1&season_id=4&home_team_id=2&away_team_id=3&team_id=2&date_from=2026-01-01&date_to=2026-01-03"
        ),
        query_client.get("/matches/5"),
        query_client.get("/matches/5/statistics"),
    ]
    assert all(response.status_code == 200 for response in responses)
    assert responses[0].json()["items"][0]["display_name"] == "League"
    assert responses[6].json()["items"][0]["id"] == 5
    assert responses[8].json()["home"]["full_match"]["fouls"] == 6
    assert "source_record_id" not in responses[7].text
    assert "source_sha256" not in responses[8].text
    assert (
        query_client.get("/matches", headers={"X-Request-ID": "query-1"}).headers[
            "X-Request-ID"
        ]
        == "query-1"
    )
    paths = query_client.get("/openapi.json").json()["paths"]
    assert "/matches/{match_id}/statistics" in paths
    assert paths["/matches"]["get"]["summary"] == "List historical matches"


def test_query_validation_and_sanitized_absence(query_client: TestClient) -> None:
    invalid = [
        query_client.get("/competitions?unknown=x"),
        query_client.get("/teams?name="),
        query_client.get("/matches?date_from=2026-02-01&date_to=2026-01-01"),
        query_client.get("/matches?page=0"),
    ]
    assert all(response.status_code == 422 for response in invalid)
    assert all(response.json()["code"] == "invalid_request" for response in invalid)
    assert query_client.get("/competitions/99").json()["code"] == "not_found"
    assert query_client.get("/seasons/99").status_code == 404
    assert query_client.get("/teams/99").status_code == 404
    assert query_client.get("/matches/99").status_code == 404
    missing_stats = query_client.get("/matches/6/statistics")
    assert missing_stats.json()["code"] == "statistics_not_found"
    assert "unsupported" not in missing_stats.text


@pytest.mark.asyncio
async def test_application_service_absence_paths() -> None:
    service = HistoricalQueryService(RepositoryFake())  # type: ignore[arg-type]
    assert (await service.list_competitions(2, 10)).page == 2
    assert (await service.list_seasons(None, 1, 10)).items == (SEASON,)
    assert (await service.list_teams(None, 1, 10)).total == 2
    assert (await service.list_matches(MatchFilters(), 1, 10)).items == (MATCH,)
    with pytest.raises(ResourceNotFoundError):
        await service.get_competition(99)
    with pytest.raises(ResourceNotFoundError):
        await service.get_season(99)
    with pytest.raises(ResourceNotFoundError):
        await service.get_team(99)
    with pytest.raises(ResourceNotFoundError):
        await service.get_match(99)
    with pytest.raises(StatisticsNotFoundError):
        await service.get_statistics(6)


class MappingResult:
    def __init__(self, row: dict[str, Any]) -> None:
        self.row = row

    def mappings(self) -> MappingResult:
        return self

    def all(self) -> list[dict[str, Any]]:
        return [self.row]

    def one_or_none(self) -> dict[str, Any] | None:
        return self.row


class SessionFake:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.executions = 0

    async def scalar(self, statement: Any) -> int:
        return 1

    async def execute(self, statement: Any) -> MappingResult:
        self.executions += 1
        if self.fail:
            raise SQLAlchemyError("synthetic database failure")
        return MappingResult(
            {
                "competition_id": 1,
                "competition_display_name": "League",
                "competition_created_at": NOW,
                "season_id": 4,
                "season_label": "2026",
                "season_created_at": NOW,
                "team_id": 2,
                "team_display_name": "Home",
                "team_created_at": NOW,
                "home_team_id": 2,
                "home_team_display_name": "Home",
                "home_team_created_at": NOW,
                "away_team_id": 3,
                "away_team_display_name": "Away",
                "away_team_created_at": NOW,
                "match_id": 5,
                "played_on": date(2026, 1, 2),
                "match_created_at": NOW,
                "has_statistics": True,
                "home_goals_first_half": 1,
                "home_shots_first_half": 2,
                "home_shots_on_target_first_half": 1,
                "home_corners_first_half": 3,
                "away_goals_first_half": 1,
                "away_shots_first_half": 2,
                "away_shots_on_target_first_half": 1,
                "away_corners_first_half": 3,
                "home_goals_full_match": 2,
                "home_shots_full_match": 4,
                "home_shots_on_target_full_match": 2,
                "home_corners_full_match": 5,
                "home_fouls_full_match": 6,
                "home_cards_full_match": 1,
                "away_goals_full_match": 2,
                "away_shots_full_match": 4,
                "away_shots_on_target_full_match": 2,
                "away_corners_full_match": 5,
                "away_fouls_full_match": 6,
                "away_cards_full_match": 1,
            }
        )


class ProviderFake:
    def __init__(self, session: SessionFake) -> None:
        self.session_value = session

    @asynccontextmanager
    async def session(self) -> Any:
        yield self.session_value


@pytest.mark.asyncio
async def test_sqlalchemy_repository_synthetic_paths_and_filters() -> None:
    session = SessionFake()
    repository = SqlAlchemyHistoricalQueryRepository(ProviderFake(session))
    assert (await repository.list_competitions(1, 1)).total == 1
    assert await repository.get_competition(1) == COMPETITION
    assert (await repository.list_seasons(None, 1, 1)).items == (SEASON,)
    assert (await repository.list_seasons(1, 1, 1)).items == (SEASON,)
    assert await repository.get_season(4) == SEASON
    assert (await repository.list_teams(None, 1, 1)).items == (HOME,)
    assert (await repository.list_teams("Home", 1, 1)).items == (HOME,)
    assert await repository.get_team(2) == HOME
    for filters in (
        MatchFilters(),
        MatchFilters(competition_id=1),
        MatchFilters(season_id=4),
        MatchFilters(home_team_id=2),
        MatchFilters(away_team_id=3),
        MatchFilters(team_id=2),
        MatchFilters(date_from=date(2026, 1, 1)),
        MatchFilters(date_to=date(2026, 1, 3)),
    ):
        assert (await repository.list_matches(filters, 1, 1)).items == (MATCH,)
    assert await repository.get_match(5) == MATCH
    assert await repository.get_statistics(5) == STATISTICS
    assert session.executions == 18


@pytest.mark.asyncio
async def test_sqlalchemy_repository_sanitizes_persistence_failure() -> None:
    repository = SqlAlchemyHistoricalQueryRepository(
        ProviderFake(SessionFake(fail=True))
    )
    with pytest.raises(PersistenceUnavailableError):
        await repository.list_competitions(1, 1)


class EmptyResult:
    def mappings(self) -> EmptyResult:
        return self

    def all(self) -> list[dict[str, Any]]:
        return []

    def one_or_none(self) -> None:
        return None


class EmptySession(SessionFake):
    async def execute(self, statement: Any) -> EmptyResult:
        self.executions += 1
        return EmptyResult()


@pytest.mark.asyncio
async def test_sqlalchemy_repository_absence_and_all_failure_paths() -> None:
    empty = SqlAlchemyHistoricalQueryRepository(ProviderFake(EmptySession()))
    assert await empty.get_competition(99) is None
    assert await empty.get_season(99) is None
    assert await empty.get_team(99) is None
    assert await empty.get_match(99) is None
    assert await empty.get_statistics(99) is None
    failing = SqlAlchemyHistoricalQueryRepository(ProviderFake(SessionFake(fail=True)))
    for operation in (
        failing.get_competition(1),
        failing.get_season(1),
        failing.get_team(1),
        failing.get_match(1),
        failing.get_statistics(1),
    ):
        with pytest.raises(PersistenceUnavailableError):
            await operation


def test_query_dependency_handles_missing_session(settings: Any) -> None:
    with TestClient(create_app(settings, FakeDatabase())) as client:
        response = client.get("/competitions")
    assert response.status_code == 503
    assert response.json()["code"] == "dependency_unavailable"


class QueryDatabaseFake(ProviderFake):
    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def is_ready(self) -> bool:
        return True


def test_query_dependency_builds_postgresql_repository(settings: Any) -> None:
    with TestClient(create_app(settings, QueryDatabaseFake(SessionFake()))) as client:
        response = client.get("/competitions")
    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == 1
