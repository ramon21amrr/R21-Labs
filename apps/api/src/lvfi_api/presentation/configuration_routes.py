"""Strict HTTP contracts for the APP-014 configuration ledger."""
# ruff: noqa: B008

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal, cast

from fastapi import APIRouter, Depends, Path, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

from lvfi_api.application.configuration import ConfigurationService
from lvfi_api.domain.configuration import (
    ConfigurationCatalog,
    ConfigurationRevision,
    ConfigurationRevisionDraft,
    EffectiveConfiguration,
)
from lvfi_api.domain.errors import InvalidQueryError, PersistenceUnavailableError
from lvfi_api.persistence.configuration import SqlAlchemyConfigurationRepository
from lvfi_api.presentation.local_admin_authentication_routes import (
    require_authenticated_admin,
)

catalog_router = APIRouter(tags=["configuration"])
administration_router = APIRouter(prefix="/administration", tags=["configuration"])
match_router = APIRouter(tags=["configuration"])


class CatalogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    catalog_id: str
    schema_version: int
    payload: dict[str, Any]
    content_hash: str
    created_at: str

    @classmethod
    def from_contract(cls, value: ConfigurationCatalog) -> CatalogResponse:
        return cls(
            catalog_id=value.catalog_id,
            schema_version=value.schema_version,
            payload=value.payload,
            content_hash=value.content_hash,
            created_at=str(value.created_at),
        )


class ConfigurationRevisionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    catalog_id: Literal["lvfi-mvp@1.0.0"]
    scope: Literal["global", "competition", "match"]
    parameter_code: StrictStr = Field(min_length=1, max_length=64)
    value: StrictInt | StrictStr
    competition_id: StrictInt | None = Field(default=None, ge=1)
    match_id: StrictInt | None = Field(default=None, ge=1)
    reason: StrictStr = Field(min_length=1, max_length=2000)


class ConfigurationRevisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision_id: int
    catalog_id: str
    catalog_hash: str
    scope: Literal["global", "competition", "match"]
    parameter_code: str
    value: int | str
    competition_id: int | None
    match_id: int | None
    actor: str
    reason: str
    replaces_revision_id: int | None
    revision_hash: str
    created_at: str

    @classmethod
    def from_contract(
        cls, value: ConfigurationRevision
    ) -> ConfigurationRevisionResponse:
        return cls(
            revision_id=value.revision_id,
            catalog_id=value.catalog_id,
            catalog_hash=value.catalog_hash,
            scope=value.scope,
            parameter_code=value.parameter_code,
            value=cast(int | str, value.value),
            competition_id=value.competition_id,
            match_id=value.match_id,
            actor=value.actor,
            reason=value.reason,
            replaces_revision_id=value.replaces_revision_id,
            revision_hash=value.revision_hash,
            created_at=str(value.created_at),
        )


class ConfigurationHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revisions: list[ConfigurationRevisionResponse]


class EffectiveConfigurationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    match_id: int
    competition_id: int
    catalog_id: str
    catalog_hash: str
    values: dict[str, int | str]
    selected_revisions: list[ConfigurationRevisionResponse]
    discarded_revisions: list[ConfigurationRevisionResponse]
    effective_hash: str

    @classmethod
    def from_contract(
        cls, value: EffectiveConfiguration
    ) -> EffectiveConfigurationResponse:
        return cls(
            match_id=value.match_id,
            competition_id=value.competition_id,
            catalog_id=value.catalog_id,
            catalog_hash=value.catalog_hash,
            values=cast(dict[str, int | str], value.values),
            selected_revisions=[
                ConfigurationRevisionResponse.from_contract(item)
                for item in value.selected_revisions
            ],
            discarded_revisions=[
                ConfigurationRevisionResponse.from_contract(item)
                for item in value.discarded_revisions
            ],
            effective_hash=value.effective_hash,
        )


async def get_configuration_service(request: Request) -> ConfigurationService:
    injected = getattr(request.app.state, "configuration_service", None)
    if injected is not None:
        return cast(ConfigurationService, injected)
    database = request.app.state.database
    if not hasattr(database, "session"):
        raise PersistenceUnavailableError("configuration database unavailable")
    return ConfigurationService(SqlAlchemyConfigurationRepository(database))


def _only_query_parameters(*allowed: str) -> Callable[[Request], Awaitable[None]]:
    allowed_parameters = frozenset(allowed)

    async def validate(request: Request) -> None:
        if set(request.query_params) - allowed_parameters:
            raise InvalidQueryError("unsupported query parameter")

    return validate


@catalog_router.get(
    "/configuration-catalogs/lvfi-mvp/1.0.0",
    response_model=CatalogResponse,
)
async def get_catalog(
    service: ConfigurationService = Depends(get_configuration_service),
) -> CatalogResponse:
    return CatalogResponse.from_contract(await service.get_catalog())


@administration_router.post(
    "/configuration-revisions",
    response_model=ConfigurationRevisionResponse,
    status_code=201,
)
async def create_configuration_revision(
    payload: ConfigurationRevisionCreateRequest,
    actor: str = Depends(require_authenticated_admin),
    service: ConfigurationService = Depends(get_configuration_service),
) -> ConfigurationRevisionResponse:
    return ConfigurationRevisionResponse.from_contract(
        await service.create_revision(
            ConfigurationRevisionDraft(actor=actor, **payload.model_dump())
        )
    )


@administration_router.get(
    "/configuration-revisions",
    response_model=ConfigurationHistoryResponse,
    dependencies=[
        Depends(
            _only_query_parameters(
                "parameter_code", "scope", "competition_id", "match_id"
            )
        )
    ],
)
async def get_configuration_history(
    parameter_code: str | None = Query(default=None, min_length=1, max_length=64),
    scope: Literal["global", "competition", "match"] | None = Query(default=None),
    competition_id: int | None = Query(default=None, ge=1),
    match_id: int | None = Query(default=None, ge=1),
    service: ConfigurationService = Depends(get_configuration_service),
) -> ConfigurationHistoryResponse:
    return ConfigurationHistoryResponse(
        revisions=[
            ConfigurationRevisionResponse.from_contract(item)
            for item in await service.get_history(
                parameter_code, scope, competition_id, match_id
            )
        ]
    )


@match_router.get(
    "/matches/{match_id}/configuration/effective",
    response_model=EffectiveConfigurationResponse,
)
async def get_effective_configuration(
    match_id: int = Path(ge=1),
    service: ConfigurationService = Depends(get_configuration_service),
) -> EffectiveConfigurationResponse:
    return EffectiveConfigurationResponse.from_contract(
        await service.effective(match_id)
    )
