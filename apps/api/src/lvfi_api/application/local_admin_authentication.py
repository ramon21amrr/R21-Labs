"""Server-owned local administrator authentication and session lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import uuid4

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lvfi_api.persistence.historical_models import (
    local_admin_auth_events,
    local_admin_credentials,
    local_admin_sessions,
)

ADMIN_USERNAME = "admin"
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128
LOGIN_FAILURE_LIMIT = 5
LOCK_DURATION = timedelta(minutes=15)
IDLE_TIMEOUT = timedelta(minutes=30)
ABSOLUTE_TIMEOUT = timedelta(hours=12)

# PasswordHasher defaults are deliberately kept in the encoded Argon2id hash so
# later verification remains self-describing and can be rehashed safely.
_password_hasher = PasswordHasher(type=Type.ID)


class AuthenticationError(Exception):
    """A deliberately non-specific authentication failure."""


class BootstrapError(Exception):
    """The one local credential already exists or the secret is invalid."""


@dataclass(frozen=True)
class IssuedSession:
    token: str
    absolute_expires_at: datetime


def password_is_valid(password: str) -> bool:
    """Validate only the Product Owner-approved password bounds."""
    return MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH


def token_hash(token: str) -> str:
    """Return the fixed-size, non-reversible session-token representation."""
    return sha256(token.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


async def _audit(
    session: AsyncSession,
    event_type: str,
    actor: str | None,
    correlation_id: str | None,
) -> None:
    await session.execute(
        insert(local_admin_auth_events).values(
            event_type=event_type, actor=actor, correlation_id=correlation_id
        )
    )


class LocalAdminAuthenticationService:
    """Persist and validate exactly one local administrator identity."""

    def __init__(self, database: object) -> None:
        self._database = database

    async def bootstrap(self, password: str) -> None:
        if not password_is_valid(password):
            raise BootstrapError
        async with self._database.session() as session:
            exists = await session.scalar(
                select(local_admin_credentials.c.username).where(
                    local_admin_credentials.c.username == ADMIN_USERNAME
                )
            )
            if exists is not None:
                raise BootstrapError
            now = _now()
            await session.execute(
                insert(local_admin_credentials).values(
                    username=ADMIN_USERNAME,
                    password_hash=_password_hasher.hash(password),
                    failed_attempts=0,
                    locked_until=None,
                    password_changed_at=now,
                    created_at=now,
                )
            )
            await _audit(session, "bootstrap", None, None)

    async def login(
        self, password: str, correlation_id: str | None
    ) -> IssuedSession:
        issued: IssuedSession | None = None
        async with self._database.session() as session:
            row = (
                await session.execute(
                    select(local_admin_credentials)
                    .where(local_admin_credentials.c.username == ADMIN_USERNAME)
                    .with_for_update()
                )
            ).mappings().one_or_none()
            now = _now()
            valid = False
            if row is not None:
                locked_until = row["locked_until"]
                if locked_until is not None and locked_until > now:
                    valid = False
                else:
                    failed_attempts = (
                        0 if locked_until is not None else row["failed_attempts"]
                    )
                    try:
                        valid = password_is_valid(password) and _password_hasher.verify(
                            row["password_hash"], password
                        )
                    except (InvalidHashError, VerificationError, VerifyMismatchError):
                        valid = False
                    if valid:
                        await session.execute(
                            update(local_admin_credentials)
                            .where(local_admin_credentials.c.username == ADMIN_USERNAME)
                            .values(failed_attempts=0, locked_until=None)
                        )
                    else:
                        failures = failed_attempts + 1
                        await session.execute(
                            update(local_admin_credentials)
                            .where(local_admin_credentials.c.username == ADMIN_USERNAME)
                            .values(
                                failed_attempts=failures,
                                locked_until=(now + LOCK_DURATION)
                                if failures >= LOGIN_FAILURE_LIMIT
                                else None,
                            )
                        )
            if not valid:
                await _audit(session, "login_failed", None, correlation_id)
            else:
                token = token_urlsafe(32)
                absolute_expires_at = now + ABSOLUTE_TIMEOUT
                await session.execute(
                    insert(local_admin_sessions).values(
                        session_id=str(uuid4()),
                        username=ADMIN_USERNAME,
                        token_hash=token_hash(token),
                        issued_at=now,
                        last_activity_at=now,
                        idle_expires_at=now + IDLE_TIMEOUT,
                        absolute_expires_at=absolute_expires_at,
                        invalidated_at=None,
                    )
                )
                await _audit(session, "login_succeeded", None, correlation_id)
                issued = IssuedSession(token, absolute_expires_at)
        if issued is None:
            raise AuthenticationError
        return issued

    async def actor_for_token(self, token: str | None) -> str:
        if not token:
            raise AuthenticationError
        authenticated = False
        async with self._database.session() as session:
            row = (
                await session.execute(
                    select(local_admin_sessions)
                    .where(local_admin_sessions.c.token_hash == token_hash(token))
                    .with_for_update()
                )
            ).mappings().one_or_none()
            now = _now()
            if (
                row is None
                or row["invalidated_at"] is not None
                or row["idle_expires_at"] <= now
                or row["absolute_expires_at"] <= now
            ):
                if row is not None and row["invalidated_at"] is None:
                    await session.execute(
                        update(local_admin_sessions)
                        .where(local_admin_sessions.c.session_id == row["session_id"])
                        .values(invalidated_at=now)
                    )
            else:
                await session.execute(
                    update(local_admin_sessions)
                    .where(local_admin_sessions.c.session_id == row["session_id"])
                    .values(last_activity_at=now, idle_expires_at=now + IDLE_TIMEOUT)
                )
                authenticated = True
        if not authenticated:
            raise AuthenticationError
        return ADMIN_USERNAME

    async def logout(self, token: str | None, correlation_id: str | None) -> None:
        if not token:
            raise AuthenticationError
        logged_out = False
        async with self._database.session() as session:
            row = (
                await session.execute(
                    select(local_admin_sessions)
                    .where(local_admin_sessions.c.token_hash == token_hash(token))
                    .with_for_update()
                )
            ).mappings().one_or_none()
            now = _now()
            if (
                row is not None
                and row["invalidated_at"] is None
                and row["idle_expires_at"] > now
                and row["absolute_expires_at"] > now
            ):
                await session.execute(
                    update(local_admin_sessions)
                    .where(
                        local_admin_sessions.c.session_id == row["session_id"],
                    )
                    .values(invalidated_at=now)
                )
                await _audit(session, "logout", ADMIN_USERNAME, correlation_id)
                logged_out = True
            elif row is not None and row["invalidated_at"] is None:
                await session.execute(
                    update(local_admin_sessions)
                    .where(local_admin_sessions.c.session_id == row["session_id"])
                    .values(invalidated_at=now)
                )
        if not logged_out:
            raise AuthenticationError

    async def change_password(
        self,
        token: str | None,
        current_password: str,
        new_password: str,
        correlation_id: str | None,
    ) -> None:
        if not password_is_valid(new_password):
            raise AuthenticationError
        if not token:
            raise AuthenticationError
        async with self._database.session() as session:
            credential = (
                await session.execute(
                    select(local_admin_credentials)
                    .where(local_admin_credentials.c.username == ADMIN_USERNAME)
                    .with_for_update()
                )
            ).mappings().one_or_none()
            if credential is None:
                raise AuthenticationError
            try:
                valid = _password_hasher.verify(
                    credential["password_hash"], current_password
                )
            except (InvalidHashError, VerificationError, VerifyMismatchError):
                valid = False
            if not valid:
                raise AuthenticationError
            now = _now()
            current_hash = token_hash(token)
            current_session = (
                await session.execute(
                    select(local_admin_sessions)
                    .where(local_admin_sessions.c.token_hash == current_hash)
                    .with_for_update()
                )
            ).mappings().one_or_none()
            if (
                current_session is None
                or current_session["invalidated_at"] is not None
                or current_session["idle_expires_at"] <= now
                or current_session["absolute_expires_at"] <= now
            ):
                if (
                    current_session is not None
                    and current_session["invalidated_at"] is None
                ):
                    await session.execute(
                        update(local_admin_sessions)
                        .where(
                            local_admin_sessions.c.session_id
                            == current_session["session_id"]
                        )
                        .values(invalidated_at=now)
                    )
                raise AuthenticationError
            await session.execute(
                update(local_admin_credentials)
                .where(local_admin_credentials.c.username == ADMIN_USERNAME)
                .values(
                    password_hash=_password_hasher.hash(new_password),
                    password_changed_at=now,
                )
            )
            await session.execute(
                update(local_admin_sessions)
                .where(
                    local_admin_sessions.c.token_hash != current_hash,
                    local_admin_sessions.c.invalidated_at.is_(None),
                )
                .values(invalidated_at=now)
            )
            await _audit(session, "password_changed", ADMIN_USERNAME, correlation_id)

    async def reset_password(self, password: str) -> None:
        if not password_is_valid(password):
            raise BootstrapError
        async with self._database.session() as session:
            credential = await session.scalar(
                select(local_admin_credentials.c.username)
                .where(local_admin_credentials.c.username == ADMIN_USERNAME)
                .with_for_update()
            )
            if credential is None:
                raise BootstrapError
            now = _now()
            await session.execute(
                update(local_admin_credentials)
                .where(local_admin_credentials.c.username == ADMIN_USERNAME)
                .values(
                    password_hash=_password_hasher.hash(password),
                    failed_attempts=0,
                    locked_until=None,
                    password_changed_at=now,
                )
            )
            await session.execute(
                update(local_admin_sessions)
                .where(local_admin_sessions.c.invalidated_at.is_(None))
                .values(invalidated_at=now)
            )
            await _audit(session, "password_reset", None, None)
