"""FastAPI application factory for the LVFI modular monolith."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from fastapi import FastAPI

from lvfi_api import __version__
from lvfi_api.config import Settings, get_settings
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.infrastructure.database import Database
from lvfi_api.infrastructure.observability import configure_logging
from lvfi_api.presentation.errors import (
    persistence_unavailable_handler,
    unexpected_error_handler,
)
from lvfi_api.presentation.middleware import CorrelationMiddleware
from lvfi_api.presentation.routes import router


class ManagedDatabase(Protocol):
    """Lifecycle subset accepted by the application factory."""

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def is_ready(self) -> bool: ...


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    database: ManagedDatabase = app.state.database
    await database.start()
    try:
        yield
    finally:
        await database.stop()


def create_app(
    settings: Settings | None = None, database: ManagedDatabase | None = None
) -> FastAPI:
    """Build the configured API without starting external infrastructure eagerly."""
    from fastapi.exceptions import RequestValidationError

    from lvfi_api.domain.errors import (
        InvalidQueryError,
        MethodOneEngineError,
        MethodOneSampleIncompleteError,
        MethodOneSampleInvalidError,
        ResourceNotFoundError,
        StatisticsNotFoundError,
    )
    from lvfi_api.presentation.historical_errors import (
        invalid_query_handler,
        method_one_engine_error_handler,
        method_one_sample_blocked_handler,
        request_validation_handler,
        resource_not_found_handler,
    )
    from lvfi_api.presentation.historical_routes import router as historical_router
    from lvfi_api.presentation.pricing_execution_routes import (
        router as pricing_execution_router,
    )

    effective_settings = settings or get_settings()
    configure_logging(effective_settings)
    app = FastAPI(
        title=effective_settings.app_name,
        version=__version__,
        debug=effective_settings.debug,
        lifespan=_lifespan,
    )
    app.state.database = database or Database(effective_settings)
    app.add_middleware(
        CorrelationMiddleware,
        header_name=effective_settings.correlation_header,
        environment=effective_settings.environment,
    )
    app.add_exception_handler(
        PersistenceUnavailableError, persistence_unavailable_handler
    )
    app.add_exception_handler(InvalidQueryError, invalid_query_handler)
    app.add_exception_handler(
        MethodOneSampleIncompleteError, method_one_sample_blocked_handler
    )
    app.add_exception_handler(
        MethodOneSampleInvalidError, method_one_sample_blocked_handler
    )
    app.add_exception_handler(MethodOneEngineError, method_one_engine_error_handler)
    app.add_exception_handler(ResourceNotFoundError, resource_not_found_handler)
    app.add_exception_handler(StatisticsNotFoundError, resource_not_found_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
    app.include_router(router)
    app.include_router(historical_router)
    app.include_router(pricing_execution_router)
    return app
