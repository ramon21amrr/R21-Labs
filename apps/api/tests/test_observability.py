"""Tests for JSON logs and configuration."""

from __future__ import annotations

import json
import logging

from lvfi_api.config import Settings
from lvfi_api.infrastructure.observability import JsonFormatter, configure_logging


def test_json_formatter_includes_required_and_request_fields() -> None:
    record = logging.LogRecord(
        "lvfi.test", logging.INFO, __file__, 1, "hello", (), None
    )
    record.environment = "test"
    record.correlation_id = "correlated"
    record.method = "GET"
    record.path = "/health"
    record.duration_ms = 1.25
    record.status = 200
    record.error = "sanitized"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "hello"
    assert payload["correlation_id"] == "correlated"
    assert payload["status"] == 200


def test_json_formatter_uses_defaults_for_optional_fields() -> None:
    record = logging.LogRecord(
        "lvfi.test", logging.INFO, __file__, 1, "hello", (), None
    )

    payload = json.loads(JsonFormatter().format(record))

    assert payload["environment"] == "unknown"
    assert "status" not in payload


def test_configure_logging_installs_structured_handler() -> None:
    settings = Settings(
        environment="test",
        app_name="lvfi-api-test",
        database_url="postgresql://localhost/lvfi",
        log_level="ERROR",
    )

    configure_logging(settings)

    assert isinstance(logging.getLogger().handlers[0].formatter, JsonFormatter)
    assert logging.getLogger().level == logging.ERROR
