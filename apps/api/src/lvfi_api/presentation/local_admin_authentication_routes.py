"""HTTP boundary for the single local administrator identity."""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from lvfi_api.application.local_admin_authentication import (
    ADMIN_USERNAME,
    AuthenticationError,
    LocalAdminAuthenticationService,
)

COOKIE_NAME = "lvfi_admin_session"
router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=1, max_length=128)


class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor: str


def _service(request: Request) -> LocalAdminAuthenticationService:
    injected = getattr(request.app.state, "local_admin_authentication_service", None)
    if injected is not None:
        return cast(LocalAdminAuthenticationService, injected)
    return LocalAdminAuthenticationService(request.app.state.database)


def _cookie_secure(request: Request) -> bool:
    """Apply the configured public transport rather than an internal rewrite hop."""
    return request.app.state.settings.external_https or request.url.scheme == "https"


def _set_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=12 * 60 * 60,
        httponly=True,
        samesite="strict",
        secure=_cookie_secure(request),
        path="/",
    )


def _delete_cookie(response: Response, request: Request) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        samesite="strict",
        secure=_cookie_secure(request),
        path="/",
    )


async def require_authenticated_admin(
    request: Request,
    session_token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> str:
    """Protect every business router and derive actor only from its session."""
    try:
        return await _service(request).actor_for_token(session_token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail="authentication required") from exc


@router.post("/login", response_model=SessionResponse)
async def login(
    payload: LoginRequest, request: Request, response: Response
) -> SessionResponse:
    try:
        issued = await _service(request).login(
            payload.password, request.headers.get("X-Request-ID")
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail="invalid credentials") from exc
    _set_cookie(response, request, issued.token)
    return SessionResponse(actor=ADMIN_USERNAME)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    _: Annotated[str, Depends(require_authenticated_admin)],
    session_token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> Response:
    try:
        await _service(request).logout(
            session_token, request.headers.get("X-Request-ID")
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail="authentication required") from exc
    result = Response(status_code=204)
    _delete_cookie(result, request)
    return result


@router.get("/session", response_model=SessionResponse)
async def current_session(
    actor: Annotated[str, Depends(require_authenticated_admin)],
) -> SessionResponse:
    return SessionResponse(actor=actor)


@router.post("/password/change", status_code=204)
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    _: Annotated[str, Depends(require_authenticated_admin)],
    session_token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> Response:
    try:
        await _service(request).change_password(
            session_token,
            payload.current_password,
            payload.new_password,
            request.headers.get("X-Request-ID"),
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail="authentication failed") from exc
    return Response(status_code=204)
