"""Set-based PostgreSQL persistence for immutable manual market references."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.market_pricings import MarketPricing
from lvfi_api.domain.market_reference_observations import (
    MarketReferenceObservation,
    MarketReferenceObservationDraft,
)
from lvfi_api.persistence.historical_models import (
    market_pricings,
    market_reference_observations,
    matches,
)
from lvfi_api.persistence.historical_queries import SessionProvider
from lvfi_api.persistence.market_pricings import _record as market_pricing_record


def _record(row: RowMapping) -> MarketReferenceObservation:
    return MarketReferenceObservation(
        observation_id=cast(str, row["observation_id"]),
        match_id=cast(int, row["match_id"]),
        market_pricing_id=cast(str, row["market_pricing_id"]),
        market_code=cast(str, row["market_code"]),
        selection=cast(str, row["selection"]),
        model_line_quarters=cast(int | None, row["model_line_quarters"]),
        reference_line_quarters=cast(int | None, row["reference_line_quarters"]),
        reference_value=cast(float, row["reference_value"]),
        observed_at=cast(Any, row["observed_at"]),
        created_at=cast(Any, row["created_at"]),
        correlation_id=cast(str, row["correlation_id"]),
    )


class SqlAlchemyMarketReferenceRepository:
    def __init__(self, database: SessionProvider) -> None:
        self._database = database

    async def get_snapshot(self, market_pricing_id: str) -> MarketPricing | None:
        statement = select(market_pricings).where(
            market_pricings.c.market_pricing_id == market_pricing_id
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("market reference query failed") from exc
        return market_pricing_record(row) if row is not None else None

    async def get(self, observation_id: str) -> MarketReferenceObservation | None:
        statement = select(market_reference_observations).where(
            market_reference_observations.c.observation_id == observation_id
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("market reference query failed") from exc
        return _record(row) if row is not None else None

    async def get_by_idempotency_key(
        self, match_id: int, idempotency_key: str
    ) -> MarketReferenceObservation | None:
        statement = select(market_reference_observations).where(
            market_reference_observations.c.match_id == match_id,
            market_reference_observations.c.idempotency_key == idempotency_key,
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("market reference query failed") from exc
        return _record(row) if row is not None else None

    async def create(
        self, draft: MarketReferenceObservationDraft
    ) -> MarketReferenceObservation:
        values = {name: getattr(draft, name) for name in draft.__dataclass_fields__}
        statement = (
            insert(market_reference_observations)
            .values(**values)
            .on_conflict_do_nothing(
                constraint="market_reference_match_idempotency_key"
            )
            .returning(market_reference_observations)
        )
        try:
            async with self._database.session() as session:
                row = (await session.execute(statement)).mappings().one_or_none()
                if row is None:
                    existing = select(market_reference_observations).where(
                        market_reference_observations.c.match_id == draft.match_id,
                        market_reference_observations.c.idempotency_key
                        == draft.idempotency_key,
                    )
                    row = (await session.execute(existing)).mappings().one()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("market reference write failed") from exc
        return _record(row)

    async def list_by_match_snapshot(
        self, match_id: int, market_pricing_id: str, page: int, page_size: int
    ) -> Page[MarketReferenceObservation] | None:
        statement = (
            select(market_reference_observations)
            .where(
                market_reference_observations.c.match_id == match_id,
                market_reference_observations.c.market_pricing_id == market_pricing_id,
            )
            .order_by(
                market_reference_observations.c.observed_at.desc(),
                market_reference_observations.c.observation_id.desc(),
            )
        )
        try:
            async with self._database.session() as session:
                match = await session.scalar(
                    select(matches.c.id).where(matches.c.id == match_id)
                )
                if match is None:
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
            raise PersistenceUnavailableError("market reference query failed") from exc
        return Page(tuple(_record(row) for row in rows), page, page_size, total)
