"""Synthetic coverage for deterministic Method 1 sample construction."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.application.method_one_samples import MethodOneSampleService
from lvfi_api.domain.errors import ResourceNotFoundError
from lvfi_api.domain.historical_queries import (
    Match,
    MatchStatistics,
    MethodOneSampleMatch,
    Reference,
    Season,
    StatisticsPeriod,
    TeamStatistics,
)
from lvfi_api.main import create_app
from lvfi_api.persistence.method_one_samples import SqlAlchemyMethodOneSampleRepository

from .conftest import FakeDatabase

NOW = datetime(2026, 1, 2, tzinfo=UTC)
COMPETITION = Reference(1, "Synthetic League", NOW)
HOME = Reference(2, "Synthetic Home", NOW)
AWAY = Reference(3, "Synthetic Away", NOW)
SEASON = Season(4, COMPETITION, "2026", NOW)
TARGET = Match(50, date(2026, 7, 2), COMPETITION, SEASON, HOME, AWAY, True, NOW)
PERIOD = StatisticsPeriod(0, 2, 1, 3, None, None)
FULL_PERIOD = StatisticsPeriod(1, 4, 2, 5, 6, 1)
STATISTICS = MatchStatistics(
    TARGET.id,
    TeamStatistics(PERIOD, FULL_PERIOD),
    TeamStatistics(PERIOD, FULL_PERIOD),
)
SAMPLE_MATCH = MethodOneSampleMatch(TARGET, STATISTICS)


def sample_match(match_id: int) -> MethodOneSampleMatch:
    match = Match(
        match_id,
        date(2026, 7, 1),
        COMPETITION,
        SEASON,
        HOME,
        AWAY,
        True,
        NOW,
    )
    return MethodOneSampleMatch(
        match, MatchStatistics(match_id, STATISTICS.home, STATISTICS.away)
    )


class HistoricalFake:
    def __init__(self, match: Match | None = TARGET) -> None:
        self.match = match

    async def get_match(self, match_id: int) -> Match:
        if self.match is None or match_id != self.match.id:
            raise ResourceNotFoundError("match")
        return self.match


class SampleFake:
    def __init__(
        self,
        home: tuple[MethodOneSampleMatch, ...],
        away: tuple[MethodOneSampleMatch, ...],
    ) -> None:
        self.home = home
        self.away = away
        self.target: Match | None = None

    async def get_samples(
        self, target_match: Match
    ) -> tuple[tuple[MethodOneSampleMatch, ...], tuple[MethodOneSampleMatch, ...]]:
        self.target = target_match
        return self.home, self.away


@pytest.mark.asyncio
async def test_service_builds_complete_separate_samples() -> None:
    distinct_matches = tuple(sample_match(match_id) for match_id in range(1, 11))
    repository = SampleFake(distinct_matches, distinct_matches)
    service = MethodOneSampleService(HistoricalFake(), repository)  # type: ignore[arg-type]

    result = await service.get_sample(TARGET.id)

    assert repository.target == TARGET
    assert result.parameters.requested_count == 10
    assert result.parameters.competition_id == 1
    assert result.parameters.season_id == 4
    assert not result.parameters.include_previous_season
    assert result.parameters.ordering == "played_on_desc_match_id_asc"
    assert result.parameters.statistic_periods == (
        "goals_first_half",
        "goals_regulation_time",
    )
    assert result.home_sample.venue_condition == "home"
    assert result.away_sample.venue_condition == "away"
    assert result.home_sample.complete and result.away_sample.complete
    assert result.home_sample.insufficient_reason is None
    assert result.away_sample.insufficient_reason is None
    assert result.warnings == ()
    assert len({item.match.id for item in result.home_sample.matches}) == 10


@pytest.mark.asyncio
async def test_service_reports_incomplete_samples_and_absent_target() -> None:
    service = MethodOneSampleService(
        HistoricalFake(),
        SampleFake((SAMPLE_MATCH,), ()),  # type: ignore[arg-type]
    )
    result = await service.get_sample(TARGET.id)
    assert result.home_sample.found_count == 1
    assert not result.home_sample.complete
    assert result.home_sample.insufficient_reason == "insufficient_eligible_matches"
    assert result.away_sample.found_count == 0
    assert result.warnings == ("home_sample_incomplete", "away_sample_incomplete")
    missing = MethodOneSampleService(
        HistoricalFake(None),
        SampleFake((), ()),  # type: ignore[arg-type]
    )
    with pytest.raises(ResourceNotFoundError):
        await missing.get_sample(TARGET.id)


@pytest.fixture
def sample_client(settings: Any) -> TestClient:
    app = create_app(settings, FakeDatabase())
    app.state.method_one_sample_service = MethodOneSampleService(
        HistoricalFake(),
        SampleFake((SAMPLE_MATCH,), ()),  # type: ignore[arg-type]
    )
    with TestClient(app) as client:
        yield client


def test_endpoint_contract_openapi_correlation_and_sanitized_absence(
    sample_client: TestClient,
) -> None:
    response = sample_client.get(
        "/matches/50/method-one/sample", headers={"X-Request-ID": "sample-1"}
    )
    assert response.status_code == 200
    body = response.json()
    assert response.headers["X-Request-ID"] == "sample-1"
    assert body["target_match"]["id"] == 50
    assert body["parameters"]["include_previous_season"] is False
    assert body["home_sample"]["found_count"] == 1
    assert body["away_sample"]["insufficient_reason"] == "insufficient_eligible_matches"
    assert (
        body["home_sample"]["matches"][0]["statistics"]["home"]["first_half"]["goals"]
        == 0
    )
    assert "source_record" not in response.text
    assert "sha256" not in response.text
    paths = sample_client.get("/openapi.json").json()["paths"]
    assert "/matches/{match_id}/method-one/sample" in paths
    operation = paths["/matches/{match_id}/method-one/sample"]["get"]
    assert operation["summary"] == "Build Method 1 historical samples"
    example = operation["responses"]["200"]["content"]["application/json"]["example"]
    assert example["target_match"]["home_team"]["display_name"] == "Example Home"
    assert "source_record" not in str(example)


def test_endpoint_handles_missing_dependency_and_target(settings: Any) -> None:
    with TestClient(create_app(settings, FakeDatabase())) as client:
        unavailable = client.get("/matches/50/method-one/sample")
    assert unavailable.status_code == 503
    app = create_app(settings, FakeDatabase())
    app.state.method_one_sample_service = MethodOneSampleService(
        HistoricalFake(None),
        SampleFake((), ()),  # type: ignore[arg-type]
    )
    with TestClient(app) as client:
        missing = client.get("/matches/50/method-one/sample")
    assert missing.status_code == 404
    assert missing.json()["code"] == "not_found"


class MappingResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def mappings(self) -> MappingResult:
        return self

    def all(self) -> list[dict[str, Any]]:
        return self.rows

    def one_or_none(self) -> dict[str, Any] | None:
        return self.rows[0] if self.rows else None


class SessionFake:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.statements: list[Any] = []

    async def execute(self, statement: Any) -> MappingResult:
        self.statements.append(statement)
        if self.fail:
            raise SQLAlchemyError("synthetic failure")
        row = {
            "competition_id": 1,
            "competition_display_name": "Synthetic League",
            "competition_created_at": NOW,
            "season_id": 4,
            "season_label": "2026",
            "season_created_at": NOW,
            "home_team_id": 2,
            "home_team_display_name": "Synthetic Home",
            "home_team_created_at": NOW,
            "away_team_id": 3,
            "away_team_display_name": "Synthetic Away",
            "away_team_created_at": NOW,
            "match_id": 49,
            "played_on": date(2026, 7, 2),
            "match_created_at": NOW,
            "has_statistics": True,
        }
        for side in ("home", "away"):
            for period in ("first_half", "full_match"):
                row[f"{side}_goals_{period}"] = 0
                row[f"{side}_shots_{period}"] = 1
                row[f"{side}_shots_on_target_{period}"] = 1
                row[f"{side}_corners_{period}"] = 1
            row[f"{side}_fouls_full_match"] = 1
            row[f"{side}_cards_full_match"] = 0
        return MappingResult([row])


class ProviderFake:
    def __init__(self, session: SessionFake) -> None:
        self.session_value = session

    @asynccontextmanager
    async def session(self) -> Any:
        yield self.session_value


class QueryDatabaseFake(ProviderFake):
    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def is_ready(self) -> bool:
        return True


def test_endpoint_composes_postgresql_query_services(settings: Any) -> None:
    with TestClient(create_app(settings, QueryDatabaseFake(SessionFake()))) as client:
        response = client.get("/matches/50/method-one/sample")
    assert response.status_code == 200
    assert response.json()["target_match"]["id"] == 49


@pytest.mark.asyncio
async def test_repository_uses_two_bounded_joined_queries_and_sanitizes_failure() -> (
    None
):
    session = SessionFake()
    repository = SqlAlchemyMethodOneSampleRepository(ProviderFake(session))
    home, away = await repository.get_samples(TARGET)
    assert len(home) == len(away) == 1
    assert home[0].match.id == 49
    assert home[0].statistics.home.first_half.goals == 0
    assert len(session.statements) == 2
    rendered = "\n".join(str(statement) for statement in session.statements)
    assert "LIMIT" in rendered and "matches.played_on <" in rendered
    assert "matches.id <" in rendered and "matches.season_id" in rendered
    failing = SqlAlchemyMethodOneSampleRepository(ProviderFake(SessionFake(True)))
    with pytest.raises(Exception, match="historical sample query failed"):
        await failing.get_samples(TARGET)
