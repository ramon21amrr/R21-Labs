"""Validate the initial Alembic lineage without requiring a local PostgreSQL server."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from alembic import command


def _config(monkeypatch: pytest.MonkeyPatch) -> tuple[Config, StringIO]:
    monkeypatch.setenv("LVFI_ENVIRONMENT", "test")
    monkeypatch.setenv("LVFI_APP_NAME", "lvfi-api-test")
    monkeypatch.setenv("LVFI_DATABASE_URL", "postgresql://localhost/lvfi")
    output = StringIO()
    config = Config(
        str(Path(__file__).parents[1] / "alembic.ini"), output_buffer=output
    )
    return config, output


def test_initial_migration_is_the_only_current_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, _ = _config(monkeypatch)
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["20260724_01"]
    assert script.get_revision("20260724_01").down_revision is None


def test_migration_upgrade_and_downgrade_generate_postgresql_sql(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, output = _config(monkeypatch)

    command.upgrade(config, "head", sql=True)
    command.downgrade(config, "20260724_01:base", sql=True)

    rendered_sql = output.getvalue()
    assert "CREATE TABLE alembic_version" in rendered_sql
    assert "DROP TABLE alembic_version" in rendered_sql
