"""Public read-only result routes for Match Center."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from lvfi_api.domain.method_three import MethodThreeConfiguration
from lvfi_api.domain.method_two import MethodTwoConfiguration
from lvfi_api.main import create_app
from lvfi_api.presentation.method_result_routes import (
    get_method_three_service,
    get_method_two_service,
)


@dataclass(frozen=True)
class _Result:
    method: str
    method_version: str
    status: str
    evidence: dict[str, object]


class _MethodTwoService:
    def __init__(self) -> None:
        self.calls: list[tuple[int, MethodTwoConfiguration]] = []

    async def execute(
        self, match_id: int, configuration: MethodTwoConfiguration
    ) -> _Result:
        self.calls.append((match_id, configuration))
        return _Result(
            "method_two_adjusted_poisson",
            "1.0.0",
            "completed",
            {"sample_match_ids": (9, 8), "home_lambda": 1.25},
        )


class _MethodThreeService:
    def __init__(self) -> None:
        self.calls: list[tuple[int, MethodThreeConfiguration]] = []

    async def execute(
        self, match_id: int, configuration: MethodThreeConfiguration
    ) -> _Result:
        self.calls.append((match_id, configuration))
        return _Result(
            "method_three_observed_frequency",
            "1.0.0",
            "completed",
            {"sample_match_ids": (9, 8), "frequency": 0.5},
        )


def test_method_result_routes_delegate_to_existing_services(
    settings: Any, database: Any
) -> None:
    app = create_app(settings, database)
    method_two = _MethodTwoService()
    method_three = _MethodThreeService()
    app.state.method_two_service = method_two
    app.state.method_three_service = method_three
    with TestClient(app) as client:
        two = client.get(
            "/matches/101/method-two/result",
            params={
                "sample_size": 10,
                "context": "venue",
                "season_scope": "current",
                "metric": "goals_scored",
            },
        )
        three = client.get(
            "/matches/101/method-three/result",
            params={
                "sample_size": 10,
                "competition_scope": "target_competition",
                "season_scope": "current",
                "metric": "goals_scored",
                "comparator": "at_least",
                "achievement_target": 1,
            },
        )

    assert two.status_code == 200
    assert two.json() == {
        "method": "method_two_adjusted_poisson",
        "method_version": "1.0.0",
        "payload": {
            "method": "method_two_adjusted_poisson",
            "method_version": "1.0.0",
            "status": "completed",
            "evidence": {"sample_match_ids": [9, 8], "home_lambda": 1.25},
        },
    }
    assert method_two.calls == [
        (
            101,
            MethodTwoConfiguration(10, "venue", "current", None, "goals_scored"),
        )
    ]
    assert three.status_code == 200
    assert three.json()["payload"]["evidence"]["frequency"] == 0.5
    assert method_three.calls == [
        (
            101,
            MethodThreeConfiguration(
                10,
                "target_competition",
                "current",
                None,
                "goals_scored",
                "at_least",
                1,
            ),
        )
    ]


def test_method_result_routes_require_explicit_compatible_selectors(
    settings: Any, database: Any
) -> None:
    app = create_app(settings, database)
    two = _MethodTwoService()
    three = _MethodThreeService()
    app.state.method_two_service = two
    app.state.method_three_service = three
    with TestClient(app) as client:
        missing = client.get("/matches/101/method-two/result")
        incompatible = client.get(
            "/matches/101/method-three/result",
            params={
                "sample_size": 10,
                "competition_scope": "target_competition",
                "season_scope": "current",
                "previous_season_id": 4,
                "metric": "goals_scored",
                "comparator": "at_least",
                "achievement_target": 1,
                "unsupported": "x",
            },
        )

    assert missing.status_code == 422
    assert incompatible.status_code == 422
    assert not two.calls
    assert not three.calls


def test_method_result_routes_reject_noncanonical_sample_and_season_combinations(
    settings: Any, database: Any
) -> None:
    app = create_app(settings, database)
    two = _MethodTwoService()
    three = _MethodThreeService()
    app.state.method_two_service = two
    app.state.method_three_service = three
    with TestClient(app) as client:
        noncanonical_two = client.get(
            "/matches/101/method-two/result",
            params={
                "sample_size": 6,
                "context": "venue",
                "season_scope": "current",
                "metric": "goals_scored",
            },
        )
        noncanonical_three = client.get(
            "/matches/101/method-three/result",
            params={
                "sample_size": 6,
                "competition_scope": "target_competition",
                "season_scope": "current",
                "metric": "goals_scored",
                "comparator": "at_least",
                "achievement_target": 1,
            },
        )
        missing_previous_three = client.get(
            "/matches/101/method-three/result",
            params={
                "sample_size": 10,
                "competition_scope": "target_competition",
                "season_scope": "current_and_previous",
                "metric": "goals_scored",
                "comparator": "at_least",
                "achievement_target": 1,
            },
        )
        current_with_previous_three = client.get(
            "/matches/101/method-three/result",
            params={
                "sample_size": 10,
                "competition_scope": "target_competition",
                "season_scope": "current",
                "previous_season_id": 9,
                "metric": "goals_scored",
                "comparator": "at_least",
                "achievement_target": 1,
            },
        )
        previous_two = client.get(
            "/matches/101/method-two/result",
            params={
                "sample_size": 5,
                "context": "overall",
                "season_scope": "current_and_previous",
                "previous_season_id": 9,
                "metric": "corners",
            },
        )

    assert noncanonical_two.status_code == 422
    assert noncanonical_three.status_code == 422
    assert missing_previous_three.status_code == 422
    assert current_with_previous_three.status_code == 422
    assert previous_two.status_code == 200
    assert two.calls[-1] == (
        101,
        MethodTwoConfiguration(5, "overall", "current_and_previous", 9, "corners"),
    )


@pytest.mark.asyncio
async def test_method_result_route_dependencies_compose_existing_statistics_port(
    settings: Any, database: Any
) -> None:
    app = create_app(settings, database)
    app.state.statistics_sample_service = object()
    request = Request({"type": "http", "app": app})

    assert isinstance(await get_method_two_service(request), object)
    assert isinstance(await get_method_three_service(request), object)
