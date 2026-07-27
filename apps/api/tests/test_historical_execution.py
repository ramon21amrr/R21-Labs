"""Persistence-path tests using a deterministic synthetic async session."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from openpyxl import Workbook  # type: ignore[import-untyped]

from lvfi_api.historical_import import (
    HISTORICAL_HEADERS,
    HistoricalImporter,
    SourceValidationError,
    normalize_row,
    read_source,
    source_sha256,
)


def _row() -> list[object]:
    return [
        date(2026, 1, 2),
        "Campeonato",
        2026,
        "Mandante",
        "Visitante",
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


def _workbook(path: Path, row: list[object] | None = None) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "JOGOS"
    sheet.append(HISTORICAL_HEADERS)
    sheet.append(_row() if row is None else row)
    workbook.save(path)
    return path


def test_parser_accepts_explicit_date_and_integer_text() -> None:
    row = _row()
    row[0] = "02/01/2026"
    row[5] = "1"

    normalized, issues = normalize_row(row, 2)

    assert issues == ()
    assert normalized is not None
    assert normalized.played_on == date(2026, 1, 2)


def test_safe_reader_detects_source_change_after_iteration(tmp_path: Path) -> None:
    source = _workbook(tmp_path / "source.xlsx")
    digest = source_sha256(source)
    _, rows = read_source(source, "JOGOS", digest)
    changed = _row()
    changed[1] = "Changed"
    _workbook(source, changed)

    with pytest.raises(SourceValidationError, match="changed"):
        list(rows)


class _Result:
    def __init__(self, identifier: int) -> None:
        self._identifier = identifier

    def scalar_one(self) -> int:
        return self._identifier


class _Session:
    def __init__(self, existing_batch: int | None = None) -> None:
        self.existing_batch = existing_batch
        self.identifier = 0
        self.statements: list[object] = []

    async def scalar(self, _: object) -> int | None:
        result = self.existing_batch
        self.existing_batch = None
        return result

    async def execute(self, statement: object) -> _Result:
        self.identifier += 1
        self.statements.append(statement)
        return _Result(self.identifier)


@pytest.mark.asyncio
async def test_execute_persists_accepted_and_rejected_raw_records(
    tmp_path: Path,
) -> None:
    accepted_source = _workbook(tmp_path / "accepted.xlsx")
    accepted_session = _Session()
    accepted = await HistoricalImporter(accepted_session).execute(  # type: ignore[arg-type]
        accepted_source, "JOGOS", source_sha256(accepted_source), False
    )
    rejected = _row()
    rejected[5] = "bad"
    rejected_source = _workbook(tmp_path / "rejected.xlsx", rejected)
    rejected_session = _Session()
    rejected_summary = await HistoricalImporter(rejected_session).execute(  # type: ignore[arg-type]
        rejected_source, "JOGOS", source_sha256(rejected_source), False
    )

    assert accepted.accepted_records == 1
    assert accepted.rejected_records == 0
    assert rejected_summary.accepted_records == 0
    assert rejected_summary.rejected_records == 1
    assert accepted_session.statements
    assert rejected_session.statements


@pytest.mark.asyncio
async def test_execute_is_idempotent_when_the_batch_exists(tmp_path: Path) -> None:
    source = _workbook(tmp_path / "source.xlsx")
    summary = await HistoricalImporter(_Session(existing_batch=1)).execute(  # type: ignore[arg-type]
        source, "JOGOS", source_sha256(source), False
    )

    assert summary.already_imported is True
