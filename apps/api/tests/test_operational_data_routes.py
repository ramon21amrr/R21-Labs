"""HTTP coverage for controlled operational-data import endpoints."""

from __future__ import annotations

import os
from csv import writer
from datetime import date
from io import StringIO
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from lvfi_api.config import Settings
from lvfi_api.historical_import import (
    HISTORICAL_HEADERS,
    ImportSummary,
    SourceValidationError,
)
from lvfi_api.infrastructure.database import Database
from lvfi_api.main import create_app
from lvfi_api.persistence.historical_models import matches, statistic_revisions
from lvfi_api.presentation import operational_data_routes


def _csv_body() -> bytes:
    output = StringIO()
    csv_writer = writer(output)
    csv_writer.writerow(HISTORICAL_HEADERS)
    csv_writer.writerow(
        [
            date(2026, 1, 2),
            "League",
            2026,
            "Home",
            "Away",
            1,
            0,
            2,
            1,
            3,
            1,
            6,
            4,
            1,
            1,
            3,
            2,
            2,
            1,
            5,
            3,
            7,
            8,
            1,
            2,
        ]
    )
    return output.getvalue().encode()


def test_preview_import_returns_safe_aggregate(client: TestClient) -> None:
    response = client.post(
        "/administration/imports/preview?filename=matches.csv",
        content=_csv_body(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "source_sha256": response.json()["source_sha256"],
        "sheet_name": "JOGOS",
        "total_records": 1,
        "accepted_records": 1,
        "rejected_records": 0,
        "warning_records": 0,
        "dry_run": True,
        "already_imported": False,
    }


def test_preview_and_confirmation_reject_invalid_or_unavailable_inputs(
    client: TestClient,
) -> None:
    assert (
        client.post(
            "/administration/imports/preview?filename=bad.txt", content=b"x"
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/administration/imports/preview?filename=matches.csv", content=b""
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/administration/imports/preview?filename=matches.csv", content=b"a,b\n"
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/administration/imports/confirm?filename=matches.csv", content=_csv_body()
        ).status_code
        == 503
    )


class _Session:
    async def __aenter__(self) -> _Session:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class _Database:
    def __init__(self) -> None:
        self.value = _Session()

    def session(self) -> _Session:
        return self.value

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def is_ready(self) -> bool:
        return True


class _Importer:
    def __init__(self, session: object) -> None:
        self.session = session

    async def execute(
        self, source: object, sheet_name: str, actor: object, dry_run: bool
    ) -> ImportSummary:
        return ImportSummary("A" * 64, sheet_name, 1, 1, 0, 0, dry_run)


class _InvalidImporter(_Importer):
    async def execute(
        self, source: object, sheet_name: str, actor: object, dry_run: bool
    ) -> ImportSummary:
        raise SourceValidationError("synthetic")


def test_confirmation_uses_database_session_and_returns_aggregate(
    settings: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = _Database()
    app = create_app(settings, database)
    monkeypatch.setattr(operational_data_routes, "HistoricalImporter", _Importer)
    with TestClient(app) as client:
        response = client.post(
            "/administration/imports/confirm?filename=matches.csv", content=_csv_body()
        )
    assert response.status_code == 200
    assert response.json()["dry_run"] is False


def test_confirmation_sanitizes_source_validation_errors(
    settings: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = create_app(settings, _Database())
    monkeypatch.setattr(operational_data_routes, "HistoricalImporter", _InvalidImporter)
    with TestClient(app) as client:
        response = client.post(
            "/administration/imports/confirm?filename=matches.csv", content=_csv_body()
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_postgresql_operational_workflow_is_idempotent_and_append_only() -> None:
    database_url = os.environ.get("LVFI_DATABASE_URL")
    if database_url is None or "127.0.0.1:55432" not in database_url:
        pytest.skip("requires the isolated Codex PostgreSQL task database")

    database = Database(
        Settings(
            environment="test",
            app_name="lvfi-postgresql-operational-test",
            database_url=database_url,
        )
    )
    app = create_app(
        Settings(
            environment="test",
            app_name="lvfi-postgresql-operational-test",
            database_url=database_url,
        ),
        database,
    )
    with TestClient(app) as client:
        preview = client.post(
            "/administration/imports/preview?filename=matches.csv", content=_csv_body()
        )
        confirmed = client.post(
            "/administration/imports/confirm?filename=matches.csv", content=_csv_body()
        )
        repeated = client.post(
            "/administration/imports/confirm?filename=matches.csv", content=_csv_body()
        )
        future = client.post(
            "/administration/matches",
            json={
                "played_on": "2030-01-02",
                "competition": "Future League",
                "season": "2030",
                "home_team": "Future Home",
                "away_team": "Future Away",
            },
        )
        duplicate = client.post(
            "/administration/matches",
            json={
                "played_on": "2030-01-02",
                "competition": "Future League",
                "season": "2030",
                "home_team": "Future Home",
                "away_team": "Future Away",
            },
        )

        engine = create_async_engine(database_url)
        try:
            async with engine.connect() as connection:
                match_id = await connection.scalar(
                    select(matches.c.id).order_by(matches.c.id)
                )
            assert match_id is not None
            available = client.post(
                f"/administration/matches/{match_id}/statistic-revisions",
                json={
                    "statistic_field": "home_goals_full_match",
                    "availability": "available",
                    "new_value": 3,
                    "reason": "verified correction",
                },
            )
            missing = client.post(
                f"/administration/matches/{match_id}/statistic-revisions",
                json={
                    "statistic_field": "home_goals_full_match",
                    "availability": "missing",
                    "new_value": None,
                    "reason": "source later unavailable",
                },
            )
            revision_id = available.json()["revision_id"]
            with pytest.raises(DBAPIError, match="append-only"):
                async with engine.begin() as connection:
                    await connection.execute(
                        update(statistic_revisions)
                        .where(statistic_revisions.c.id == revision_id)
                        .values(reason="must fail")
                    )
        finally:
            await engine.dispose()

    assert preview.status_code == 200 and preview.json()["dry_run"] is True
    assert (
        confirmed.status_code == 200
        and confirmed.json()["already_imported"] is False
    )
    assert repeated.status_code == 200 and repeated.json()["already_imported"] is True
    assert future.status_code == 201 and duplicate.status_code == 422
    assert available.status_code == 201 and available.json()["previous_value"] == 2
    assert missing.status_code == 201 and missing.json()["availability"] == "missing"
    assert missing.json()["new_value"] is None
