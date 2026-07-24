"""Minimal operational routes, deliberately without business endpoints."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from fastapi import APIRouter, Request
from pydantic import BaseModel

from lvfi_api.domain.errors import PersistenceUnavailableError


@runtime_checkable
class ReadinessDatabase(Protocol):
    """Only the health dependency required by the readiness route."""

    async def is_ready(self) -> bool: ...


class HealthResponse(BaseModel):
    status: str
    version: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["operations"])
async def health(request: Request) -> HealthResponse:
    """Show that the API process is running without touching PostgreSQL."""
    return HealthResponse(status="ok", version=request.app.version)


@router.get("/ready", response_model=HealthResponse, tags=["operations"])
async def ready(request: Request) -> HealthResponse:
    """Show that required persistence infrastructure can serve the API."""
    database = request.app.state.database
    if not isinstance(database, ReadinessDatabase) or not await database.is_ready():
        raise PersistenceUnavailableError("postgresql readiness probe failed")
    return HealthResponse(status="ready", version=request.app.version)
