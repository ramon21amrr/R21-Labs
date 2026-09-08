"""Public API coverage for the configurable reusable statistics endpoint."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from lvfi_api.domain.errors import ResourceNotFoundError
from lvfi_api.domain.statistics import (
    StatisticsCandidate,
    StatisticsSample,
    StatisticsSampleRequest,
    StatisticsTarget,
    UnavailableValue,
    ValueFrequency,
)
from lvfi_api.main import create_app
from lvfi_api.presentation.statistics_routes import get_statistics_sample_service

from .conftest import FakeDatabase

TARGET = StatisticsTarget(
    match_id=100,
    played_on=date(2026, 7, 10),
    competition_id=1,
    competition_name="League",
    season_id=10,
    season_label="2026",
    home_team_id=7,
    home_team_name="Home",
    away_team_id=8,
    away_team_name="Away",
)
CANDIDATE = StatisticsCandidate(
    match_id=99,
    played_on=date(2026, 7, 9),
    competition_id=1,
    competition_name="League",
    season_id=10,
    season_label="2026",
    home_team_id=7,
    home_team_name="Home",
    away_team_id=9,
    away_team_name="Other",
    venue="home",
    value=0,
    unavailable_reason=None,
)


def sample(request: StatisticsSampleRequest) -> StatisticsSample:
    return StatisticsSample(
        target=TARGET,
        request=request,
        ordering="played_on_desc_match_id_asc",
        candidate_count=2,
        used_count=1,
        candidate_match_ids=(99, 98),
        used_match_ids=(99,),
        candidates=(
            CANDIDATE,
            replace(
                CANDIDATE,
                match_id=98,
                value=None,
                unavailable_reason="statistic_unavailable",
            ),
        ),
        used_matches=(CANDIDATE,),
        valid_values=(0,),
        unavailable_values=(UnavailableValue(98, "statistic_unavailable"),),
        available_count=1,
        mean=0,
        population_standard_deviation=0,
        coefficient_of_variation=None,
        frequencies=(ValueFrequency(0, 1),),
        achievement_count=1 if request.comparator else None,
        achievement_rate=1 if request.comparator else None,
        warnings=("sample_partial", "unavailable_values", "low_available_observations"),
    )


class ServiceFake:
    def __init__(self, *, missing: bool = False) -> None:
        self.missing = missing
        self.calls: list[tuple[int, StatisticsSampleRequest]] = []

    async def get_sample(
        self, match_id: int, request: StatisticsSampleRequest
    ) -> StatisticsSample:
        self.calls.append((match_id, request))
        if self.missing:
            raise ResourceNotFoundError("match")
        return sample(request)


class MethodOneMustNotBeRead:
    def __getattr__(self, _: str) -> object:
        raise AssertionError("statistics endpoint must not access Method 1")


class DatabaseWithSession(FakeDatabase):
    def session(self) -> object:
        return object()


@pytest.fixture
def statistics_client(settings: Any) -> Iterator[tuple[TestClient, ServiceFake]]:
    service = ServiceFake()
    app = create_app(settings, FakeDatabase())
    app.state.statistics_sample_service = service
    app.state.method_one_sample_service = MethodOneMustNotBeRead()
    with TestClient(app) as client:
        yield client, service


def test_statistics_endpoint_exposes_public_dto_and_explicit_filters(
    statistics_client: tuple[TestClient, ServiceFake],
) -> None:
    client, service = statistics_client
    response = client.get(
        "/matches/100/statistics/sample",
        params={
            "team_id": 7,
            "sample_size": 20,
            "venue": "home",
            "competition_scope": "all_eligible",
            "season_scope": "current_and_previous",
            "previous_season_id": 9,
            "metric": "corners",
            "comparator": "at_least",
            "achievement_target": 0,
        },
        headers={"X-Request-ID": "statistics-request"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "statistics-request"
    assert service.calls == [
        (
            100,
            StatisticsSampleRequest(
                team_id=7,
                sample_size=20,
                venue="home",
                competition_scope="all_eligible",
                season_scope="current_and_previous",
                previous_season_id=9,
                metric="corners",
                comparator="at_least",
                achievement_target=0,
            ),
        )
    ]
    body = response.json()
    assert body["target_match"]["match_id"] == 100
    assert body["filters"] == {
        "team_id": 7,
        "sample_size": 20,
        "venue": "home",
        "competition_scope": "all_eligible",
        "season_scope": "current_and_previous",
        "previous_season_id": 9,
        "metric": "corners",
        "comparator": "at_least",
        "achievement_target": 0,
    }
    assert body["candidate_match_ids"] == [99, 98]
    assert body["used_match_ids"] == [99]
    assert body["valid_values"] == [0]
    assert body["unavailable_values"] == [
        {"match_id": 98, "reason": "statistic_unavailable"}
    ]
    assert body["mean"] == body["standard_deviation"] == 0
    assert body["coefficient_of_variation"] is None
    assert body["frequencies"] == [{"value": 0, "count": 1}]
    assert "source_record" not in response.text
    assert "method_one" not in response.text


@pytest.mark.parametrize(
    "url",
    [
        "/matches/100/statistics/sample?team_id=7&sample_size=6",
        "/matches/100/statistics/sample?team_id=7&venue=neutral",
        "/matches/100/statistics/sample?team_id=7&season_scope=current_and_previous",
        "/matches/100/statistics/sample?team_id=7&previous_season_id=9",
        "/matches/100/statistics/sample?team_id=7&comparator=equal",
        "/matches/100/statistics/sample?team_id=7&achievement_target=1",
        "/matches/100/statistics/sample?team_id=7&unsupported=x",
    ],
)
def test_statistics_endpoint_validates_all_public_filters(
    statistics_client: tuple[TestClient, ServiceFake], url: str
) -> None:
    client, service = statistics_client

    response = client.get(url)

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_request"
    assert not service.calls


def test_statistics_endpoint_sanitizes_absence_and_missing_dependency(
    settings: Any,
) -> None:
    app = create_app(settings, FakeDatabase())
    app.state.statistics_sample_service = ServiceFake(missing=True)
    with TestClient(app) as client:
        missing = client.get("/matches/100/statistics/sample?team_id=7")
    assert missing.status_code == 404
    assert missing.json()["code"] == "not_found"
    assert "match" not in missing.text

    with TestClient(create_app(settings, FakeDatabase())) as client:
        unavailable = client.get("/matches/100/statistics/sample?team_id=7")
    assert unavailable.status_code == 503
    assert unavailable.json()["code"] == "dependency_unavailable"


@pytest.mark.asyncio
async def test_statistics_dependency_builds_sqlalchemy_service(settings: Any) -> None:
    app = create_app(settings, DatabaseWithSession())
    request = Request({"type": "http", "app": app})

    service = await get_statistics_sample_service(request)

    assert service.__class__.__name__ == "StatisticsSampleService"


def test_statistics_endpoint_is_present_in_openapi(
    statistics_client: tuple[TestClient, ServiceFake],
) -> None:
    client, _ = statistics_client
    operation = client.get("/openapi.json").json()["paths"][
        "/matches/{match_id}/statistics/sample"
    ]["get"]

    assert (
        operation["summary"]
        == "Build a configurable reusable historical statistics sample"
    )
    parameter_names = {item["name"] for item in operation["parameters"]}
    assert {"team_id", "sample_size", "venue", "metric"} <= parameter_names
    response_schema = operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    response_name = response_schema["$ref"].rsplit("/", maxsplit=1)[1]
    filters_schema = client.get("/openapi.json").json()["components"]["schemas"][
        response_name
    ]["properties"]["filters"]
    assert filters_schema["$ref"].endswith("/StatisticsSampleFiltersResponse")
