"""Controlled replay using only an APP-007 canonical input snapshot."""

from __future__ import annotations

import json
from dataclasses import is_dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Protocol, cast
from uuid import uuid4

from lvfi_pricing.core.numeric import NumericPolicy
from lvfi_pricing.models.method_one import (
    DISTRIBUTION_VERSION,
    METHOD_ONE_CANONICAL_SCHEMA_VERSION,
    MethodOneConfiguration,
    MethodOneFinalResult,
    MethodOneMultiplierCandidate,
    MethodOneMultiplierResolution,
    MethodOneRecencyConfiguration,
    MethodOneRequest,
    MethodOneSeriesReference,
    MethodOneWeightConfiguration,
)
from lvfi_pricing.models.samples import (
    DataSnapshotMetadata,
    MatchIdentity,
    MatchObservation,
    ObservationValue,
    SampleCounts,
    SampleDefinition,
    SampleExclusion,
    SampleFilter,
    SampleQuality,
    SampleSnapshot,
)

from lvfi_api.application.method_one_execution import MethodOnePublicFacade
from lvfi_api.application.pricing_execution_persistence import (
    PricingExecutionRepository,
)
from lvfi_api.domain.errors import ResourceNotFoundError
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.pricing_execution_reproductions import (
    PricingExecutionReproduction,
    PricingExecutionReproductionDraft,
    PricingExecutionReproductionOutcome,
)
from lvfi_api.domain.pricing_executions import PricingExecution, PricingExecutionStatus
from lvfi_api.infrastructure.pricing_engine import public_method_one

_PRICING_ENGINE_VERSION = "1.0.1"
_METHOD_ONE_VERSION = "1.0.0"
_CURRENT = (_PRICING_ENGINE_VERSION, DISTRIBUTION_VERSION, _METHOD_ONE_VERSION, 1)
_TYPE_REGISTRY = {
    value.__name__: value
    for value in (
        NumericPolicy,
        MethodOneConfiguration,
        MethodOneMultiplierCandidate,
        MethodOneMultiplierResolution,
        MethodOneRecencyConfiguration,
        MethodOneRequest,
        MethodOneSeriesReference,
        MethodOneWeightConfiguration,
        DataSnapshotMetadata,
        MatchIdentity,
        MatchObservation,
        ObservationValue,
        SampleCounts,
        SampleDefinition,
        SampleExclusion,
        SampleFilter,
        SampleQuality,
        SampleSnapshot,
    )
}
_ENUM_TYPES = tuple(
    value
    for value in (
        *vars(__import__("lvfi_pricing.models.method_one", fromlist=["*"])).values(),
        *vars(__import__("lvfi_pricing.models.samples", fromlist=["*"])).values(),
    )
    if isinstance(value, type) and issubclass(value, Enum)
)
_ENUM_REGISTRY = {value.__name__: value for value in _ENUM_TYPES}


class PricingExecutionReproductionRepository(Protocol):
    async def create(
        self, draft: PricingExecutionReproductionDraft
    ) -> PricingExecutionReproduction: ...

    async def get(
        self, reproduction_id: str
    ) -> PricingExecutionReproduction | None: ...

    async def list_by_execution(
        self, execution_id: str, page: int, page_size: int
    ) -> Page[PricingExecutionReproduction]: ...


class PricingExecutionReproductionService:
    """Append a reproducible outcome without reading samples or mutating APP-007."""

    def __init__(
        self,
        executions: PricingExecutionRepository,
        reproductions: PricingExecutionReproductionRepository,
        engine: MethodOnePublicFacade = public_method_one,
    ) -> None:
        self._executions = executions
        self._reproductions = reproductions
        self._engine = engine

    async def reproduce(
        self, execution_id: str, correlation_id: str
    ) -> PricingExecutionReproduction:
        original = await self._executions.get(execution_id)
        if original is None:
            raise ResourceNotFoundError("pricing execution")
        if not _reproducible(original):
            return await self._append(
                original,
                correlation_id,
                PricingExecutionReproductionOutcome.BLOCKED,
                failure_code="original_execution_not_reproducible",
            )
        if _versions(original) != _CURRENT:
            return await self._append(
                original,
                correlation_id,
                PricingExecutionReproductionOutcome.INCOMPATIBLE_VERSION,
                differences=_version_differences(original),
                failure_code="incompatible_version",
            )
        try:
            request = decode_canonical_request(
                cast(dict[str, Any], original.canonical_input)
            )
            payload = self._engine.canonical_bytes(request)
            fingerprint = self._engine.sha256(request)
            if not isinstance(payload, bytes) or not isinstance(fingerprint, str):
                raise ValueError
        except Exception:
            return await self._append(
                original,
                correlation_id,
                PricingExecutionReproductionOutcome.BLOCKED,
                failure_code="canonical_input_invalid",
            )
        if fingerprint != original.input_fingerprint:
            return await self._append(
                original,
                correlation_id,
                PricingExecutionReproductionOutcome.MISMATCH,
                reproduced_input_fingerprint=fingerprint,
                differences=_differences(
                    "canonical_input", original.canonical_input, json.loads(payload)
                ),
                failure_code="input_fingerprint_mismatch",
            )
        try:
            result = self._engine.run(request)
            if not isinstance(result, MethodOneFinalResult):
                raise ValueError
            reproduced = self._engine.serialize(result)
            result_bytes = getattr(reproduced, "canonical_bytes", None)
            result_fingerprint = getattr(reproduced, "content_hash", None)
            if not isinstance(result_bytes, bytes) or not isinstance(
                result_fingerprint, str
            ):
                raise ValueError
        except Exception:
            return await self._append(
                original,
                correlation_id,
                PricingExecutionReproductionOutcome.TECHNICAL_FAILURE,
                reproduced_input_fingerprint=fingerprint,
                failure_code="method_one_reproduction_failed",
            )
        reproduced_result = json.loads(result_bytes)
        exact = result_fingerprint == original.result_fingerprint
        return await self._append(
            original,
            correlation_id,
            (
                PricingExecutionReproductionOutcome.EXACT_MATCH
                if exact
                else PricingExecutionReproductionOutcome.MISMATCH
            ),
            reproduced_input_fingerprint=fingerprint,
            reproduced_result_fingerprint=result_fingerprint,
            differences=(
                ()
                if exact
                else _differences(
                    "canonical_result", original.canonical_result, reproduced_result
                )
            ),
            failure_code=None if exact else "result_fingerprint_mismatch",
        )

    async def get(self, reproduction_id: str) -> PricingExecutionReproduction:
        reproduction = await self._reproductions.get(reproduction_id)
        if reproduction is None:
            raise ResourceNotFoundError("pricing reproduction")
        return reproduction

    async def list_by_execution(
        self, execution_id: str, page: int, page_size: int
    ) -> Page[PricingExecutionReproduction]:
        if await self._executions.get(execution_id) is None:
            raise ResourceNotFoundError("pricing execution")
        return await self._reproductions.list_by_execution(
            execution_id, page, page_size
        )

    async def _append(
        self,
        original: PricingExecution,
        correlation_id: str,
        outcome: PricingExecutionReproductionOutcome,
        reproduced_input_fingerprint: str | None = None,
        reproduced_result_fingerprint: str | None = None,
        differences: tuple[dict[str, Any], ...] = (),
        failure_code: str | None = None,
    ) -> PricingExecutionReproduction:
        return await self._reproductions.create(
            PricingExecutionReproductionDraft(
                reproduction_id=str(uuid4()),
                execution_id=original.execution_id,
                outcome=outcome,
                finalized_at=datetime.now(UTC),
                correlation_id=correlation_id,
                original_input_fingerprint=original.input_fingerprint,
                reproduced_input_fingerprint=reproduced_input_fingerprint,
                original_result_fingerprint=original.result_fingerprint,
                reproduced_result_fingerprint=reproduced_result_fingerprint,
                original_pricing_engine_version=original.pricing_engine_version,
                current_pricing_engine_version=_PRICING_ENGINE_VERSION,
                original_distribution_version=original.distribution_version,
                current_distribution_version=DISTRIBUTION_VERSION,
                original_method_one_version=original.method_one_version,
                current_method_one_version=_METHOD_ONE_VERSION,
                original_schema_version=original.schema_version,
                current_schema_version=METHOD_ONE_CANONICAL_SCHEMA_VERSION,
                differences=differences,
                failure_code=failure_code,
            )
        )


def decode_canonical_request(value: dict[str, Any]) -> MethodOneRequest:
    """Decode only the current, explicit canonical schema; never coerce old data."""
    decoded = _decode(value)
    if not isinstance(decoded, MethodOneRequest):
        raise ValueError("canonical root is not a request")
    return decoded


def _decode(value: Any) -> Any:
    if not isinstance(value, dict):
        if isinstance(value, list):
            return [_decode(item) for item in value]
        return value
    kind = value.get("type")
    if kind == "Float" and set(value) == {"type", "value"}:
        return float.fromhex(cast(str, value["value"]))
    if kind == "DateTime" and set(value) == {"type", "value"}:
        parsed = datetime.fromisoformat(cast(str, value["value"]))
        if parsed.tzinfo is None:
            raise ValueError("naive datetime")
        return parsed
    if kind == "Tuple" and set(value) == {"type", "items"}:
        return tuple(_decode(item) for item in cast(list[Any], value["items"]))
    if kind == "Mapping" and set(value) == {"type", "items"}:
        return {
            str(_decode(key)): _decode(item)
            for key, item in cast(list[list[Any]], value["items"])
        }
    if kind == "Enum" and set(value) == {"type", "enum", "value"}:
        enum = _ENUM_REGISTRY.get(cast(str, value["enum"]))
        if enum is None:
            raise ValueError("unknown enum")
        return enum(cast(str, value["value"]))
    fields = value.get("fields")
    target = _TYPE_REGISTRY.get(cast(str, kind)) if isinstance(kind, str) else None
    if (
        target is None
        or not isinstance(fields, dict)
        or value.get("schema_version") != 1
    ):
        raise ValueError("unsupported canonical value")
    decoded = {name: _decode(item) for name, item in fields.items()}
    instance = target(**decoded)
    if not is_dataclass(instance):
        raise ValueError("unsupported canonical instance")
    return instance


def _reproducible(value: PricingExecution) -> bool:
    return (
        value.status is PricingExecutionStatus.COMPLETED
        and value.canonical_input is not None
        and value.canonical_result is not None
        and value.input_fingerprint is not None
        and value.result_fingerprint is not None
    )


def _versions(value: PricingExecution) -> tuple[str, str, str, int]:
    return (
        value.pricing_engine_version,
        value.distribution_version,
        value.method_one_version,
        value.schema_version,
    )


def _version_differences(value: PricingExecution) -> tuple[dict[str, Any], ...]:
    names = (
        "pricing_engine_version",
        "distribution_version",
        "method_one_version",
        "schema_version",
    )
    return tuple(
        {"path": name, "original": previous, "reproduced": current}
        for name, previous, current in zip(
            names, _versions(value), _CURRENT, strict=True
        )
        if previous != current
    )


def _differences(
    path: str, original: Any, reproduced: Any
) -> tuple[dict[str, Any], ...]:
    if isinstance(original, dict) and isinstance(reproduced, dict):
        return tuple(
            item
            for key in sorted(set(original) | set(reproduced))
            for item in _differences(
                f"{path}.{key}", original.get(key), reproduced.get(key)
            )
        )
    if isinstance(original, list) and isinstance(reproduced, list):
        return tuple(
            item
            for index in range(max(len(original), len(reproduced)))
            for item in _differences(
                f"{path}[{index}]",
                original[index] if index < len(original) else None,
                reproduced[index] if index < len(reproduced) else None,
            )
        )
    return (
        ()
        if original == reproduced
        else ({"path": path, "original": original, "reproduced": reproduced},)
    )
