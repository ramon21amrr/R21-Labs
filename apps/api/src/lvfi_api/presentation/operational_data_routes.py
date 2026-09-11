# ruff: noqa: B008
"""Administrative binary-source preview and confirmation endpoints."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal, cast

from fastapi import APIRouter, Depends, Query, Request
from fastapi import Path as FastApiPath
from pydantic import BaseModel, ConfigDict, Field

from lvfi_api.application.operational_data import OperationalDataService
from lvfi_api.domain.errors import InvalidQueryError, PersistenceUnavailableError
from lvfi_api.domain.operational_data import (
    FutureMatch,
    FutureMatchDraft,
    StatisticRevision,
    StatisticRevisionDraft,
)
from lvfi_api.historical_import import (
    HistoricalImporter,
    ImportSummary,
    SourceValidationError,
)
from lvfi_api.persistence.operational_data import SqlAlchemyOperationalDataRepository
from lvfi_api.presentation.local_admin_authentication_routes import (
    require_authenticated_admin,
)

router = APIRouter(prefix="/administration", tags=["operational data"])
MAX_SOURCE_BYTES = 25 * 1024 * 1024


class ImportSummaryResponse(BaseModel):
    """Safe aggregate preview: rows are never returned as a public payload."""

    model_config = ConfigDict(extra="forbid")
    source_sha256: str
    sheet_name: str
    total_records: int
    accepted_records: int
    rejected_records: int
    warning_records: int
    dry_run: bool
    already_imported: bool

    @classmethod
    def from_summary(cls, value: ImportSummary) -> ImportSummaryResponse:
        return cls(**{field: getattr(value, field) for field in cls.model_fields})


class FutureMatchCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    played_on: str
    competition: str = Field(min_length=1, max_length=255)
    season: str = Field(min_length=1, max_length=32)
    home_team: str = Field(min_length=1, max_length=255)
    away_team: str = Field(min_length=1, max_length=255)


class FutureMatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    match_id: int
    played_on: str
    competition: str
    season: str
    home_team: str
    away_team: str
    actor: str
    created_at: str

    @classmethod
    def from_contract(cls, value: FutureMatch) -> FutureMatchResponse:
        return cls(
            **{
                field: str(getattr(value, field))
                if field in {"played_on", "created_at"}
                else getattr(value, field)
                for field in cls.model_fields
            }
        )


class StatisticRevisionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statistic_field: str = Field(min_length=1, max_length=80)
    availability: Literal["available", "missing"]
    new_value: int | None = Field(default=None, ge=0)
    reason: str = Field(min_length=1, max_length=2000)


class StatisticRevisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision_id: int
    match_id: int
    statistic_field: str
    previous_value: int | None
    availability: Literal["available", "missing"]
    new_value: int | None
    actor: str
    reason: str
    created_at: str

    @classmethod
    def from_contract(cls, value: StatisticRevision) -> StatisticRevisionResponse:
        return cls(
            **{
                field: str(getattr(value, field))
                if field == "created_at"
                else getattr(value, field)
                for field in cls.model_fields
            }
        )


async def get_operational_data_service(request: Request) -> OperationalDataService:
    injected = getattr(request.app.state, "operational_data_service", None)
    if injected is not None:
        return cast(OperationalDataService, injected)
    database = request.app.state.database
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("database write session unavailable")
    return OperationalDataService(SqlAlchemyOperationalDataRepository(database))


async def _source_path(
    request: Request, filename: str
) -> tuple[TemporaryDirectory[str], Path]:
    if Path(filename).name != filename or Path(filename).suffix.lower() not in {
        ".csv",
        ".xlsx",
        ".xlsm",
    }:
        raise InvalidQueryError("invalid source filename")
    body = await request.body()
    if not body or len(body) > MAX_SOURCE_BYTES:
        raise InvalidQueryError("invalid source body")
    directory = TemporaryDirectory(prefix="lvfi-import-")
    source = Path(directory.name) / filename
    source.write_bytes(body)
    return directory, source


@router.post(
    "/imports/preview",
    response_model=ImportSummaryResponse,
    summary="Preview a controlled CSV, XLSX or XLSM import",
)
async def preview_import(
    request: Request,
    filename: str = Query(min_length=5, max_length=255),
    sheet_name: str = Query(default="JOGOS", min_length=1, max_length=128),
) -> ImportSummaryResponse:
    directory, source = await _source_path(request, filename)
    try:
        summary = await HistoricalImporter(None).execute(  # type: ignore[arg-type]
            source, sheet_name, None, True
        )
    except SourceValidationError as exc:
        raise InvalidQueryError("invalid source") from exc
    finally:
        directory.cleanup()
    return ImportSummaryResponse.from_summary(summary)


@router.post(
    "/imports/confirm",
    response_model=ImportSummaryResponse,
    summary="Confirm a previously previewed controlled import",
)
async def confirm_import(
    request: Request,
    filename: str = Query(min_length=5, max_length=255),
    sheet_name: str = Query(default="JOGOS", min_length=1, max_length=128),
) -> ImportSummaryResponse:
    database = request.app.state.database
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("database write session unavailable")
    directory, source = await _source_path(request, filename)
    try:
        async with database.session() as session:
            summary = await HistoricalImporter(session).execute(
                source, sheet_name, None, False
            )
    except SourceValidationError as exc:
        raise InvalidQueryError("invalid source") from exc
    finally:
        directory.cleanup()
    return ImportSummaryResponse.from_summary(summary)


@router.post("/matches", response_model=FutureMatchResponse, status_code=201)
async def create_future_match(
    payload: FutureMatchCreateRequest,
    actor: str = Depends(require_authenticated_admin),
    service: OperationalDataService = Depends(get_operational_data_service),
) -> FutureMatchResponse:
    from datetime import date

    try:
        played_on = date.fromisoformat(payload.played_on)
    except ValueError as exc:
        raise InvalidQueryError("invalid match date") from exc
    return FutureMatchResponse.from_contract(
        await service.create_future_match(
            FutureMatchDraft(
                played_on=played_on,
                actor=actor,
                **payload.model_dump(exclude={"played_on"}),
            )
        )
    )


@router.post(
    "/matches/{match_id}/statistic-revisions",
    response_model=StatisticRevisionResponse,
    status_code=201,
)
async def create_statistic_revision(
    payload: StatisticRevisionCreateRequest,
    match_id: int = FastApiPath(ge=1),
    actor: str = Depends(require_authenticated_admin),
    service: OperationalDataService = Depends(get_operational_data_service),
) -> StatisticRevisionResponse:
    return StatisticRevisionResponse.from_contract(
        await service.revise_statistic(
            StatisticRevisionDraft(
                match_id=match_id, actor=actor, **payload.model_dump()
            )
        )
    )
