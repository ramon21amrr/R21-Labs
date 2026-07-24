"""Operational endpoint, correlation, and safe-error tests."""

from __future__ import annotations

from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from lvfi_api.config import Settings
from lvfi_api.main import create_app

from .conftest import FakeDatabase


def test_application_metadata_and_openapi(
    settings: Settings, database: FakeDatabase
) -> None:
    app = create_app(settings, database)

    assert app.title == "lvfi-api-test"
    assert app.version == "0.1.0"
    assert "/health" in app.openapi()["paths"]


def test_health_accepts_provided_correlation_id(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-123"
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_health_generates_correlation_id_for_absent_or_unsafe_value(
    client: TestClient,
) -> None:
    generated = client.get("/health")
    unsafe = client.get("/health", headers={"X-Request-ID": "invalid\nvalue"})

    assert UUID(generated.headers["X-Request-ID"]).version == 4
    assert UUID(unsafe.headers["X-Request-ID"]).version == 4


def test_ready_returns_ready_when_database_is_available(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "version": "0.1.0"}


def test_ready_returns_sanitized_error_when_database_is_unavailable(
    settings: Settings,
) -> None:
    with TestClient(create_app(settings, FakeDatabase(ready=False))) as client:
        response = client.get("/ready", headers={"X-Request-ID": "correlated"})

    assert response.status_code == 503
    assert response.json() == {
        "code": "dependency_unavailable",
        "message": "service unavailable",
        "correlation_id": "correlated",
    }


def test_unexpected_errors_are_sanitized(settings: Settings) -> None:
    app: FastAPI = create_app(settings, FakeDatabase())

    @app.get("/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("database password must not leave the server")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/unexpected")

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "password" not in response.text
