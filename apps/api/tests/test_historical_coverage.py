"""Exercise remaining explicit branches in the controlled importer."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from openpyxl import Workbook  # type: ignore[import-untyped]

from lvfi_api import cli
from lvfi_api.historical_import import (
    HISTORICAL_HEADERS,
    HistoricalImporter,
    ImportSummary,
    normalize_row,
    source_sha256,
)
from lvfi_api.persistence.historical_models import teams


def _source(path: Path) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "JOGOS"
    sheet.append(HISTORICAL_HEADERS)
    sheet.append(
        [
            datetime(2026, 1, 2),
            "Competition",
            2026,
            "Home",
            "Away",
            1,
            0,
            2,
            1,
            3,
            1,
            6,
            4,
            1,
            1,
            3,
            2,
            2,
            1,
            5,
            3,
            7,
            8,
            1,
            2,
        ]
    )
    workbook.save(path)
    return path


class _Result:
    def __init__(self, identifier: int) -> None:
        self.identifier = identifier

    def scalar_one(self) -> int:
        return self.identifier


class _QueuedSession:
    def __init__(self, scalar_values: list[int | None]) -> None:
        self.scalar_values = scalar_values
        self.identifier = 0

    async def scalar(self, _: object) -> int | None:
        return self.scalar_values.pop(0)

    async def execute(self, _: object) -> _Result:
        self.identifier += 1
        return _Result(self.identifier)


def test_datetime_is_accepted_and_normalized_to_date() -> None:
    values = [
        datetime(2026, 1, 2),
        "Competition",
        2026,
        "Home",
        "Away",
        1,
        0,
        2,
        1,
        3,
        1,
        6,
        4,
        1,
        1,
        3,
        2,
        2,
        1,
        5,
        3,
        7,
        8,
        1,
        2,
    ]
    normalized, issues = normalize_row(values, 2)

    assert issues == ()
    assert normalized is not None
    assert normalized.played_on.isoformat() == "2026-01-02"


@pytest.mark.asyncio
async def test_existing_reference_and_canonical_conflict_are_explicit(
    tmp_path: Path,
) -> None:
    importer = HistoricalImporter(_QueuedSession([5]))  # type: ignore[arg-type]
    assert await importer._id_for(teams, teams.c.normalized_name, "home") == 5
    importer = HistoricalImporter(_QueuedSession([None]))  # type: ignore[arg-type]
    assert await importer._id_for(teams, teams.c.normalized_name, "home") == 1
    importer = HistoricalImporter(_QueuedSession([5]))  # type: ignore[arg-type]
    assert await importer._season_id(1, "2026") == 5
    source = _source(tmp_path / "conflict.xlsx")
    session = _QueuedSession([None, None, None, None, None, 99])
    summary = await HistoricalImporter(session).execute(  # type: ignore[arg-type]
        source, "JOGOS", source_sha256(source), False
    )

    assert summary.accepted_records == 0
    assert summary.rejected_records == 1


def test_cli_success_and_unknown_command_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    class Database:
        def __init__(self, _: object) -> None:
            pass

        async def start(self) -> None:
            pass

        async def stop(self) -> None:
            pass

        def session(self) -> object:
            class Session:
                async def __aenter__(self) -> object:
                    return object()

                async def __aexit__(self, *_: object) -> None:
                    pass

            return Session()

    class Importer:
        def __init__(self, _: object) -> None:
            pass

        async def execute(self, *_: object) -> ImportSummary:
            return ImportSummary("hash", "JOGOS", 1, 1, 0, 0, True)

    monkeypatch.setattr(cli, "Database", Database)
    monkeypatch.setattr(cli, "HistoricalImporter", Importer)
    monkeypatch.setattr(cli, "get_settings", lambda: object())
    assert cli.main(["historical-import", "--file", "source.xlsm", "--dry-run"]) == 0
    monkeypatch.setattr(
        cli,
        "_parser",
        lambda: SimpleNamespace(
            parse_args=lambda _: SimpleNamespace(command="unknown")
        ),
    )
    assert cli.main([]) == 4
