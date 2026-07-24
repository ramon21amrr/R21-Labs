"""Typed environment configuration for the LVFI API."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded exclusively from the environment or a local file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="LVFI_", extra="ignore", case_sensitive=False
    )

    environment: Literal["local", "test", "pilot", "production"]
    app_name: str = Field(min_length=1, max_length=80)
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: str = Field(min_length=1)
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=5, ge=0, le=50)
    database_timeout_seconds: int = Field(default=5, ge=1, le=60)
    correlation_header: str = "X-Request-ID"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        return str(PostgresDsn(value))

    @field_validator("correlation_header")
    @classmethod
    def validate_correlation_header(cls, value: str) -> str:
        if not value or any(
            not (character.isalnum() or character == "-") for character in value
        ):
            raise ValueError(
                "correlation header must contain only letters, numbers, or hyphens"
            )
        return value


@lru_cache
def get_settings() -> Settings:
    """Return the validated process configuration exactly once."""
    return Settings()  # type: ignore[call-arg]
