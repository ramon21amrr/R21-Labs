"""PostgreSQL storage for append-only controlled reproduction attempts."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.pricing_execution_reproductions import (
    PricingExecutionReproduction,
    PricingExecutionReproductionDraft,
    PricingExecutionReproductionOutcome,
)
from lvfi_api.persistence.historical_models import pricing_execution_reproductions
from lvfi_api.persistence.historical_queries import SessionProvider


def _record(row: RowMapping) -> PricingExecutionReproduction:
    return PricingExecutionReproduction(
        reproduction_id=cast(str, row["reproduction_id"]),
        execution_id=cast(str, row["execution_id"]),
        outcome=PricingExecutionReproductionOutcome(cast(str, row["outcome"])),
        created_at=cast(Any, row["created_at"]),
        finalized_at=cast(Any, row["finalized_at"]),
        correlation_id=cast(str, row["correlation_id"]),
        original_input_fingerprint=cast(str | None, row["original_input_fingerprint"]),
        reproduced_input_fingerprint=cast(
            str | None, row["reproduced_input_fingerprint"]
        ),
        original_result_fingerprint=cast(
            str | None, row["original_result_fingerprint"]
        ),
        reproduced_result_fingerprint=cast(
            str | None, row["reproduced_result_fingerprint"]
        ),
        original_pricing_engine_version=cast(
            str, row["original_pricing_engine_version"]
        ),
        current_pricing_engine_version=cast(str, row["current_pricing_engine_version"]),
        original_distribution_version=cast(str, row["original_distribution_version"]),
        current_distribution_version=cast(str, row["current_distribution_version"]),
        original_method_one_version=cast(str, row["original_method_one_version"]),
        current_method_one_version=cast(str, row["current_method_one_version"]),
        original_schema_version=cast(int, row["original_schema_version"]),
        current_schema_version=cast(int, row["current_schema_version"]),
        differences=tuple(cast(list[dict[str, Any]], row["differences"])),
        failure_code=cast(str | None, row["failure_code"]),
    )


class SqlAlchemyPricingExecutionReproductionRepository:
    """Use one insert per attempt and set-based deterministic reads."""

    def __init__(self, database: SessionProvider) -> None:
        self._database = database

    async def create(
        self, draft: PricingExecutionReproductionDraft
    ) -> PricingExecutionReproduction:
        values = {
            name: getattr(draft, name)
            for name in PricingExecutionReproductionDraft.__dataclass_fields__
        }
        statement = (
            insert(pricing_execution_reproductions)
            .values(**values)
            .returning(pricing_execution_reproductions)
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "pricing reproduction write failed"
            ) from exc
        return _record(row)

    async def get(self, reproduction_id: str) -> PricingExecutionReproduction | None:
        statement = select(pricing_execution_reproductions).where(
            pricing_execution_reproductions.c.reproduction_id == reproduction_id
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError(
                "pricing reproduction query failed"
            ) from exc
        return _record(row) if row is not None else None

    async def list_by_execution(
        self, execution_id: str, page: int, page_size: int
    ) -> Page[PricingExecutionReproduction]:
        statement = (
            select(pricing_execution_reproductions)
            .where(pricing_execution_reproductions.c.execution_id == execution_id)
            .order_by(
                pricing_execution_reproductions.c.created_at.desc(),
                pricing_execution_reproductions.c.reproduction_id.desc(),
            )
        )
        try:
            async with self._database.session() as session:
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
            raise PersistenceUnavailableError(
                "pricing reproduction query failed"
            ) from exc
        return Page(tuple(_record(row) for row in rows), page, page_size, total)
