"""Unit tests for PostgreSQL lifecycle, readiness, and transaction boundaries."""

from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from lvfi_api.config import Settings
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.infrastructure.database import Database


class FakeConnection:
    async def execute(self, statement: object) -> None:
        self.statement = statement

    async def __aenter__(self) -> FakeConnection:
        return self

    async def __aexit__(self, *arguments: object) -> None:
        return None


class FailingConnection(FakeConnection):
    async def execute(self, statement: object) -> None:
        raise OSError("database offline")


class FakeEngine:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.disposed = False

    def connect(self) -> FakeConnection:
        return self.connection

    async def dispose(self) -> None:
        self.disposed = True


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, *arguments: object) -> None:
        return None


class FakeSessions:
    def __init__(self, session: FakeSession) -> None:
        self.session = session

    def __call__(self) -> FakeSession:
        return self.session


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        app_name="lvfi-api-test",
        database_url="postgresql+asyncpg://lvfi:lvfi@127.0.0.1:5432/lvfi_test",
    )


@pytest.mark.asyncio
async def test_database_start_stop_and_unstarted_readiness(settings: Settings) -> None:
    database = Database(settings)

    assert await database.is_ready() is False
    await database.start()
    await database.start()
    await database.stop()
    await database.stop()


@pytest.mark.asyncio
async def test_database_readiness_handles_success_and_connection_failure(
    settings: Settings,
) -> None:
    database = Database(settings)
    database._engine = cast(AsyncEngine, FakeEngine(FakeConnection()))

    assert await database.is_ready() is True

    database._engine = cast(AsyncEngine, FakeEngine(FailingConnection()))
    assert await database.is_ready() is False


@pytest.mark.asyncio
async def test_database_session_commits_and_rolls_back(settings: Settings) -> None:
    database = Database(settings)
    committed = FakeSession()
    database._sessions = cast(async_sessionmaker[AsyncSession], FakeSessions(committed))

    async with database.session() as yielded:
        assert isinstance(yielded, FakeSession)
        assert yielded is committed
    assert committed.committed is True

    rolled_back = FakeSession()
    database._sessions = cast(
        async_sessionmaker[AsyncSession], FakeSessions(rolled_back)
    )
    with pytest.raises(ValueError, match="failure"):
        async with database.session():
            raise ValueError("failure")
    assert rolled_back.rolled_back is True


@pytest.mark.asyncio
async def test_database_session_requires_start(settings: Settings) -> None:
    database = Database(settings)

    with pytest.raises(PersistenceUnavailableError, match="not been started"):
        async with database.session():
            pass
