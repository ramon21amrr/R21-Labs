"""Validated operational-data commands with explicit persistence boundaries."""

from __future__ import annotations

from typing import Protocol

from lvfi_api.domain.errors import InvalidQueryError, ResourceNotFoundError
from lvfi_api.domain.operational_data import (
    FutureMatch,
    FutureMatchDraft,
    StatisticRevision,
    StatisticRevisionDraft,
    valid_future_match,
    valid_statistic_revision,
)


class OperationalDataRepository(Protocol):
    async def create_future_match(
        self, draft: FutureMatchDraft
    ) -> FutureMatch | None: ...

    async def revise_statistic(
        self, draft: StatisticRevisionDraft
    ) -> StatisticRevision | None: ...


class OperationalDataService:
    def __init__(self, repository: OperationalDataRepository) -> None:
        self._repository = repository

    async def create_future_match(self, draft: FutureMatchDraft) -> FutureMatch:
        if not valid_future_match(draft):
            raise InvalidQueryError("invalid future match")
        value = await self._repository.create_future_match(draft)
        if value is None:
            raise InvalidQueryError("canonical match conflict")
        return value

    async def revise_statistic(
        self, draft: StatisticRevisionDraft
    ) -> StatisticRevision:
        if not valid_statistic_revision(draft):
            raise InvalidQueryError("invalid statistic revision")
        value = await self._repository.revise_statistic(draft)
        if value is None:
            raise ResourceNotFoundError("match statistics")
        return value
