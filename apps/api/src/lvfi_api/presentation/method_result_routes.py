"""Read-only HTTP results for the existing Methods Two and Three services."""
# ruff: noqa: B008

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Literal, cast

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict

from lvfi_api.application.method_three import MethodThreeObservedFrequencyService
from lvfi_api.application.method_two import MethodTwoAdjustedPoissonService
from lvfi_api.domain.errors import InvalidQueryError
from lvfi_api.domain.method_three import MethodThreeConfiguration, MethodThreeResult
from lvfi_api.domain.method_two import MethodTwoConfiguration, MethodTwoResult
from lvfi_api.presentation.statistics_routes import get_statistics_sample_service

router = APIRouter(tags=["method results"])


class MethodResultResponse(BaseModel):
    """Opaque evidence comes from the domain service; the client never calculates it."""

    model_config = ConfigDict(extra="forbid")
    method: str
    method_version: str
    payload: dict[str, Any]

    @classmethod
    def from_contract(
        cls, value: MethodTwoResult | MethodThreeResult
    ) -> MethodResultResponse:
        return cls(
            method=value.method,
            method_version=value.method_version,
            payload=cast(dict[str, Any], jsonable_encoder(asdict(value))),
        )


async def get_method_two_service(request: Request) -> MethodTwoAdjustedPoissonService:
    injected = getattr(request.app.state, "method_two_service", None)
    if injected is not None:
        return cast(MethodTwoAdjustedPoissonService, injected)
    return MethodTwoAdjustedPoissonService(await get_statistics_sample_service(request))


async def get_method_three_service(
    request: Request,
) -> MethodThreeObservedFrequencyService:
    injected = getattr(request.app.state, "method_three_service", None)
    if injected is not None:
        return cast(MethodThreeObservedFrequencyService, injected)
    return MethodThreeObservedFrequencyService(
        await get_statistics_sample_service(request)
    )


def _validate_query_parameters(request: Request, *allowed: str) -> None:
    if set(request.query_params) - set(allowed):
        raise InvalidQueryError("unsupported query parameter")


def _validate_season(season_scope: str, previous_season_id: int | None) -> None:
    if season_scope == "current_and_previous" and previous_season_id is None:
        raise InvalidQueryError("previous season is required")
    if season_scope == "current" and previous_season_id is not None:
        raise InvalidQueryError("previous season is unsupported")


@router.get(
    "/matches/{match_id}/method-two/result",
    response_model=MethodResultResponse,
    summary="Build a read-only Method Two result from explicit selectors",
)
async def get_method_two_result(
    request: Request,
    match_id: int = Path(ge=1),
    sample_size: int = Query(..., ge=5, le=20),
    context: Literal["venue", "overall"] = Query(...),
    season_scope: Literal["current", "current_and_previous"] = Query(...),
    previous_season_id: int | None = Query(default=None, ge=1),
    metric: Literal[
        "goals_scored", "corners", "shots_on_target", "shots", "cards", "fouls"
    ] = Query(...),
    service: MethodTwoAdjustedPoissonService = Depends(get_method_two_service),
) -> MethodResultResponse:
    _validate_query_parameters(
        request,
        "sample_size",
        "context",
        "season_scope",
        "previous_season_id",
        "metric",
    )
    _validate_season(season_scope, previous_season_id)
    if sample_size not in {5, 10, 15, 20}:
        raise InvalidQueryError("unsupported sample size")
    return MethodResultResponse.from_contract(
        await service.execute(
            match_id,
            MethodTwoConfiguration(
                sample_size=cast(Literal[5, 10, 15, 20], sample_size),
                context=context,
                season_scope=season_scope,
                previous_season_id=previous_season_id,
                metric=metric,
            ),
        )
    )


@router.get(
    "/matches/{match_id}/method-three/result",
    response_model=MethodResultResponse,
    summary="Build a read-only Method Three result from explicit selectors",
)
async def get_method_three_result(
    request: Request,
    match_id: int = Path(ge=1),
    sample_size: int = Query(..., ge=5, le=20),
    competition_scope: Literal["target_competition", "all_eligible"] = Query(...),
    season_scope: Literal["current", "current_and_previous"] = Query(...),
    previous_season_id: int | None = Query(default=None, ge=1),
    metric: Literal[
        "goals_scored",
        "goals_conceded",
        "result_win",
        "corners",
        "shots_on_target",
        "shots",
        "cards",
        "fouls",
    ] = Query(...),
    comparator: Literal["at_least", "at_most", "equal"] = Query(...),
    achievement_target: int = Query(..., ge=0),
    service: MethodThreeObservedFrequencyService = Depends(get_method_three_service),
) -> MethodResultResponse:
    _validate_query_parameters(
        request,
        "sample_size",
        "competition_scope",
        "season_scope",
        "previous_season_id",
        "metric",
        "comparator",
        "achievement_target",
    )
    _validate_season(season_scope, previous_season_id)
    if sample_size not in {5, 10, 15, 20}:
        raise InvalidQueryError("unsupported sample size")
    return MethodResultResponse.from_contract(
        await service.execute(
            match_id,
            MethodThreeConfiguration(
                sample_size=cast(Literal[5, 10, 15, 20], sample_size),
                competition_scope=competition_scope,
                season_scope=season_scope,
                previous_season_id=previous_season_id,
                metric=metric,
                comparator=comparator,
                achievement_target=achievement_target,
            ),
        )
    )
