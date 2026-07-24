"""Consistent, sanitized HTTP error responses."""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from lvfi_api.infrastructure.observability import correlation_id

logger = logging.getLogger(__name__)


class ErrorBody(BaseModel):
    """Stable error envelope safe for public clients."""

    code: str
    message: str
    correlation_id: str


def _body(code: str, message: str) -> dict[str, str]:
    return ErrorBody(
        code=code, message=message, correlation_id=correlation_id.get()
    ).model_dump()


async def persistence_unavailable_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Map expected infrastructure unavailability to a safe 503 response."""
    logger.warning(
        "persistence unavailable",
        extra={"method": request.method, "path": request.url.path, "error": str(exc)},
    )
    return JSONResponse(
        status_code=503, content=_body("dependency_unavailable", "service unavailable")
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Avoid returning exceptions or stack traces to HTTP clients."""
    logger.exception(
        "unexpected request error",
        extra={
            "method": request.method,
            "path": request.url.path,
            "error": type(exc).__name__,
        },
    )
    return JSONResponse(
        status_code=500, content=_body("internal_error", "internal server error")
    )
