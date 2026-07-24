"""Tests for explicit, fail-fast environment configuration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from lvfi_api.config import Settings, get_settings


def test_settings_accepts_valid_postgresql_configuration() -> None:
    settings = Settings(
        environment="local",
        app_name="lvfi-api",
        database_url="postgresql+asyncpg://lvfi:lvfi@localhost:5432/lvfi",
        correlation_header="X-Request-ID",
    )

    assert settings.port == 8000
    assert str(settings.database_url).startswith("postgresql+asyncpg://")


def test_settings_rejects_missing_required_configuration() -> None:
    with pytest.raises(ValidationError, match="environment"):
        Settings(  # type: ignore[call-arg]
            app_name="lvfi-api", database_url="postgresql://localhost/lvfi"
        )


def test_settings_rejects_unsafe_correlation_header() -> None:
    with pytest.raises(ValidationError, match="correlation header"):
        Settings(
            environment="local",
            app_name="lvfi-api",
            database_url="postgresql://localhost/lvfi",
            correlation_header="X Request ID",
        )


def test_get_settings_loads_prefixed_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("LVFI_ENVIRONMENT", "test")
    monkeypatch.setenv("LVFI_APP_NAME", "from-environment")
    monkeypatch.setenv("LVFI_DATABASE_URL", "postgresql://localhost/lvfi")

    assert get_settings().app_name == "from-environment"

    get_settings.cache_clear()
