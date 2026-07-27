"""Synthetic public-boundary tests for APP-006 Method One execution."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient

from lvfi_api.application.method_one_execution import (
    MethodOneExecutionService,
    build_method_one_request,
)
from lvfi_api.domain.errors import MethodOneEngineError, MethodOneSampleIncompleteError
from lvfi_api.domain.historical_queries import (
    Match,
    MatchStatistics,
    MethodOneSample,
    MethodOneSampleMatch,
    MethodOneSampleParameters,
    MethodOneTeamSample,
    Reference,
    Season,
    StatisticsPeriod,
    TeamStatistics,
)
from lvfi_api.main import create_app

from .conftest import FakeDatabase

NOW = datetime(2026, 1, 1, tzinfo=UTC)
COMPETITION = Reference(1, "Synthetic League", NOW)
HOME = Reference(2, "Home", NOW)
AWAY = Reference(3, "Away", NOW)
SEASON = Season(4, COMPETITION, "2026", NOW)
TARGET = Match(100, date(2026, 7, 10), COMPETITION, SEASON, HOME, AWAY, True, NOW)


def _statistics(match_id: int, home_goals: int, away_goals: int) -> MatchStatistics:
    first_home = StatisticsPeriod(0, 1, 1, 1, None, None)
    first_away = StatisticsPeriod(0, 1, 1, 1, None, None)
    return MatchStatistics(
        match_id,
        TeamStatistics(first_home, StatisticsPeriod(home_goals, 1, 1, 1, 1, 0)),
        TeamStatistics(first_away, StatisticsPeriod(away_goals, 1, 1, 1, 1, 0)),
    )


def _past(match_id: int, home: Reference, away: Reference) -> MethodOneSampleMatch:
    match = Match(
        match_id,
        date(2026, 7, 9),
        COMPETITION,
        SEASON,
        home,
        away,
        True,
        NOW,
    )
    return MethodOneSampleMatch(match, _statistics(match_id, 2, 1))


def sample(*, complete: bool = True) -> MethodOneSample:
    count = 10 if complete else 9
    home = tuple(_past(index, HOME, AWAY) for index in range(1, count + 1))
    away = tuple(_past(index + 20, HOME, AWAY) for index in range(1, count + 1))
    return MethodOneSample(
        TARGET,
        MethodOneSampleParameters(
            10,
            1,
            4,
            False,
            "played_on_desc_match_id_asc",
            ("goals_first_half", "goals_regulation_time"),
        ),
        MethodOneTeamSample(
            "home",
            10,
            count,
            complete,
            None if complete else "insufficient_eligible_matches",
            home,
        ),
        MethodOneTeamSample(
            "away",
            10,
            count,
            complete,
            None if complete else "insufficient_eligible_matches",
            away,
        ),
        (),
    )


class Provider:
    def __init__(self, value: MethodOneSample) -> None:
        self.value = value

    async def get_sample(self, match_id: int) -> MethodOneSample:
        assert match_id == TARGET.id
        return self.value


@pytest.mark.asyncio
async def test_executes_deterministically_and_maps_exact_public_contract() -> None:
    source = sample()
    request = build_method_one_request(source)
    assert request.period.value == "regulation_time"
    assert request.configuration.configuration_version == "1.0.0"
    assert request.series_references[0].snapshot.observations[0].value.value == 2.0
    assert request.series_references[1].snapshot.observations[0].value.value == 1.0
    assert request.series_references[2].snapshot.observations[0].value.value == 1.0
    assert request.series_references[3].snapshot.observations[0].value.value == 2.0
    first = await MethodOneExecutionService(Provider(source)).execute(TARGET.id)
    second = await MethodOneExecutionService(Provider(source)).execute(TARGET.id)
    assert first.payload.canonical_bytes == second.payload.canonical_bytes
    assert first.payload.method_version == "1.0.0"
    assert first.payload.package_version == "1.1.1"
    assert first.payload.schema_version == 1


@pytest.mark.asyncio
async def test_blocks_incomplete_sample_before_engine_execution() -> None:
    with pytest.raises(MethodOneSampleIncompleteError):
        await MethodOneExecutionService(Provider(sample(complete=False))).execute(
            TARGET.id
        )


def test_endpoint_openapi_correlation_and_sanitized_block(settings: object) -> None:
    app = create_app(settings, FakeDatabase())
    app.state.method_one_execution_service = MethodOneExecutionService(
        Provider(sample())
    )
    with TestClient(app) as client:
        response = client.post(
            "/matches/100/method-one/pricing", headers={"X-Request-ID": "method-1"}
        )
        openapi = client.get("/openapi.json").json()
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "method-1"
    assert response.json()["root_type"] == "MethodOneFinalResult"
    assert response.json()["content_hash"]
    assert "/matches/{match_id}/method-one/pricing" in openapi["paths"]
    blocked = create_app(settings, FakeDatabase())
    blocked.state.method_one_execution_service = MethodOneExecutionService(
        Provider(sample(complete=False))
    )
    with TestClient(blocked) as client:
        failure = client.post("/matches/100/method-one/pricing")
    assert failure.status_code == 422
    assert failure.json()["code"] == "method_one_sample_incomplete"


class BrokenEngine:
    def run(self, request: object) -> object:
        return object()

    def serialize(self, result: object) -> object:
        return object()

    def sha256(self, value: object) -> object:
        return "a" * 64


@pytest.mark.asyncio
async def test_engine_failure_is_typed_before_public_handler() -> None:
    with pytest.raises(MethodOneEngineError):
        await MethodOneExecutionService(Provider(sample()), BrokenEngine()).execute(
            TARGET.id
        )
