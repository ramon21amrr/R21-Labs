"""Final branch coverage for non-string invalid dates."""

from __future__ import annotations

from lvfi_api.historical_import import normalize_row


def test_non_string_invalid_date_is_rejected() -> None:
    values: list[object] = [
        None,
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

    assert normalized is None
    assert issues[0].code == "invalid_date"
