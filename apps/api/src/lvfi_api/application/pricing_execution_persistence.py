"""Transactional orchestration for immutable Method One execution persistence."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from lvfi_pricing.models.method_one import (
    DISTRIBUTION_VERSION,
    METHOD_ONE_CANONICAL_SCHEMA_VERSION,
    MethodOneConfiguration,
    MethodOneFinalResult,
    MethodOnePayload,
    MethodOneRequest,
)

from lvfi_api.application.method_one_execution import (
    MethodOnePublicFacade,
    MethodOneSampleProvider,
    build_method_one_request,
)
from lvfi_api.domain.errors import (
    MethodOneEngineError,
    MethodOneSampleIncompleteError,
    MethodOneSampleInvalidError,
    ResourceNotFoundError,
)
from lvfi_api.domain.historical_queries import MethodOneSample, Page
from lvfi_api.domain.pricing_executions import (
    PricingExecution,
    PricingExecutionDraft,
    PricingExecutionStatus,
)
from lvfi_api.infrastructure.pricing_engine import public_method_one

_CONFIGURATION_ID = "lvfi-app-006-default"
_PRICING_ENGINE_VERSION = "1.0.1"
_FAILURE_CODE = "method_one_execution_failed"
_BLOCKED_CODE = "method_one_sample_incomplete"


class PricingExecutionRepository(Protocol):
    """Append-only storage operations required by the execution application flow."""

    async def get(self, execution_id: str) -> PricingExecution | None: ...

    async def get_by_idempotency_key(
        self, match_id: int, idempotency_key: str
    ) -> PricingExecution | None: ...

    async def create(self, draft: PricingExecutionDraft) -> PricingExecution: ...

    async def list_by_match(
        self, match_id: int, page: int, page_size: int
    ) -> Page[PricingExecution] | None: ...


class PricingExecutionPersistenceService:
    """Execute through the public facade once, then atomically append its outcome."""

    def __init__(
        self,
        samples: MethodOneSampleProvider,
        repository: PricingExecutionRepository,
        engine: MethodOnePublicFacade = public_method_one,
    ) -> None:
        self._samples = samples
        self._repository = repository
        self._engine = engine

    async def execute(
        self, match_id: int, correlation_id: str, idempotency_key: str | None
    ) -> PricingExecution:
        if idempotency_key is not None:
            existing = await self._repository.get_by_idempotency_key(
                match_id, idempotency_key
            )
            if existing is not None:
                return existing
        sample = await self._samples.get_sample(match_id)
        common = _common_values(sample)
        sample_fingerprint = _sample_fingerprint(sample)
        try:
            request = build_method_one_request(sample, self._engine)
        except MethodOneSampleIncompleteError:
            return await self._repository.create(
                _draft(
                    match_id,
                    PricingExecutionStatus.BLOCKED_SAMPLE_INCOMPLETE,
                    correlation_id,
                    idempotency_key,
                    sample_fingerprint,
                    common,
                    failure_code=_BLOCKED_CODE,
                )
            )
        except MethodOneSampleInvalidError:
            return await self._repository.create(
                _draft(
                    match_id,
                    PricingExecutionStatus.TECHNICAL_FAILURE,
                    correlation_id,
                    idempotency_key,
                    sample_fingerprint,
                    common,
                    failure_code=_FAILURE_CODE,
                )
            )
        input_payload, input_fingerprint = _canonical_input(request, self._engine)
        try:
            result = self._engine.run(request)
            if not isinstance(result, MethodOneFinalResult):
                raise MethodOneEngineError()
            payload = self._engine.serialize(result)
            if not isinstance(payload, MethodOnePayload):
                raise MethodOneEngineError()
        except Exception:
            return await self._repository.create(
                _draft(
                    match_id,
                    PricingExecutionStatus.TECHNICAL_FAILURE,
                    correlation_id,
                    idempotency_key,
                    sample_fingerprint,
                    common,
                    input_fingerprint,
                    input_payload,
                    failure_code=_FAILURE_CODE,
                )
            )
        return await self._repository.create(
            _draft(
                match_id,
                PricingExecutionStatus.COMPLETED,
                correlation_id,
                idempotency_key,
                sample_fingerprint,
                common,
                input_fingerprint,
                input_payload,
                result_fingerprint=payload.content_hash,
                canonical_result=payload.canonical_bytes.decode("utf-8"),
            )
        )

    async def get(self, execution_id: str) -> PricingExecution:
        execution = await self._repository.get(execution_id)
        if execution is None:
            raise ResourceNotFoundError("pricing execution")
        return execution

    async def list_by_match(
        self, match_id: int, page: int, page_size: int
    ) -> Page[PricingExecution]:
        executions = await self._repository.list_by_match(match_id, page, page_size)
        if executions is None:
            raise ResourceNotFoundError("match")
        return executions


def _canonical_input(
    request: MethodOneRequest, engine: MethodOnePublicFacade
) -> tuple[str, str]:
    canonical = engine.canonical_bytes(request)
    fingerprint = engine.sha256(request)
    if not isinstance(canonical, bytes) or not isinstance(fingerprint, str):
        raise MethodOneEngineError()
    return canonical.decode("utf-8"), fingerprint


def _common_values(sample: MethodOneSample) -> dict[str, Any]:
    configuration = MethodOneConfiguration(_CONFIGURATION_ID)
    return {
        "pricing_engine_version": _PRICING_ENGINE_VERSION,
        "distribution_version": DISTRIBUTION_VERSION,
        "method_one_version": configuration.formula_version,
        "schema_version": METHOD_ONE_CANONICAL_SCHEMA_VERSION,
        "public_parameters": {
            "requested_count": sample.parameters.requested_count,
            "competition_id": sample.parameters.competition_id,
            "season_id": sample.parameters.season_id,
            "include_previous_season": sample.parameters.include_previous_season,
            "ordering": sample.parameters.ordering,
            "statistic_periods": list(sample.parameters.statistic_periods),
            "configuration_id": _CONFIGURATION_ID,
        },
    }


def _sample_fingerprint(sample: MethodOneSample) -> str:
    """Hash a minimal, canonical selection projection without source provenance."""
    payload = {
        "match_id": sample.target_match.id,
        "parameters": {
            "requested_count": sample.parameters.requested_count,
            "competition_id": sample.parameters.competition_id,
            "season_id": sample.parameters.season_id,
            "include_previous_season": sample.parameters.include_previous_season,
            "ordering": sample.parameters.ordering,
            "statistic_periods": list(sample.parameters.statistic_periods),
        },
        "home": _sample_series(sample.home_sample.matches),
        "away": _sample_series(sample.away_sample.matches),
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sample_series(items: tuple[Any, ...]) -> list[dict[str, Any]]:
    return [
        {
            "match_id": item.match.id,
            "played_on": item.match.played_on.isoformat(),
            "home_goals": item.statistics.home.full_match.goals,
            "away_goals": item.statistics.away.full_match.goals,
        }
        for item in items
    ]


def _draft(
    match_id: int,
    status: PricingExecutionStatus,
    correlation_id: str,
    idempotency_key: str | None,
    sample_fingerprint: str,
    common: dict[str, Any],
    input_fingerprint: str | None = None,
    canonical_input: str | None = None,
    result_fingerprint: str | None = None,
    canonical_result: str | None = None,
    failure_code: str | None = None,
) -> PricingExecutionDraft:
    return PricingExecutionDraft(
        execution_id=str(uuid4()),
        match_id=match_id,
        status=status,
        finalized_at=datetime.now(UTC),
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        sample_fingerprint=sample_fingerprint,
        input_fingerprint=input_fingerprint,
        result_fingerprint=result_fingerprint,
        pricing_engine_version=common["pricing_engine_version"],
        distribution_version=common["distribution_version"],
        method_one_version=common["method_one_version"],
        schema_version=common["schema_version"],
        public_parameters=common["public_parameters"],
        canonical_input=canonical_input,
        canonical_result=canonical_result,
        failure_code=failure_code,
    )
