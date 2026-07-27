"""Tests for safe historical-import CLI process outcomes."""

from __future__ import annotations

import asyncio

import pytest

from lvfi_api import cli
from lvfi_api.historical_import import SourceValidationError


def test_main_returns_import_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    async def successful(_: object) -> int:
        return 2

    monkeypatch.setattr(cli, "_historical_import", successful)

    assert cli.main(["historical-import", "--file", "source.xlsm", "--dry-run"]) == 2


def test_main_returns_structural_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def invalid(_: object) -> int:
        raise SourceValidationError("bad source")

    monkeypatch.setattr(cli, "_historical_import", invalid)

    assert cli.main(["historical-import", "--file", "source.xlsm", "--dry-run"]) == 3


def test_main_returns_configuration_or_database_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing(_: object) -> int:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(cli, "_historical_import", failing)

    assert cli.main(["historical-import", "--file", "source.xlsm", "--execute"]) == 4


def test_historical_import_stops_database_after_session_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    class Session:
        async def __aenter__(self) -> object:
            events.append("enter")
            return object()

        async def __aexit__(self, *_: object) -> None:
            events.append("exit")

    class Database:
        def __init__(self, _: object) -> None:
            pass

        async def start(self) -> None:
            events.append("start")

        async def stop(self) -> None:
            events.append("stop")

        def session(self) -> Session:
            return Session()

    class Importer:
        def __init__(self, _: object) -> None:
            pass

        async def execute(self, *_: object) -> object:
            raise RuntimeError("failure")

    monkeypatch.setattr(cli, "Database", Database)
    monkeypatch.setattr(cli, "HistoricalImporter", Importer)
    monkeypatch.setattr(cli, "get_settings", lambda: object())

    with pytest.raises(RuntimeError, match="failure"):
        asyncio.run(
            cli._historical_import(
                type(
                    "Args",
                    (),
                    {
                        "file": None,
                        "sheet": "JOGOS",
                        "expected_sha256": "x",
                        "dry_run": True,
                    },
                )()
            )
        )

    assert events == ["start", "enter", "exit", "stop"]
