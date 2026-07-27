"""Sanitized error handlers for public historical query endpoints."""

from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from lvfi_api.domain.errors import (
    InvalidQueryError,
    ResourceNotFoundError,
    StatisticsNotFoundError,
)
from lvfi_api.presentation.errors import _body


async def invalid_query_handler(
    request: Request, exc: InvalidQueryError
) -> JSONResponse:
    """Hide filter details while returning a stable client error."""
    return JSONResponse(
        status_code=422,
        content=_body("invalid_request", "invalid request parameter"),
    )


async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Prevent framework validation details from becoming the public contract."""
    return JSONResponse(
        status_code=422,
        content=_body("invalid_request", "invalid request parameter"),
    )


async def resource_not_found_handler(
    request: Request, exc: ResourceNotFoundError | StatisticsNotFoundError
) -> JSONResponse:
    """Return one stable absence response without persistence information."""
    code = (
        "statistics_not_found"
        if isinstance(exc, StatisticsNotFoundError)
        else "not_found"
    )
    return JSONResponse(status_code=404, content=_body(code, "resource not found"))
