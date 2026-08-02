"""Deterministic comparison of persisted Method One execution records only."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Number
from typing import Any, Protocol

from lvfi_api.domain.errors import InvalidQueryError, ResourceNotFoundError
from lvfi_api.domain.pricing_executions import PricingExecution


class PricingExecutionComparisonRepository(Protocol):
    """Read-only lookup required to compare two append-only records."""

    async def get_many(
        self, execution_ids: tuple[str, ...]
    ) -> tuple[PricingExecution, ...]: ...


@dataclass(frozen=True, slots=True)
class ComparisonField:
    """A stable, public-safe leaf comparison."""

    path: str
    left: Any
    right: Any
    equal: bool
    delta: int | float | None


@dataclass(frozen=True, slots=True)
class PricingExecutionComparison:
    """One read-only comparison, never a replay of the Pricing Engine."""

    left_execution_id: str
    right_execution_id: str
    match_id: int
    canonical_compatible: bool
    incompatibilities: tuple[str, ...]
    fields: tuple[ComparisonField, ...]


class PricingExecutionComparisonService:
    """Compare stored canonical material without an engine dependency."""

    def __init__(self, repository: PricingExecutionComparisonRepository) -> None:
        self._repository = repository

    async def compare(
        self, left_execution_id: str, right_execution_id: str
    ) -> PricingExecutionComparison:
        if left_execution_id == right_execution_id:
            raise InvalidQueryError("two distinct execution identifiers are required")
        records = await self._repository.get_many(
            (left_execution_id, right_execution_id)
        )
        found = {record.execution_id: record for record in records}
        left = found.get(left_execution_id)
        right = found.get(right_execution_id)
        if left is None or right is None:
            raise ResourceNotFoundError("pricing execution")
        if left.match_id != right.match_id:
            raise InvalidQueryError("executions must belong to the same match")
        incompatibilities = _incompatibilities(left, right)
        fields = tuple(
            sorted(
                _metadata_fields(left, right)
                + _canonical_fields(left, right, not incompatibilities),
                key=lambda field: field.path,
            )
        )
        return PricingExecutionComparison(
            left_execution_id=left.execution_id,
            right_execution_id=right.execution_id,
            match_id=left.match_id,
            canonical_compatible=not incompatibilities,
            incompatibilities=incompatibilities,
            fields=fields,
        )


def _incompatibilities(
    left: PricingExecution, right: PricingExecution
) -> tuple[str, ...]:
    values = (
        ("schema_version", left.schema_version, right.schema_version),
        (
            "pricing_engine_version",
            left.pricing_engine_version,
            right.pricing_engine_version,
        ),
        ("distribution_version", left.distribution_version, right.distribution_version),
        ("method_one_version", left.method_one_version, right.method_one_version),
    )
    return tuple(name for name, first, second in values if first != second)


def _metadata_fields(
    left: PricingExecution, right: PricingExecution
) -> list[ComparisonField]:
    values = (
        ("status", left.status.value, right.status.value),
        ("created_at", left.created_at.isoformat(), right.created_at.isoformat()),
        ("finalized_at", left.finalized_at.isoformat(), right.finalized_at.isoformat()),
        ("sample_fingerprint", left.sample_fingerprint, right.sample_fingerprint),
        ("input_fingerprint", left.input_fingerprint, right.input_fingerprint),
        ("result_fingerprint", left.result_fingerprint, right.result_fingerprint),
        (
            "pricing_engine_version",
            left.pricing_engine_version,
            right.pricing_engine_version,
        ),
        ("distribution_version", left.distribution_version, right.distribution_version),
        ("method_one_version", left.method_one_version, right.method_one_version),
        ("schema_version", left.schema_version, right.schema_version),
        ("failure_code", left.failure_code, right.failure_code),
    )
    return [_field(path, first, second, False) for path, first, second in values]


def _canonical_fields(
    left: PricingExecution, right: PricingExecution, compatible: bool
) -> list[ComparisonField]:
    fields: list[ComparisonField] = []
    for section, first, second in (
        ("public_parameters", left.public_parameters, right.public_parameters),
        ("canonical_input", left.canonical_input, right.canonical_input),
        ("canonical_result", left.canonical_result, right.canonical_result),
    ):
        fields.extend(
            _compare_values(
                section, first, second, compatible and section != "public_parameters"
            )
        )
    return fields


def _compare_values(
    path: str, left: Any, right: Any, deltas_allowed: bool
) -> list[ComparisonField]:
    if isinstance(left, dict) and isinstance(right, dict):
        return [
            field
            for key in sorted(set(left) | set(right))
            for field in _compare_values(
                f"{path}.{key}", left.get(key), right.get(key), deltas_allowed
            )
        ]
    if isinstance(left, list) and isinstance(right, list):
        return [
            field
            for index in range(max(len(left), len(right)))
            for field in _compare_values(
                f"{path}[{index}]",
                left[index] if index < len(left) else None,
                right[index] if index < len(right) else None,
                deltas_allowed,
            )
        ]
    return [_field(path, left, right, deltas_allowed)]


def _field(path: str, left: Any, right: Any, deltas_allowed: bool) -> ComparisonField:
    numeric = deltas_allowed and _is_numeric(left) and _is_numeric(right)
    return ComparisonField(
        path=path,
        left=left,
        right=right,
        equal=left == right,
        delta=right - left if numeric else None,
    )


def _is_numeric(value: Any) -> bool:
    return isinstance(value, Number) and not isinstance(value, bool)
