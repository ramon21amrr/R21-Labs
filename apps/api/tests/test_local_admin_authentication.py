"""Focused APP-017 behavior and security-boundary tests."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from lvfi_api import cli
from lvfi_api.application import local_admin_authentication as auth
from lvfi_api.config import Settings
from lvfi_api.infrastructure.database import Database as RealDatabase
from lvfi_api.main import create_app
from lvfi_api.persistence.historical_models import (
    local_admin_auth_events,
    local_admin_credentials,
    local_admin_sessions,
)
from lvfi_api.presentation import local_admin_authentication_routes as auth_routes

from .conftest import FakeDatabase

TEST_PASSWORD = token_urlsafe(18)
OTHER_TEST_PASSWORD = token_urlsafe(18)
TEST_TOKEN = token_urlsafe(32)


class Result:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row

    def mappings(self) -> Result:
        return self

    def one_or_none(self) -> dict[str, Any] | None:
        return self.row


class Session:
    def __init__(
        self, rows: list[dict[str, Any] | None] = (), scalars: list[Any] = ()
    ) -> None:
        self.rows, self.scalars, self.calls = list(rows), list(scalars), []

    async def execute(self, statement: object) -> Result:
        self.calls.append(statement)
        return Result(self.rows.pop(0) if self.rows else None)

    async def scalar(self, statement: object) -> Any:
        self.calls.append(statement)
        return self.scalars.pop(0) if self.scalars else None


class Database:
    def __init__(self, session: Session) -> None:
        self.value = session

    def session(self) -> Any:
        session = self.value

        class Context:
            async def __aenter__(self) -> Session:
                return session

            async def __aexit__(self, *args: object) -> None:
                return None

        return Context()


class Hasher:
    def hash(self, password: str) -> str:
        return f"argon2id:{password}"

    def verify(self, stored: str, password: str) -> bool:
        if stored == "broken":
            raise auth.VerifyMismatchError
        return stored == f"argon2id:{password}"


def credential(**changes: Any) -> dict[str, Any]:
    now = datetime.now(UTC)
    return {
        "username": "admin",
        "password_hash": f"argon2id:{TEST_PASSWORD}",
        "failed_attempts": 0,
        "locked_until": None,
        "password_changed_at": now,
        "created_at": now,
        **changes,
    }


@pytest.fixture
def hasher(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "_password_hasher", Hasher())


@pytest.mark.asyncio
async def test_credentials_login_sessions_and_password_lifecycle(hasher: None) -> None:
    assert not auth.password_is_valid("x" * 11)
    assert auth.password_is_valid("x" * 12) and auth.password_is_valid("x" * 128)
    assert (
        not auth.password_is_valid("x" * 129) and len(auth.token_hash(TEST_TOKEN)) == 64
    )
    with pytest.raises(auth.BootstrapError):
        await auth.LocalAdminAuthenticationService(Database(Session())).bootstrap(
            "short"
        )
    with pytest.raises(auth.BootstrapError):
        await auth.LocalAdminAuthenticationService(
            Database(Session(scalars=["admin"]))
        ).bootstrap("x" * 12)
    await auth.LocalAdminAuthenticationService(
        Database(Session(scalars=[None]))
    ).bootstrap("x" * 12)
    with pytest.raises(auth.AuthenticationError):
        await auth.LocalAdminAuthenticationService(
            Database(Session(rows=[None]))
        ).login("x" * 12, "r")
    locked = credential(locked_until=datetime.now(UTC) + timedelta(minutes=1))
    with pytest.raises(auth.AuthenticationError):
        await auth.LocalAdminAuthenticationService(
            Database(Session(rows=[locked]))
        ).login("x" * 12, None)
    expired = credential(
        locked_until=datetime.now(UTC) - timedelta(minutes=1), failed_attempts=5
    )
    with pytest.raises(auth.AuthenticationError):
        await auth.LocalAdminAuthenticationService(
            Database(Session(rows=[expired]))
        ).login(OTHER_TEST_PASSWORD, None)
    with pytest.raises(auth.AuthenticationError):
        await auth.LocalAdminAuthenticationService(
            Database(Session(rows=[credential(password_hash="broken")]))
        ).login("x" * 12, None)
    issued = await auth.LocalAdminAuthenticationService(
        Database(Session(rows=[credential(password_hash=f"argon2id:{TEST_PASSWORD}")]))
    ).login(TEST_PASSWORD, "r")
    assert issued.token and issued.absolute_expires_at > datetime.now(UTC)
    service = auth.LocalAdminAuthenticationService(Database(Session()))
    with pytest.raises(auth.AuthenticationError):
        await service.actor_for_token(None)
    valid = {
        "session_id": "id",
        "invalidated_at": None,
        "idle_expires_at": datetime.now(UTC) + timedelta(minutes=1),
        "absolute_expires_at": datetime.now(UTC) + timedelta(hours=1),
    }
    assert (
        await auth.LocalAdminAuthenticationService(
            Database(Session(rows=[valid]))
        ).actor_for_token("token")
        == "admin"
    )
    with pytest.raises(auth.AuthenticationError):
        await auth.LocalAdminAuthenticationService(
            Database(
                Session(
                    rows=[
                        {
                            **valid,
                            "idle_expires_at": datetime.now(UTC) - timedelta(seconds=1),
                        }
                    ]
                )
            )
        ).actor_for_token("token")
    with pytest.raises(auth.AuthenticationError):
        await auth.LocalAdminAuthenticationService(
            Database(Session(rows=[{**valid, "invalidated_at": datetime.now(UTC)}]))
        ).actor_for_token("token")
    with pytest.raises(auth.AuthenticationError):
        await service.logout(None, None)
    with pytest.raises(auth.AuthenticationError):
        await auth.LocalAdminAuthenticationService(
            Database(Session(rows=[None]))
        ).logout(TEST_TOKEN, "r")
    await auth.LocalAdminAuthenticationService(Database(Session(rows=[valid]))).logout(
        TEST_TOKEN, "r"
    )
    with pytest.raises(auth.AuthenticationError):
        await auth.LocalAdminAuthenticationService(
            Database(
                Session(
                    rows=[
                        {
                            **valid,
                            "idle_expires_at": datetime.now(UTC) - timedelta(seconds=1),
                        }
                    ]
                )
            )
        ).logout(TEST_TOKEN, "r")
    for token, current, new, rows in [
        (None, "x" * 12, "y" * 12, []),
        ("t", "x" * 12, "short", []),
        ("t", "x" * 12, "y" * 12, [None]),
        ("t", "x" * 12, "y" * 12, [credential(password_hash="broken")]),
    ]:
        with pytest.raises(auth.AuthenticationError):
            await auth.LocalAdminAuthenticationService(
                Database(Session(rows=rows))
            ).change_password(token, current, new, None)
    with pytest.raises(auth.AuthenticationError):
        await auth.LocalAdminAuthenticationService(
            Database(
                Session(
                    rows=[
                        credential(),
                        {
                            **valid,
                            "idle_expires_at": datetime.now(UTC) - timedelta(seconds=1),
                        },
                    ]
                )
            )
        ).change_password(TEST_TOKEN, TEST_PASSWORD, "y" * 12, None)
    with pytest.raises(auth.AuthenticationError):
        await auth.LocalAdminAuthenticationService(
            Database(
                Session(
                    rows=[
                        credential(),
                        {**valid, "invalidated_at": datetime.now(UTC)},
                    ]
                )
            )
        ).change_password(TEST_TOKEN, TEST_PASSWORD, "y" * 12, None)
    await auth.LocalAdminAuthenticationService(
        Database(
            Session(rows=[credential(password_hash=f"argon2id:{TEST_PASSWORD}"), valid])
        )
    ).change_password(TEST_TOKEN, TEST_PASSWORD, "y" * 12, "r")
    with pytest.raises(auth.BootstrapError):
        await service.reset_password("short")
    with pytest.raises(auth.BootstrapError):
        await auth.LocalAdminAuthenticationService(
            Database(Session(scalars=[None]))
        ).reset_password("y" * 12)
    await auth.LocalAdminAuthenticationService(
        Database(Session(scalars=["admin"]))
    ).reset_password("y" * 12)


class HttpAuth:
    fail_logout = False

    async def login(self, password: str, _: str | None) -> auth.IssuedSession:
        if password != TEST_PASSWORD:
            raise auth.AuthenticationError
        return auth.IssuedSession(TEST_TOKEN, datetime.now(UTC) + timedelta(hours=12))

    async def actor_for_token(self, token: str | None) -> str:
        if token != TEST_TOKEN:
            raise auth.AuthenticationError
        return "admin"

    async def logout(self, *_: object) -> None:
        if self.fail_logout:
            raise auth.AuthenticationError
        return None

    async def change_password(self, *args: object) -> None:
        if args[1] != TEST_PASSWORD:
            raise auth.AuthenticationError


@pytest.mark.real_auth
def test_http_cookie_generic_failure_and_server_guard() -> None:
    settings = Settings(
        environment="local",
        app_name="test",
        database_url="postgresql://localhost/test",
        external_https=True,
    )
    app = create_app(settings, FakeDatabase())
    app.state.local_admin_authentication_service = HttpAuth()
    with TestClient(app, base_url="https://testserver") as client:
        assert client.get("/auth/session").status_code == 401
        failed = client.post("/auth/login", json={"password": OTHER_TEST_PASSWORD})
        logged = client.post("/auth/login", json={"password": TEST_PASSWORD})
        assert client.get("/auth/session").status_code == 200
        changed = client.post(
            "/auth/password/change",
            json={
                "current_password": TEST_PASSWORD,
                "new_password": OTHER_TEST_PASSWORD,
            },
        )
        rejected_change = client.post(
            "/auth/password/change",
            json={
                "current_password": OTHER_TEST_PASSWORD,
                "new_password": TEST_PASSWORD,
            },
        )
        logout = client.post("/auth/logout")
        client.post("/auth/login", json={"password": TEST_PASSWORD})
        app.state.local_admin_authentication_service.fail_logout = True
        rejected_logout = client.post("/auth/logout")
    assert (
        failed.status_code == 401 and failed.json()["detail"] == "invalid credentials"
    )
    cookie = logged.headers["set-cookie"].lower()
    assert (
        "httponly" in cookie
        and "samesite=strict" in cookie
        and "secure" in cookie
        and TEST_TOKEN not in logged.text
    )
    assert (
        changed.status_code == 204
        and rejected_change.status_code == 401
        and logout.status_code == 204
    )
    assert rejected_logout.status_code == 401


def test_auth_service_factory_uses_database_when_not_injected() -> None:
    request = type(
        "Request",
        (),
        {
            "app": type(
                "App",
                (),
                {"state": type("State", (), {"database": Database(Session())})()},
            )()
        },
    )()
    assert isinstance(
        auth_routes._service(request), auth.LocalAdminAuthenticationService
    )


def test_hidden_cli_bootstrap_reset_and_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = iter(["x" * 12, "x" * 12, "x" * 12, "different"])
    monkeypatch.setattr(cli, "getpass", lambda _: next(values))

    async def completed(*_: object) -> int:
        return 0

    monkeypatch.setattr(cli, "_admin_credential", completed)
    assert cli.main(["admin-bootstrap"]) == 0
    assert cli.main(["admin-reset-password"]) == 2

    async def failed(*_: object) -> int:
        raise auth.BootstrapError

    monkeypatch.setattr(cli, "getpass", lambda _: "x" * 12)
    monkeypatch.setattr(cli, "_admin_credential", failed)
    assert cli.main(["admin-reset-password"]) == 3


@pytest.mark.asyncio
async def test_cli_admin_operation_owns_database_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class CliDatabase:
        async def start(self) -> None:
            calls.append("start")

        async def stop(self) -> None:
            calls.append("stop")

    class CliService:
        def __init__(self, _: object) -> None:
            pass

        async def bootstrap(self, _: str) -> None:
            calls.append("bootstrap")

        async def reset_password(self, _: str) -> None:
            calls.append("reset")

    monkeypatch.setattr(cli, "Database", lambda _: CliDatabase())
    monkeypatch.setattr(cli, "LocalAdminAuthenticationService", CliService)
    monkeypatch.setattr(cli, "get_settings", lambda: object())
    assert await cli._admin_credential("admin-bootstrap", "x" * 12) == 0
    assert await cli._admin_credential("admin-reset-password", "x" * 12) == 0
    assert calls == ["start", "bootstrap", "stop", "start", "reset", "stop"]


@pytest.mark.asyncio
async def test_postgresql_local_admin_persists_lock_and_session_lifecycle() -> None:
    database_url = os.environ.get("LVFI_DATABASE_URL")
    if database_url is None or "127.0.0.1:55432" not in database_url:
        pytest.skip("requires the isolated Codex PostgreSQL task database")

    database = RealDatabase(
        Settings(
            environment="test",
            app_name="lvfi-postgresql-authentication-test",
            database_url=database_url,
        )
    )
    await database.start()
    try:
        service = auth.LocalAdminAuthenticationService(database)
        await service.bootstrap(TEST_PASSWORD)
        for _ in range(auth.LOGIN_FAILURE_LIMIT):
            with pytest.raises(auth.AuthenticationError):
                await service.login(OTHER_TEST_PASSWORD, "test-correlation")
        async with database.session() as session:
            credential_row = (
                (await session.execute(select(local_admin_credentials)))
                .mappings()
                .one()
            )
            events = (
                (await session.execute(select(local_admin_auth_events)))
                .mappings()
                .all()
            )
        assert credential_row["failed_attempts"] == auth.LOGIN_FAILURE_LIMIT
        assert credential_row["locked_until"] > datetime.now(UTC)
        assert [event["event_type"] for event in events].count("login_failed") == 5
        assert all(event["actor"] is None for event in events)

        async with database.session() as session:
            await session.execute(
                update(local_admin_credentials)
                .where(local_admin_credentials.c.username == auth.ADMIN_USERNAME)
                .values(locked_until=datetime.now(UTC) - timedelta(seconds=1))
            )
        first = await service.login(TEST_PASSWORD, "test-correlation")
        second = await service.login(TEST_PASSWORD, "test-correlation")
        await service.change_password(
            first.token, TEST_PASSWORD, OTHER_TEST_PASSWORD, "test-correlation"
        )
        async with database.session() as session:
            sessions = (
                (await session.execute(select(local_admin_sessions))).mappings().all()
            )
        assert sum(row["invalidated_at"] is not None for row in sessions) == 1
        await service.reset_password(TEST_PASSWORD)
        async with database.session() as session:
            sessions = (
                (await session.execute(select(local_admin_sessions))).mappings().all()
            )
            events = (
                (await session.execute(select(local_admin_auth_events)))
                .mappings()
                .all()
            )
        assert all(row["invalidated_at"] is not None for row in sessions)
        assert events[-1]["event_type"] == "password_reset"
        assert events[-1]["actor"] is None
        assert second.token != first.token
    finally:
        await database.stop()
