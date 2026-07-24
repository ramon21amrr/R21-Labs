"""Shared LVFI API settings and lifecycle-safe fake infrastructure."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from lvfi_api.config import Settings
from lvfi_api.main import create_app


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
