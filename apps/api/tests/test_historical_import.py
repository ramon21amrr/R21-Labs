"""Synthetic coverage for the controlled historical-import contract."""

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
    normalized_key,
    read_source,
    row_sha256,
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


def _workbook(path: Path, headers: tuple[str, ...] = HISTORICAL_HEADERS) -> Path:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "JOGOS"
    worksheet.append(headers)
    worksheet.append(_row())
    workbook.save(path)
    return path


def test_normalized_key_and_row_hash_are_deterministic() -> None:
    assert normalized_key("  São Paulo  ") == "são paulo"
    assert row_sha256({"a": 1, "b": "x"}) == row_sha256({"b": "x", "a": 1})


def test_normalize_row_accepts_the_exact_contract_with_zero() -> None:
    normalized, issues = normalize_row(_row(), 2)

    assert issues == ()
    assert normalized is not None
    assert normalized.played_on == date(2026, 1, 2)
    assert normalized.season == "2026"
    assert normalized.statistics["away_goals_first_half"] == 0


@pytest.mark.parametrize(
    ("position", "value", "code"),
    [
        (0, "invalid", "invalid_date"),
        (1, "", "required_text"),
        (3, "Mandante", "same_teams"),
        (5, "text", "invalid_integer"),
        (5, -1, "negative_statistic"),
        (5, 3, "first_half_exceeds_full"),
        (13, 7, "shots_on_target_exceed_shots"),
    ],
)
def test_normalize_row_rejects_invalid_values(
    position: int, value: object, code: str
) -> None:
    row = _row()
    row[position] = value
    if code == "same_teams":
        row[4] = value
    if code == "first_half_exceeds_full":
        row[7] = 2
    if code == "shots_on_target_exceed_shots":
        row[9] = 3

    normalized, issues = normalize_row(row, 2)

    assert normalized is None
    assert code in {issue.code for issue in issues}


def test_normalize_row_rejects_incomplete_source_row() -> None:
    normalized, issues = normalize_row(_row()[:-1], 2)

    assert normalized is None
    assert issues[0].code == "incomplete_row"


def test_read_source_validates_hash_headers_sheet_and_extension(tmp_path: Path) -> None:
    source = _workbook(tmp_path / "source.xlsx")
    digest = source_sha256(source)
    observed_hash, rows = read_source(source, "JOGOS", digest)

    assert observed_hash == digest
    assert list(rows)[0][0] == 2
    with pytest.raises(SourceValidationError, match="SHA-256"):
        read_source(source, "JOGOS", "0" * 64)
    with pytest.raises(SourceValidationError, match="sheet"):
        read_source(source, "missing", digest)
    with pytest.raises(SourceValidationError, match="xlsx"):
        read_source(tmp_path / "source.csv", "JOGOS")
    invalid_headers = _workbook(tmp_path / "headers.xlsx", ("invalid",))
    with pytest.raises(SourceValidationError, match="headers"):
        read_source(invalid_headers, "JOGOS")


@pytest.mark.asyncio
async def test_dry_run_does_not_use_the_database(tmp_path: Path) -> None:
    source = _workbook(tmp_path / "source.xlsx")
    summary = await HistoricalImporter(None).execute(  # type: ignore[arg-type]
        source, "JOGOS", source_sha256(source), True
    )

    assert summary.dry_run is True
    assert summary.accepted_records == 1
    assert summary.rejected_records == 0
