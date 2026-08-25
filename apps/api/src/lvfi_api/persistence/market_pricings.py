"""PostgreSQL repository for append-only theoretical market-pricing snapshots."""

from __future__ import annotations

import json
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.market_pricings import MarketPricing, MarketPricingDraft
from lvfi_api.persistence.historical_models import market_pricings, matches
from lvfi_api.persistence.historical_queries import SessionProvider


def _record(row: RowMapping) -> MarketPricing:
    return MarketPricing(
        market_pricing_id=cast(str, row["market_pricing_id"]),
        match_id=cast(int, row["match_id"]),
        created_at=cast(Any, row["created_at"]),
        finalized_at=cast(Any, row["finalized_at"]),
        correlation_id=cast(str, row["correlation_id"]),
        source_model_version=cast(str, row["source_model_version"]),
        source_execution_id=cast(str | None, row["source_execution_id"]),
        rate_snapshot_schema_version=cast(int, row["rate_snapshot_schema_version"]),
        rates_fingerprint=cast(str, row["rates_fingerprint"]),
        pricing_engine_version=cast(str, row["pricing_engine_version"]),
        schema_version=cast(int, row["schema_version"]),
        input_fingerprint=cast(str, row["input_fingerprint"]),
        result_fingerprint=cast(str, row["result_fingerprint"]),
        engine_result_fingerprint=cast(str, row["engine_result_fingerprint"]),
        canonical_input=cast(
            dict[str, Any], json.loads(cast(str, row["canonical_input"]))
        ),
        canonical_result=cast(
            dict[str, Any], json.loads(cast(str, row["canonical_result"]))
        ),
    )


class SqlAlchemyMarketPricingRepository:
    """One immutable insert per price computation and deterministic read order."""

    def __init__(self, database: SessionProvider) -> None:
        self._database = database

    async def get(self, market_pricing_id: str) -> MarketPricing | None:
        try:
            async with self._database.session() as session:
                row = (
                    (
                        await session.execute(
                            select(market_pricings).where(
                                market_pricings.c.market_pricing_id == market_pricing_id
                            )
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("market pricing query failed") from exc
        return _record(row) if row is not None else None

    async def get_by_idempotency_key(
        self, match_id: int, idempotency_key: str
    ) -> MarketPricing | None:
        try:
            async with self._database.session() as session:
                row = (
                    (
                        await session.execute(
                            select(market_pricings).where(
                                market_pricings.c.match_id == match_id,
                                market_pricings.c.idempotency_key == idempotency_key,
                            )
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("market pricing query failed") from exc
        return _record(row) if row is not None else None

    async def create(self, draft: MarketPricingDraft) -> MarketPricing:
        values = {
            "market_pricing_id": draft.market_pricing_id,
            "match_id": draft.match_id,
            "finalized_at": draft.finalized_at,
            "correlation_id": draft.correlation_id,
            "idempotency_key": draft.idempotency_key,
            "source_model_version": draft.rates.source_model_version,
            "source_execution_id": draft.rates.source_execution_id,
            "rate_snapshot_schema_version": draft.rates.schema_version,
            "rates_fingerprint": draft.rates_fingerprint,
            "pricing_engine_version": draft.pricing_engine_version,
            "schema_version": 1,
            "input_fingerprint": draft.input_fingerprint,
            "result_fingerprint": draft.result_fingerprint,
            "engine_result_fingerprint": draft.engine_result_fingerprint,
            "canonical_input": draft.canonical_input,
            "canonical_result": draft.canonical_result,
        }
        statement = (
            insert(market_pricings)
            .values(**values)
            .on_conflict_do_nothing(constraint="market_pricing_match_idempotency_key")
            .returning(market_pricings)
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
                if row is None:
                    row = (
                        (
                            await session.execute(
                                select(market_pricings).where(
                                    market_pricings.c.match_id == draft.match_id,
                                    market_pricings.c.idempotency_key
                                    == draft.idempotency_key,
                                )
                            )
                        )
                        .mappings()
                        .one()
                    )
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("market pricing write failed") from exc
        return _record(row)

    async def list_by_match(
        self, match_id: int, page: int, page_size: int
    ) -> Page[MarketPricing] | None:
        statement = (
            select(market_pricings)
            .where(market_pricings.c.match_id == match_id)
            .order_by(
                market_pricings.c.created_at.desc(),
                market_pricings.c.market_pricing_id.desc(),
            )
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
            raise PersistenceUnavailableError("market pricing query failed") from exc
        return Page(tuple(_record(row) for row in rows), page, page_size, total)
