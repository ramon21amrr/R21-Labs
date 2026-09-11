"""PostgreSQL implementation of the immutable APP-015 analysis workflow."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import and_, func, insert, or_, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.domain.analysis_workflow import (
    Analysis,
    AnalysisEvent,
    AnalysisEventType,
    AnalysisSnapshot,
    AnalysisStatus,
    snapshot_hash,
)
from lvfi_api.domain.configuration import CATALOG_ID
from lvfi_api.domain.errors import InvalidQueryError, PersistenceUnavailableError
from lvfi_api.persistence.historical_models import (
    analysis_workflow_analyses,
    analysis_workflow_events,
    analysis_workflow_snapshots,
    competitions,
    configuration_catalogs,
    configuration_revisions,
    matches,
    pricing_executions,
    seasons,
    teams,
)
from lvfi_api.persistence.historical_queries import SessionProvider


def _event(row: RowMapping) -> AnalysisEvent:
    return AnalysisEvent(
        event_id=cast(int, row["id"]),
        event_type=AnalysisEventType(cast(str, row["event_type"])),
        execution_id=cast(str | None, row["execution_id"]),
        actor=cast(str | None, row["actor"]),
        reason=cast(str | None, row["reason"]),
        created_at=cast(datetime, row["created_at"]),
    )


def _status(events: tuple[AnalysisEvent, ...]) -> AnalysisStatus:
    kinds = {event.event_type for event in events}
    if AnalysisEventType.APPROVED in kinds:
        return AnalysisStatus.APPROVED
    if AnalysisEventType.CALCULATED in kinds:
        return AnalysisStatus.CALCULATED
    return AnalysisStatus.DRAFT


def _analysis(row: RowMapping, events: tuple[AnalysisEvent, ...]) -> Analysis:
    return Analysis(
        analysis_id=cast(str, row["analysis_id"]),
        match_id=cast(int, row["match_id"]),
        status=_status(events),
        created_at=cast(datetime, row["created_at"]),
        events=events,
    )


def _snapshot(row: RowMapping) -> AnalysisSnapshot:
    return AnalysisSnapshot(
        snapshot_id=cast(str, row["snapshot_id"]),
        analysis_id=cast(str, row["analysis_id"]),
        payload=cast(dict[str, Any], row["payload"]),
        snapshot_hash=cast(str, row["snapshot_hash"]),
        created_at=cast(datetime, row["created_at"]),
    )


async def _events(session: Any, analysis_id: str) -> tuple[AnalysisEvent, ...]:
    rows = (
        (
            await session.execute(
                select(analysis_workflow_events)
                .where(analysis_workflow_events.c.analysis_id == analysis_id)
                .order_by(
                    analysis_workflow_events.c.created_at.asc(),
                    analysis_workflow_events.c.id.asc(),
                )
            )
        )
        .mappings()
        .all()
    )
    return tuple(_event(row) for row in rows)


async def _locked_analysis(
    session: Any, analysis_id: str
) -> tuple[RowMapping, tuple[AnalysisEvent, ...]] | None:
    await session.execute(
        select(func.pg_advisory_xact_lock(func.hashtextextended(analysis_id, 0)))
    )
    row = (
        (
            await session.execute(
                select(analysis_workflow_analyses)
                .where(analysis_workflow_analyses.c.analysis_id == analysis_id)
                .with_for_update()
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        return None
    return row, await _events(session, analysis_id)


def _event_payload(event: AnalysisEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type.value,
        "execution_id": event.execution_id,
        "actor": event.actor,
        "reason": event.reason,
        "created_at": event.created_at.isoformat(),
    }


def _revision_payload(row: RowMapping) -> dict[str, Any]:
    return {
        "revision_id": row["id"],
        "catalog_id": row["catalog_id"],
        "catalog_hash": row["catalog_hash"],
        "scope": row["scope"],
        "parameter_code": row["parameter_code"],
        "value": deepcopy(row["value"]),
        "competition_id": row["competition_id"],
        "match_id": row["match_id"],
        "actor": row["actor"],
        "reason": row["reason"],
        "replaces_revision_id": row["replaces_revision_id"],
        "revision_hash": row["revision_hash"],
        "created_at": cast(datetime, row["created_at"]).isoformat(),
    }


def _sample_match_ids(value: object) -> list[int]:
    """Extract a sorted ID projection without reinterpreting the canonical input."""
    found: set[int] = set()

    def walk(item: object, key: str | None = None) -> None:
        if isinstance(item, dict):
            for name, nested in item.items():
                walk(nested, name)
        elif isinstance(item, list):
            for nested in item:
                walk(nested, key)
        elif key == "match_id":
            if isinstance(item, int) and not isinstance(item, bool) and item > 0:
                found.add(item)
            elif isinstance(item, str) and item.isdecimal() and int(item) > 0:
                found.add(int(item))

    walk(value)
    return sorted(found)


class SqlAlchemyAnalysisWorkflowRepository:
    """Serializes valid state transitions and captures one self-contained snapshot."""

    def __init__(self, database: SessionProvider) -> None:
        self._database = database

    async def create_draft(self, analysis_id: str, match_id: int) -> Analysis | None:
        try:
            async with self._database.session() as session:
                exists = await session.scalar(
                    select(matches.c.id).where(matches.c.id == match_id)
                )
                if exists is None:
                    return None
                row = (
                    (
                        await session.execute(
                            insert(analysis_workflow_analyses)
                            .values(analysis_id=analysis_id, match_id=match_id)
                            .returning(analysis_workflow_analyses)
                        )
                    )
                    .mappings()
                    .one()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("analysis draft write failed") from exc
        return _analysis(row, ())

    async def calculate(self, analysis_id: str, execution_id: str) -> Analysis | None:
        try:
            async with self._database.session() as session:
                locked = await _locked_analysis(session, analysis_id)
                if locked is None:
                    return None
                analysis_row, events = locked
                if _status(events) is not AnalysisStatus.DRAFT:
                    raise InvalidQueryError("analysis is not a draft")
                execution = (
                    (
                        await session.execute(
                            select(
                                pricing_executions.c.match_id,
                                pricing_executions.c.status,
                            ).where(pricing_executions.c.execution_id == execution_id)
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if (
                    execution is None
                    or execution["match_id"] != analysis_row["match_id"]
                ):
                    return None
                if execution["status"] != "completed":
                    raise InvalidQueryError("pricing execution is not completed")
                await session.execute(
                    insert(analysis_workflow_events).values(
                        analysis_id=analysis_id,
                        event_type="calculated",
                        execution_id=execution_id,
                    )
                )
                result_events = await _events(session, analysis_id)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "analysis calculation write failed"
            ) from exc
        return _analysis(analysis_row, result_events)

    async def review(
        self, analysis_id: str, actor: str, reason: str
    ) -> Analysis | None:
        try:
            async with self._database.session() as session:
                locked = await _locked_analysis(session, analysis_id)
                if locked is None:
                    return None
                analysis_row, events = locked
                if _status(events) is not AnalysisStatus.CALCULATED:
                    raise InvalidQueryError("analysis is not calculated")
                await session.execute(
                    insert(analysis_workflow_events).values(
                        analysis_id=analysis_id,
                        event_type="reviewed",
                        actor=actor,
                        reason=reason,
                    )
                )
                result_events = await _events(session, analysis_id)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("analysis review write failed") from exc
        return _analysis(analysis_row, result_events)

    async def approve(
        self, analysis_id: str, snapshot_id: str, actor: str, reason: str
    ) -> tuple[Analysis, AnalysisSnapshot] | None:
        try:
            async with self._database.session() as session:
                locked = await _locked_analysis(session, analysis_id)
                if locked is None:
                    return None
                analysis_row, events = locked
                if _status(events) is not AnalysisStatus.CALCULATED:
                    raise InvalidQueryError("analysis is not calculated")
                if not any(
                    event.event_type is AnalysisEventType.REVIEWED for event in events
                ):
                    raise InvalidQueryError("analysis requires review")
                calculated = next(
                    event
                    for event in events
                    if event.event_type is AnalysisEventType.CALCULATED
                )
                execution = (
                    (
                        await session.execute(
                            select(pricing_executions).where(
                                pricing_executions.c.execution_id
                                == calculated.execution_id
                            )
                        )
                    )
                    .mappings()
                    .one()
                )
                approved_at = datetime.now(UTC)
                await session.execute(
                    insert(analysis_workflow_events).values(
                        analysis_id=analysis_id,
                        event_type="approved",
                        actor=actor,
                        reason=reason,
                        created_at=approved_at,
                    )
                )
                result_events = await _events(session, analysis_id)
                payload = await self._snapshot_payload(
                    session, analysis_row, execution, result_events
                )
                row = (
                    (
                        await session.execute(
                            insert(analysis_workflow_snapshots)
                            .values(
                                snapshot_id=snapshot_id,
                                analysis_id=analysis_id,
                                payload=payload,
                                snapshot_hash=snapshot_hash(payload),
                                created_at=approved_at,
                            )
                            .returning(analysis_workflow_snapshots)
                        )
                    )
                    .mappings()
                    .one()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("analysis approval write failed") from exc
        return _analysis(analysis_row, result_events), _snapshot(row)

    async def _snapshot_payload(
        self,
        session: Any,
        analysis_row: RowMapping,
        execution: RowMapping,
        events: tuple[AnalysisEvent, ...],
    ) -> dict[str, Any]:
        match = await self._match_projection(
            session, cast(int, analysis_row["match_id"])
        )
        configuration = await self._effective_configuration(session, match)
        canonical_input = json.loads(cast(str, execution["canonical_input"]))
        canonical_result = json.loads(cast(str, execution["canonical_result"]))
        return {
            "schema_version": 1,
            "analysis": {
                "analysis_id": analysis_row["analysis_id"],
                "match_id": analysis_row["match_id"],
                "created_at": cast(datetime, analysis_row["created_at"]).isoformat(),
                "status": "approved",
                "match": match,
            },
            "effective_configuration": configuration,
            "pricing_execution": {
                "execution_id": execution["execution_id"],
                "match_id": execution["match_id"],
                "status": execution["status"],
                "created_at": cast(datetime, execution["created_at"]).isoformat(),
                "finalized_at": cast(datetime, execution["finalized_at"]).isoformat(),
                "correlation_id": execution["correlation_id"],
                "sample_fingerprint": execution["sample_fingerprint"],
                "sample_match_ids": _sample_match_ids(canonical_input),
                "input_fingerprint": execution["input_fingerprint"],
                "result_fingerprint": execution["result_fingerprint"],
                "pricing_engine_version": execution["pricing_engine_version"],
                "distribution_version": execution["distribution_version"],
                "method_one_version": execution["method_one_version"],
                "schema_version": execution["schema_version"],
                "public_parameters": deepcopy(execution["public_parameters"]),
                "canonical_input": canonical_input,
                "canonical_result": canonical_result,
                "warnings": canonical_result.get("warnings", []),
                "failure_code": execution["failure_code"],
            },
            "events": [_event_payload(event) for event in events],
        }

    async def _match_projection(self, session: Any, match_id: int) -> dict[str, Any]:
        home = teams.alias("analysis_home_team")
        away = teams.alias("analysis_away_team")
        row = (
            (
                await session.execute(
                    select(
                        matches.c.id,
                        matches.c.played_on,
                        seasons.c.id.label("season_id"),
                        seasons.c.label.label("season_label"),
                        competitions.c.id.label("competition_id"),
                        competitions.c.display_name.label("competition_name"),
                        home.c.id.label("home_team_id"),
                        home.c.display_name.label("home_team_name"),
                        away.c.id.label("away_team_id"),
                        away.c.display_name.label("away_team_name"),
                    )
                    .join(seasons, seasons.c.id == matches.c.season_id)
                    .join(competitions, competitions.c.id == seasons.c.competition_id)
                    .join(home, home.c.id == matches.c.home_team_id)
                    .join(away, away.c.id == matches.c.away_team_id)
                    .where(matches.c.id == match_id)
                )
            )
            .mappings()
            .one()
        )
        return {
            "match_id": row["id"],
            "played_on": row["played_on"].isoformat(),
            "season": {"id": row["season_id"], "label": row["season_label"]},
            "competition": {
                "id": row["competition_id"],
                "display_name": row["competition_name"],
            },
            "home_team": {
                "id": row["home_team_id"],
                "display_name": row["home_team_name"],
            },
            "away_team": {
                "id": row["away_team_id"],
                "display_name": row["away_team_name"],
            },
        }

    async def _effective_configuration(
        self, session: Any, match: dict[str, Any]
    ) -> dict[str, Any]:
        match_id = cast(int, match["match_id"])
        competition_id = cast(int, cast(dict[str, Any], match["competition"])["id"])
        catalog = (
            (
                await session.execute(
                    select(configuration_catalogs).where(
                        configuration_catalogs.c.catalog_id == CATALOG_ID
                    )
                )
            )
            .mappings()
            .one()
        )
        rows = (
            (
                await session.execute(
                    select(configuration_revisions).where(
                        configuration_revisions.c.catalog_id == CATALOG_ID,
                        or_(
                            configuration_revisions.c.scope == "global",
                            and_(
                                configuration_revisions.c.scope == "competition",
                                configuration_revisions.c.competition_id
                                == competition_id,
                            ),
                            and_(
                                configuration_revisions.c.scope == "match",
                                configuration_revisions.c.match_id == match_id,
                            ),
                        ),
                    )
                )
            )
            .mappings()
            .all()
        )
        priority = {"match": 0, "competition": 1, "global": 2}
        sorted_rows = sorted(
            rows,
            key=lambda row: (
                row["parameter_code"],
                priority[cast(str, row["scope"])],
                -cast(datetime, row["created_at"]).timestamp(),
                -cast(int, row["id"]),
            ),
        )
        selected: list[RowMapping] = []
        discarded: list[RowMapping] = []
        seen: set[str] = set()
        for row in sorted_rows:
            code = cast(str, row["parameter_code"])
            if code in seen:
                discarded.append(row)
            else:
                seen.add(code)
                selected.append(row)
        selected.sort(key=lambda row: cast(str, row["parameter_code"]))
        discarded.sort(key=lambda row: cast(int, row["id"]))
        selected_payload = [_revision_payload(row) for row in selected]
        catalog_payload = {
            "catalog_id": catalog["catalog_id"],
            "schema_version": catalog["schema_version"],
            "payload": deepcopy(catalog["payload"]),
            "content_hash": catalog["content_hash"],
            "created_at": cast(datetime, catalog["created_at"]).isoformat(),
        }
        from lvfi_api.domain.configuration import configuration_hash

        effective_hash = configuration_hash(
            {
                "catalog_id": catalog["catalog_id"],
                "catalog_hash": catalog["content_hash"],
                "match_id": match_id,
                "competition_id": competition_id,
                "selected_revisions": [
                    {
                        "parameter_code": row["parameter_code"],
                        "revision_id": row["id"],
                        "catalog_hash": row["catalog_hash"],
                        "revision_hash": row["revision_hash"],
                        "scope": row["scope"],
                        "value": row["value"],
                    }
                    for row in selected
                ],
            }
        )
        return {
            "match_id": match_id,
            "competition_id": competition_id,
            "catalog": catalog_payload,
            "values": {
                cast(str, row["parameter_code"]): deepcopy(row["value"])
                for row in selected
            },
            "selected_revisions": selected_payload,
            "discarded_revisions": [_revision_payload(row) for row in discarded],
            "effective_hash": effective_hash,
        }

    async def get(self, analysis_id: str) -> Analysis | None:
        try:
            async with self._database.session() as session:
                row = (
                    (
                        await session.execute(
                            select(analysis_workflow_analyses).where(
                                analysis_workflow_analyses.c.analysis_id == analysis_id
                            )
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None:
                    return None
                events = await _events(session, analysis_id)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("analysis query failed") from exc
        return _analysis(row, events)

    async def list_by_match(self, match_id: int) -> tuple[Analysis, ...] | None:
        try:
            async with self._database.session() as session:
                if (
                    await session.scalar(
                        select(matches.c.id).where(matches.c.id == match_id)
                    )
                    is None
                ):
                    return None
                rows = (
                    (
                        await session.execute(
                            select(analysis_workflow_analyses)
                            .where(analysis_workflow_analyses.c.match_id == match_id)
                            .order_by(
                                analysis_workflow_analyses.c.created_at.asc(),
                                analysis_workflow_analyses.c.analysis_id.asc(),
                            )
                        )
                    )
                    .mappings()
                    .all()
                )
                values: list[Analysis] = []
                for row in rows:
                    values.append(
                        _analysis(
                            row,
                            await _events(session, cast(str, row["analysis_id"])),
                        )
                    )
                return tuple(values)
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("analysis history unavailable") from exc

    async def get_snapshot_by_analysis(
        self, analysis_id: str
    ) -> AnalysisSnapshot | None:
        return await self._get_snapshot(
            analysis_workflow_snapshots.c.analysis_id == analysis_id
        )

    async def get_snapshot(self, snapshot_id: str) -> AnalysisSnapshot | None:
        return await self._get_snapshot(
            analysis_workflow_snapshots.c.snapshot_id == snapshot_id
        )

    async def _get_snapshot(self, condition: Any) -> AnalysisSnapshot | None:
        try:
            async with self._database.session() as session:
                row = (
                    (
                        await session.execute(
                            select(analysis_workflow_snapshots).where(condition)
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("analysis snapshot unavailable") from exc
        return _snapshot(row) if row is not None else None
