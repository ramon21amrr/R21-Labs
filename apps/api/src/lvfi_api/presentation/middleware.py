"""Request correlation and structured request completion logging."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from lvfi_api.infrastructure.observability import correlation_id

logger = logging.getLogger(__name__)


def _safe_request_id(value: str | None) -> str:
    if (
        value is not None
        and 0 < len(value) <= 128
        and value.isascii()
        and value.isprintable()
    ):
        return value
    return str(uuid4())


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Propagate or create a request ID, then log one sanitized completion event."""

    def __init__(self, app: ASGIApp, header_name: str, environment: str) -> None:
        super().__init__(app)
        self._header_name = header_name
        self._environment = environment

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = _safe_request_id(request.headers.get(self._header_name))
        token = correlation_id.set(request_id)
        started = perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = round((perf_counter() - started) * 1000, 3)
            correlation_id.reset(token)
        response.headers[self._header_name] = request_id
        logger.info(
            "request completed",
            extra={
                "environment": self._environment,
                "correlation_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "status": response.status_code,
            },
        )
        return response
