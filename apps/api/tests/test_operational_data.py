"""Unit tests for manual-match and statistic-revision command validation."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.application.operational_data import OperationalDataService
from lvfi_api.domain.errors import (
    InvalidQueryError,
    PersistenceUnavailableError,
    ResourceNotFoundError,
)
from lvfi_api.domain.operational_data import (
    FutureMatch,
    FutureMatchDraft,
    StatisticRevision,
    StatisticRevisionDraft,
)
from lvfi_api.main import create_app
from lvfi_api.persistence.operational_data import SqlAlchemyOperationalDataRepository
from lvfi_api.presentation.operational_data_routes import get_operational_data_service

NOW = datetime(2026, 9, 6, tzinfo=UTC)


class RepositoryFake:
    def __init__(self, found: bool = True) -> None:
        self.found = found
        self.future: FutureMatchDraft | None = None
        self.revision: StatisticRevisionDraft | None = None

    async def create_future_match(self, draft: FutureMatchDraft) -> FutureMatch | None:
        self.future = draft
        return (
            FutureMatch(
                7,
                draft.played_on,
                draft.competition,
                draft.season,
                draft.home_team,
                draft.away_team,
                draft.actor,
                NOW,
            )
            if self.found
            else None
        )

    async def revise_statistic(
        self, draft: StatisticRevisionDraft
    ) -> StatisticRevision | None:
        self.revision = draft
        return (
            StatisticRevision(
                9,
                draft.match_id,
                draft.statistic_field,
                1,
                draft.availability,
                draft.new_value,
                draft.actor,
                draft.reason,
                NOW,
            )
            if self.found
            else None
        )


def _future() -> FutureMatchDraft:
    return FutureMatchDraft(
        date(2026, 10, 1), "League", "2026", "Home", "Away", "local-admin"
    )


def _revision(**changes: object) -> StatisticRevisionDraft:
    values: dict[str, object] = {
        "match_id": 7,
        "statistic_field": "home_goals_full_match",
        "availability": "available",
        "new_value": 2,
        "actor": "local-admin",
        "reason": "source correction",
    }
    values.update(changes)
    return StatisticRevisionDraft(**values)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_service_accepts_valid_manual_commands() -> None:
    repository = RepositoryFake()
    service = OperationalDataService(repository)

    future = await service.create_future_match(_future())
    revision = await service.revise_statistic(_revision())
    missing = await service.revise_statistic(
        _revision(availability="missing", new_value=None)
    )

    assert future.match_id == 7
    assert repository.future == _future()
    assert revision.new_value == 2
    assert missing.new_value is None


@pytest.mark.asyncio
async def test_service_blocks_invalid_commands_and_missing_records() -> None:
    service = OperationalDataService(RepositoryFake(found=False))
    with pytest.raises(InvalidQueryError):
        await service.create_future_match(
            FutureMatchDraft(date.today(), "", "2026", "Home", "Away", "admin")
        )
    with pytest.raises(InvalidQueryError):
        await service.create_future_match(
            FutureMatchDraft(date.today(), "League", "2026", "Home", " home ", "admin")
        )
    with pytest.raises(InvalidQueryError):
        await service.revise_statistic(_revision(statistic_field="bad"))
    with pytest.raises(InvalidQueryError):
        await service.revise_statistic(_revision(new_value=-1))
    with pytest.raises(InvalidQueryError):
        await service.revise_statistic(_revision(availability="missing", new_value=0))
    with pytest.raises(InvalidQueryError):
        await service.create_future_match(_future())
    with pytest.raises(ResourceNotFoundError):
        await service.revise_statistic(_revision())


def test_administrative_routes_use_the_injected_operational_service(
    settings: Any, database: Any
) -> None:
    repository = RepositoryFake()
    app = create_app(settings, database)
    app.state.operational_data_service = OperationalDataService(repository)

    with TestClient(app) as client:
        created = client.post(
            "/administration/matches",
            json={
                "played_on": "2026-10-01",
                "competition": "League",
                "season": "2026",
                "home_team": "Home",
                "away_team": "Away",
            },
        )
        revised = client.post(
            "/administration/matches/7/statistic-revisions",
            json={
                "statistic_field": "home_goals_full_match",
                "availability": "available",
                "new_value": 2,
                "reason": "source correction",
            },
        )
        invalid = client.post(
            "/administration/matches",
            json={
                "played_on": "invalid",
                "competition": "League",
                "season": "2026",
                "home_team": "Home",
                "away_team": "Away",
            },
        )

    assert created.status_code == 201
    assert created.json()["match_id"] == 7
    assert revised.status_code == 201
    assert revised.json()["revision_id"] == 9
    assert invalid.status_code == 422


class _Result:
    def __init__(self, value: int | dict[str, object] | None) -> None:
        self.value = value

    def scalar_one(self) -> int:
        assert isinstance(self.value, int)
        return self.value

    def mappings(self) -> _Result:
        return self

    def one(self) -> dict[str, object]:
        assert isinstance(self.value, dict)
        return self.value


class _Session:
    def __init__(
        self,
        scalars: list[int | None] | None = None,
        results: list[int | dict[str, object] | None] | None = None,
        fail: bool = False,
    ) -> None:
        self.scalars = list(scalars or [])
        self.results = list(results or [])
        self.fail = fail
        self.executions = 0

    async def scalar(self, statement: object) -> int | None:
        if self.fail:
            raise SQLAlchemyError("synthetic")
        return self.scalars.pop(0)

    async def execute(self, statement: object) -> _Result:
        if self.fail:
            raise SQLAlchemyError("synthetic")
        self.executions += 1
        return _Result(self.results.pop(0) if self.results else None)


class _Database:
    def __init__(self, session: _Session) -> None:
        self.value = session

    @asynccontextmanager
    async def session(self) -> Any:
        yield self.value


def _future_row() -> dict[str, object]:
    return {"id": 70, "created_at": NOW}


def _revision_row(availability: str = "available") -> dict[str, object]:
    return {
        "id": 90,
        "match_id": 7,
        "statistic_field": "home_goals_full_match",
        "previous_value": 1,
        "new_value": 2 if availability == "available" else None,
        "availability": availability,
        "actor": "local-admin",
        "reason": "source correction",
        "created_at": NOW,
    }


@pytest.mark.asyncio
async def test_sqlalchemy_repository_writes_future_matches_and_append_only_revisions(
) -> None:
    future_session = _Session(
        [None, None, None, None, None], [1, 2, 3, 4, _future_row()]
    )
    future_repository = SqlAlchemyOperationalDataRepository(_Database(future_session))
    future = await future_repository.create_future_match(_future())
    assert future is not None and future.match_id == 70
    assert future_session.executions == 5

    available_session = _Session([1], [_revision_row(), None])
    available_repository = SqlAlchemyOperationalDataRepository(
        _Database(available_session)
    )
    available = await available_repository.revise_statistic(_revision())
    assert available is not None and available.previous_value == 1
    assert available_session.executions == 2

    missing_session = _Session([1], [_revision_row("missing")])
    missing_repository = SqlAlchemyOperationalDataRepository(_Database(missing_session))
    missing = await missing_repository.revise_statistic(
        _revision(availability="missing", new_value=None)
    )
    assert missing is not None and missing.new_value is None
    assert missing_session.executions == 1


@pytest.mark.asyncio
async def test_sqlalchemy_repository_handles_conflicts_absence_and_database_failures(
) -> None:
    conflict = await SqlAlchemyOperationalDataRepository(
        _Database(_Session([1, 2, 3, 4, 70]))
    ).create_future_match(_future())
    assert conflict is None
    absent_repository = SqlAlchemyOperationalDataRepository(_Database(_Session([None])))
    absent = await absent_repository.revise_statistic(_revision())
    assert absent is None
    failing = SqlAlchemyOperationalDataRepository(_Database(_Session(fail=True)))
    with pytest.raises(PersistenceUnavailableError, match="operational match"):
        await failing.create_future_match(_future())
    with pytest.raises(PersistenceUnavailableError, match="statistic revision"):
        await failing.revise_statistic(_revision())


@pytest.mark.asyncio
async def test_operational_dependency_builds_repository_and_rejects_missing_session(
) -> None:
    available = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(database=_Database(_Session())))
    )
    assert isinstance(
        await get_operational_data_service(available),  # type: ignore[arg-type]
        OperationalDataService,
    )
    missing = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(database=object()))
    )
    with pytest.raises(PersistenceUnavailableError, match="write session"):
        await get_operational_data_service(missing)  # type: ignore[arg-type]
