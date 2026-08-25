"""Append-only external references resolved against immutable ENG-006 snapshots."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from lvfi_api.domain.errors import MarketReferenceValidationError, ResourceNotFoundError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.market_pricings import MarketPricing
from lvfi_api.domain.market_reference_observations import (
    MarketReferenceObservation,
    MarketReferenceObservationDraft,
    ModelReferenceComparison,
)


class MarketReferenceRepository(Protocol):
    async def get_snapshot(self, market_pricing_id: str) -> MarketPricing | None: ...
    async def get(self, observation_id: str) -> MarketReferenceObservation | None: ...
    async def get_by_idempotency_key(
        self, match_id: int, idempotency_key: str
    ) -> MarketReferenceObservation | None: ...
    async def create(
        self, draft: MarketReferenceObservationDraft
    ) -> MarketReferenceObservation: ...
    async def list_by_match_snapshot(
        self, match_id: int, market_pricing_id: str, page: int, page_size: int
    ) -> Page[MarketReferenceObservation] | None: ...


class MarketReferenceObservationService:
    """Validate selection/line semantics against the stored theoretical snapshot."""

    def __init__(self, repository: MarketReferenceRepository) -> None:
        self._repository = repository

    async def create(
        self,
        *,
        match_id: int,
        market_pricing_id: str,
        market_code: str,
        selection: str,
        model_line_quarters: int | None,
        reference_line_quarters: int | None,
        reference_value: float,
        observed_at: datetime,
        correlation_id: str,
        idempotency_key: str | None,
    ) -> MarketReferenceObservation:
        if idempotency_key is not None:
            existing = await self._repository.get_by_idempotency_key(
                match_id, idempotency_key
            )
            if existing is not None:
                return existing
        snapshot = await self._repository.get_snapshot(market_pricing_id)
        if snapshot is None:
            raise ResourceNotFoundError("market pricing")
        if snapshot.match_id != match_id:
            raise MarketReferenceValidationError()
        quote = _quote(snapshot, market_code, selection, model_line_quarters)
        if quote is None or not _valid_input(
            quote[1], reference_line_quarters, reference_value, observed_at
        ):
            raise MarketReferenceValidationError()
        return await self._repository.create(
            MarketReferenceObservationDraft(
                observation_id=str(uuid4()),
                match_id=match_id,
                market_pricing_id=market_pricing_id,
                market_code=market_code,
                selection=selection,
                model_line_quarters=model_line_quarters,
                reference_line_quarters=reference_line_quarters,
                reference_value=reference_value,
                observed_at=observed_at.astimezone(UTC),
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        )

    async def get(self, observation_id: str) -> MarketReferenceObservation:
        value = await self._repository.get(observation_id)
        if value is None:
            raise ResourceNotFoundError("market reference observation")
        return value

    async def list_by_match_snapshot(
        self, match_id: int, market_pricing_id: str, page: int, page_size: int
    ) -> Page[MarketReferenceObservation]:
        value = await self._repository.list_by_match_snapshot(
            match_id, market_pricing_id, page, page_size
        )
        if value is None:
            raise ResourceNotFoundError("match")
        return value

    async def compare(self, observation_id: str) -> ModelReferenceComparison:
        observation = await self.get(observation_id)
        snapshot = await self._repository.get_snapshot(observation.market_pricing_id)
        if snapshot is None:  # defensive; the DB foreign key makes this unreachable.
            raise ResourceNotFoundError("market pricing")
        quote = _quote(
            snapshot,
            observation.market_code,
            observation.selection,
            observation.model_line_quarters,
        )
        if quote is None:
            raise MarketReferenceValidationError()
        return ModelReferenceComparison(
            observation=observation,
            model_value=quote[0],
            line_difference_quarters=(
                observation.reference_line_quarters - observation.model_line_quarters
                if observation.model_line_quarters is not None
                and observation.reference_line_quarters is not None
                else None
            ),
        )


def _valid_input(
    has_line: bool,
    reference_line_quarters: int | None,
    reference_value: float,
    observed_at: datetime,
) -> bool:
    return (
        not isinstance(reference_value, bool)
        and math.isfinite(reference_value)
        and reference_value > 0
        and observed_at.tzinfo is not None
        and (
            (has_line and reference_line_quarters is not None)
            or (not has_line and reference_line_quarters is None)
        )
    )


def _quote(
    snapshot: MarketPricing,
    market_code: str,
    selection: str,
    model_line_quarters: int | None,
) -> tuple[float, bool] | None:
    """Extract only the selected public Engine price; no pricing is recomputed."""
    requested = snapshot.canonical_input.get("markets")
    engine = snapshot.canonical_result.get("engine_result")
    if not isinstance(requested, list) or not isinstance(engine, dict):
        return None
    try:
        results = engine["content"]["fields"]["market_results"]["items"]
    except (KeyError, TypeError):
        return None
    if not isinstance(results, list) or len(results) != len(requested):
        return None
    for request, result in zip(requested, results, strict=True):
        if not isinstance(request, dict) or request.get("code") != market_code:
            continue
        request_selection = request.get("selection")
        asian_line = request.get("line_quarters")
        total_line = request.get("line_half_units")
        line = asian_line if isinstance(asian_line, int) else (
            total_line * 2 if isinstance(total_line, int) else None
        )
        if line != model_line_quarters:
            continue
        fields = result.get("fields") if isinstance(result, dict) else None
        if not isinstance(fields, dict):
            continue
        if request_selection is not None:
            if (
                request_selection != selection
                or fields.get("selection", {}).get("value") != selection
            ):
                continue
            value = _float_value(fields.get("fair_odds"))
            if value is not None:
                return value, line is not None
            continue
        selections = fields.get("selections", {}).get("items")
        if not isinstance(selections, list):
            continue
        for priced in selections:
            priced_fields = priced.get("fields") if isinstance(priced, dict) else None
            if (
                isinstance(priced_fields, dict)
                and priced_fields.get("selection", {}).get("value") == selection
            ):
                value = _float_value(priced_fields.get("fair_odds"))
                if value is not None:
                    return value, line is not None
    return None


def _float_value(value: Any) -> float | None:
    try:
        encoded = value["fields"]["value"]["value"]
        return float.fromhex(encoded) if isinstance(encoded, str) else None
    except (KeyError, TypeError, ValueError):
        return None
