"""Application service for append-only configuration revisioning."""

from __future__ import annotations

from typing import Protocol

from lvfi_api.domain.configuration import (
    ConfigurationCatalog,
    ConfigurationRevision,
    ConfigurationRevisionDraft,
    EffectiveConfiguration,
    valid_revision_draft,
)
from lvfi_api.domain.errors import InvalidQueryError, ResourceNotFoundError


class ConfigurationRepository(Protocol):
    async def get_catalog(self) -> ConfigurationCatalog | None: ...

    async def create_revision(
        self, draft: ConfigurationRevisionDraft
    ) -> ConfigurationRevision | None: ...

    async def get_history(
        self,
        parameter_code: str | None,
        scope: str | None,
        competition_id: int | None,
        match_id: int | None,
    ) -> tuple[ConfigurationRevision, ...]: ...

    async def effective(self, match_id: int) -> EffectiveConfiguration | None: ...


class ConfigurationService:
    def __init__(self, repository: ConfigurationRepository) -> None:
        self._repository = repository

    async def get_catalog(self) -> ConfigurationCatalog:
        catalog = await self._repository.get_catalog()
        if catalog is None:
            raise ResourceNotFoundError("configuration catalog")
        return catalog

    async def create_revision(
        self, draft: ConfigurationRevisionDraft
    ) -> ConfigurationRevision:
        if not valid_revision_draft(draft):
            raise InvalidQueryError("invalid configuration revision")
        revision = await self._repository.create_revision(draft)
        if revision is None:
            raise ResourceNotFoundError("configuration scope")
        return revision

    async def get_history(
        self,
        parameter_code: str | None,
        scope: str | None,
        competition_id: int | None,
        match_id: int | None,
    ) -> tuple[ConfigurationRevision, ...]:
        if scope not in {None, "global", "competition", "match"}:
            raise InvalidQueryError("invalid configuration scope")
        if competition_id is not None and competition_id < 1:
            raise InvalidQueryError("invalid competition")
        if match_id is not None and match_id < 1:
            raise InvalidQueryError("invalid match")
        return await self._repository.get_history(
            parameter_code, scope, competition_id, match_id
        )

    async def effective(self, match_id: int) -> EffectiveConfiguration:
        if match_id < 1:
            raise InvalidQueryError("invalid match")
        value = await self._repository.effective(match_id)
        if value is None:
            raise ResourceNotFoundError("match")
        return value
