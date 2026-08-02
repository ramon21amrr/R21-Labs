"""PostgreSQL repository for append-only Method One pricing execution records."""

from __future__ import annotations

import json
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.pricing_executions import (
    PricingExecution,
    PricingExecutionDraft,
    PricingExecutionHistoryFilters,
    PricingExecutionStatus,
)
from lvfi_api.persistence.historical_models import matches, pricing_executions
from lvfi_api.persistence.historical_queries import SessionProvider


def _record(row: RowMapping) -> PricingExecution:
    """Map only the immutable, public-safe execution columns."""
    canonical_input = row["canonical_input"]
    canonical_result = row["canonical_result"]
    return PricingExecution(
        execution_id=cast(str, row["execution_id"]),
        match_id=cast(int, row["match_id"]),
        status=PricingExecutionStatus(cast(str, row["status"])),
        created_at=cast(Any, row["created_at"]),
        finalized_at=cast(Any, row["finalized_at"]),
        correlation_id=cast(str, row["correlation_id"]),
        sample_fingerprint=cast(str, row["sample_fingerprint"]),
        input_fingerprint=cast(str | None, row["input_fingerprint"]),
        result_fingerprint=cast(str | None, row["result_fingerprint"]),
        pricing_engine_version=cast(str, row["pricing_engine_version"]),
        distribution_version=cast(str, row["distribution_version"]),
        method_one_version=cast(str, row["method_one_version"]),
        schema_version=cast(int, row["schema_version"]),
        public_parameters=cast(dict[str, Any], row["public_parameters"]),
        canonical_input=(
            cast(dict[str, Any], json.loads(cast(str, canonical_input)))
            if canonical_input is not None
            else None
        ),
        canonical_result=(
            cast(dict[str, Any], json.loads(cast(str, canonical_result)))
            if canonical_result is not None
            else None
        ),
        failure_code=cast(str | None, row["failure_code"]),
    )


class SqlAlchemyPricingExecutionRepository:
    """Keep execution storage set-based, transactional, and append-only."""

    def __init__(self, database: SessionProvider) -> None:
        self._database = database

    async def get(self, execution_id: str) -> PricingExecution | None:
        statement = select(pricing_executions).where(
            pricing_executions.c.execution_id == execution_id
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("pricing execution query failed") from exc
        return _record(row) if row is not None else None

    async def get_many(
        self, execution_ids: tuple[str, ...]
    ) -> tuple[PricingExecution, ...]:
        if not execution_ids:
            return ()
        statement = select(pricing_executions).where(
            pricing_executions.c.execution_id.in_(execution_ids)
        )
        try:
            async with self._database.session() as session:
                rows = (await session.execute(statement)).mappings().all()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("pricing execution query failed") from exc
        return tuple(_record(row) for row in rows)

    async def get_by_idempotency_key(
        self, match_id: int, idempotency_key: str
    ) -> PricingExecution | None:
        statement = select(pricing_executions).where(
            pricing_executions.c.match_id == match_id,
            pricing_executions.c.idempotency_key == idempotency_key,
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("pricing execution query failed") from exc
        return _record(row) if row is not None else None

    async def create(self, draft: PricingExecutionDraft) -> PricingExecution:
        values = {
            "execution_id": draft.execution_id,
            "match_id": draft.match_id,
            "status": draft.status.value,
            "finalized_at": draft.finalized_at,
            "correlation_id": draft.correlation_id,
            "idempotency_key": draft.idempotency_key,
            "sample_fingerprint": draft.sample_fingerprint,
            "input_fingerprint": draft.input_fingerprint,
            "result_fingerprint": draft.result_fingerprint,
            "pricing_engine_version": draft.pricing_engine_version,
            "distribution_version": draft.distribution_version,
            "method_one_version": draft.method_one_version,
            "schema_version": draft.schema_version,
            "public_parameters": draft.public_parameters,
            "canonical_input": draft.canonical_input,
            "canonical_result": draft.canonical_result,
            "failure_code": draft.failure_code,
        }
        statement = (
            insert(pricing_executions)
            .values(**values)
            .on_conflict_do_nothing(constraint="execution_match_idempotency_key")
            .returning(pricing_executions)
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
                if row is None:
                    row = (
                        (
                            await session.execute(
                                select(pricing_executions).where(
                                    pricing_executions.c.match_id == draft.match_id,
                                    pricing_executions.c.idempotency_key
                                    == draft.idempotency_key,
                                )
                            )
                        )
                        .mappings()
                        .one()
                    )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("pricing execution write failed") from exc
        return _record(row)

    async def list_by_match(
        self,
        match_id: int,
        page: int,
        page_size: int,
        filters: PricingExecutionHistoryFilters | None = None,
    ) -> Page[PricingExecution] | None:
        conditions = [pricing_executions.c.match_id == match_id]
        if filters is not None:
            if filters.status is not None:
                conditions.append(pricing_executions.c.status == filters.status.value)
            if filters.created_from is not None:
                conditions.append(
                    pricing_executions.c.created_at >= filters.created_from
                )
            if filters.created_to is not None:
                conditions.append(pricing_executions.c.created_at <= filters.created_to)
            if filters.pricing_engine_version is not None:
                conditions.append(
                    pricing_executions.c.pricing_engine_version
                    == filters.pricing_engine_version
                )
            if filters.method_one_version is not None:
                conditions.append(
                    pricing_executions.c.method_one_version
                    == filters.method_one_version
                )
            if filters.sample_fingerprint is not None:
                conditions.append(
                    pricing_executions.c.sample_fingerprint
                    == filters.sample_fingerprint
                )
            if filters.correlation_id is not None:
                conditions.append(
                    pricing_executions.c.correlation_id == filters.correlation_id
                )
        descending = filters is None or filters.order == "created_at_desc"
        created_order = (
            pricing_executions.c.created_at.desc()
            if descending
            else pricing_executions.c.created_at.asc()
        )
        identifier_order = (
            pricing_executions.c.execution_id.desc()
            if descending
            else pricing_executions.c.execution_id.asc()
        )
        statement = (
            select(pricing_executions)
            .where(*conditions)
            .order_by(created_order, identifier_order)
        )
        try:
            async with self._database.session() as session:
                exists = await session.scalar(
                    select(matches.c.id).where(matches.c.id == match_id)
                )
                if exists is None:
                    return None
                total = cast(
                    int,
                    await session.scalar(
                        select(func.count()).select_from(statement.subquery())
                    ),
                )
                rows = (
                    (
                        await session.execute(
                            statement.limit(page_size).offset((page - 1) * page_size)
                        )
                    )
                    .mappings()
                    .all()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("pricing execution query failed") from exc
        return Page(tuple(_record(row) for row in rows), page, page_size, total)
