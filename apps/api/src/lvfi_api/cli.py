# ruff: noqa: E501
"""Operational command-line entrypoints for the LVFI API."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from lvfi_api.config import get_settings
from lvfi_api.historical_import import (
    APPROVED_SOURCE_SHA256,
    HistoricalImporter,
    SourceValidationError,
)
from lvfi_api.infrastructure.database import Database


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m lvfi_api.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    historical = commands.add_parser(
        "historical-import", help="import an approved historical workbook"
    )
    historical.add_argument("--file", type=Path, required=True)
    historical.add_argument("--sheet", default="JOGOS")
    historical.add_argument("--expected-sha256", default=APPROVED_SOURCE_SHA256)
    mode = historical.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    return parser


async def _historical_import(arguments: argparse.Namespace) -> int:
    database = Database(get_settings())
    await database.start()
    try:
        async with database.session() as session:
            summary = await HistoricalImporter(session).execute(
                arguments.file,
                arguments.sheet,
                arguments.expected_sha256,
                arguments.dry_run,
            )
    finally:
        await database.stop()
    print(
        "historical-import "
        f"total={summary.total_records} accepted={summary.accepted_records} "
        f"rejected={summary.rejected_records} warnings={summary.warning_records} "
        f"dry_run={summary.dry_run} already_imported={summary.already_imported}"
    )
    return 2 if summary.rejected_records else 0


def main(arguments: list[str] | None = None) -> int:
    """Run the CLI and return documented process codes without leaking source data."""

    parsed = _parser().parse_args(arguments)
    try:
        if parsed.command == "historical-import":
            return asyncio.run(_historical_import(parsed))
    except SourceValidationError as error:
        print(f"historical-import structural-error: {error}", file=sys.stderr)
        return 3
    except Exception:
        print("historical-import configuration-or-database-error", file=sys.stderr)
        return 4
    return 4


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
