"""Shared LVFI API settings and lifecycle-safe fake infrastructure."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from lvfi_api.application.local_admin_authentication import ADMIN_USERNAME
from lvfi_api.config import Settings
from lvfi_api.main import create_app
from lvfi_api.presentation.local_admin_authentication_routes import (
    require_authenticated_admin,
)


class FakeDatabase:
    """Deterministic dependency fake for HTTP tests without a real database."""

    def __init__(self, ready: bool = True) -> None:
        self.ready = ready
        self.started = False
        self.stopped = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def is_ready(self) -> bool:
        return self.ready


@pytest.fixture(autouse=True)
def authenticated_test_client(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    """Inject authentication only at the TestClient boundary for legacy tests."""
    if request.node.get_closest_marker("real_auth"):
        return

    original = TestClient.__init__

    def initialize(
        client: TestClient, app: object, *args: object, **kwargs: object
    ) -> None:
        app.dependency_overrides[require_authenticated_admin] = lambda: ADMIN_USERNAME  # type: ignore[union-attr]
        original(client, app, *args, **kwargs)

    monkeypatch.setattr(TestClient, "__init__", initialize)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        app_name="lvfi-api-test",
        database_url="postgresql+asyncpg://lvfi:lvfi@127.0.0.1:5432/lvfi_test",
    )


@pytest.fixture
def database() -> FakeDatabase:
    return FakeDatabase()


@pytest.fixture
def client(settings: Settings, database: FakeDatabase) -> Iterator[TestClient]:
    with TestClient(create_app(settings, database)) as test_client:
        yield test_client
