"""Asynchronous PostgreSQL lifecycle and transaction boundary."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from lvfi_api.config import Settings
from lvfi_api.domain.errors import PersistenceUnavailableError


class Database:
    """Own SQLAlchemy resources and expose a narrow transactional interface."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine: AsyncEngine | None = None
        self._sessions: async_sessionmaker[AsyncSession] | None = None

    async def start(self) -> None:
        """Create the lazy PostgreSQL engine and session factory."""
        if self._engine is None:
            self._engine = create_async_engine(
                str(self._settings.database_url),
                pool_pre_ping=True,
                pool_size=self._settings.database_pool_size,
                max_overflow=self._settings.database_max_overflow,
                pool_timeout=self._settings.database_timeout_seconds,
            )
            self._sessions = async_sessionmaker(self._engine, expire_on_commit=False)

    async def stop(self) -> None:
        """Dispose all connections safely during application shutdown."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessions = None

    async def is_ready(self) -> bool:
        """Probe PostgreSQL without exposing infrastructure details to callers."""
        if self._engine is None:
            return False
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception:
            return False
        return True

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Commit successful work and roll back every failed transaction."""
        if self._sessions is None:
            raise PersistenceUnavailableError("database has not been started")
        async with self._sessions() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()
