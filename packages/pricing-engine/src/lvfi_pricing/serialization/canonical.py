"""Pure canonical representation for approved public Pricing Engine contracts."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from types import MappingProxyType

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy
from lvfi_pricing.distributions import (
    GoalDifferenceDistribution,
    PoissonDistribution,
    ScoreProbabilityMatrix,
)
from lvfi_pricing.domain import (
    FairOdds,
    Multiplier,
    PoissonRate,
    Probability,
    QuarterLine,
    Weight,
)
from lvfi_pricing.engine.contracts import (
    AsianHandicapMainLineRequest,
    AsianHandicapRequest,
    AsianTotalMainLineRequest,
    AsianTotalRequest,
    BothTeamsToScoreRequest,
    DoubleChanceRequest,
    PricingEngineMetadata,
    PricingRequest,
    PricingResult,
    ThreeWayResultRequest,
    TotalGoalsRequest,
)
from lvfi_pricing.markets import (
    AsianMainLine,
    AsianMarketPrice,
    HalfGoalLine,
    MarketPrices,
)
from lvfi_pricing.markets.asian_contracts import (
    AsianSettlementProbabilities,
    ExpectedAsianSettlementProfile,
)
from lvfi_pricing.markets.contracts import PricedSelection
from lvfi_pricing.settlement.contracts import (
    AsianLineComponent,
    AsianLineSplit,
    AsianSettlementProfile,
    AsianSettlementResult,
)

from .contracts import CanonicalValue

CANONICAL_SCHEMA_VERSION = 1

_SUPPORTED_DATACLASSES = (
    Probability,
    FairOdds,
    PoissonRate,
    Weight,
    Multiplier,
    QuarterLine,
    NumericPolicy,
    CalculationError,
    CalculationWarning,
    PoissonDistribution,
    GoalDifferenceDistribution,
    ScoreProbabilityMatrix,
    HalfGoalLine,
    PricedSelection,
    MarketPrices,
    AsianSettlementProbabilities,
    ExpectedAsianSettlementProfile,
    AsianMarketPrice,
    AsianMainLine,
    AsianLineComponent,
    AsianLineSplit,
    AsianSettlementProfile,
    AsianSettlementResult,
    ThreeWayResultRequest,
    DoubleChanceRequest,
    BothTeamsToScoreRequest,
    TotalGoalsRequest,
    AsianHandicapRequest,
    AsianTotalRequest,
    AsianHandicapMainLineRequest,
    AsianTotalMainLineRequest,
    PricingRequest,
    PricingEngineMetadata,
    PricingResult,
)

# A registry maps each supported dataclass type to the canonical envelope
# schema version that owns its serialized form. ``to_canonical_value`` keeps the
# historical Pricing Engine surface unchanged by delegating to ``PRICING_SCHEMA``;
# other serializers (for example Method One) reuse the same deterministic rules
# through ``canonicalize`` with their own, explicit registry.
SchemaRegistry = Mapping[type, int]

PRICING_SCHEMA: SchemaRegistry = MappingProxyType(
    {dataclass: CANONICAL_SCHEMA_VERSION for dataclass in _SUPPORTED_DATACLASSES}
)


def _error(code: ErrorCode, message: str, field: str = "value") -> CalculationError:
    return CalculationError(code, message, field)


def _mapping(values: Mapping[str, CanonicalValue]) -> Mapping[str, CanonicalValue]:
    return MappingProxyType(dict(sorted(values.items())))


def _canonical(
    value: object, schema: SchemaRegistry
) -> CanonicalValue | CalculationError:
    if isinstance(value, Enum):
        return _mapping(
            {
                "enum": type(value).__name__,
                "type": "Enum",
                "value": str(value.value),
            }
        )
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return _error(ErrorCode.INVALID_NUMBER, "canonical floats must be finite")
        normalized = 0.0 if value == 0.0 else value
        return _mapping({"type": "Float", "value": normalized.hex()})
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            return _error(
                ErrorCode.SERIALIZATION_ERROR, "canonical datetime must be aware"
            )
        return _mapping(
            {"type": "DateTime", "value": value.astimezone(UTC).isoformat()}
        )
    if isinstance(value, tuple):
        tuple_items: list[CanonicalValue] = []
        for item in value:
            canonical_item = _canonical(item, schema)
            if isinstance(canonical_item, CalculationError):
                return canonical_item
            tuple_items.append(canonical_item)
        return _mapping({"items": tuple(tuple_items), "type": "Tuple"})
    if isinstance(value, MappingProxyType):
        mapping_items: dict[str, CanonicalValue] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                return _error(
                    ErrorCode.SERIALIZATION_ERROR, "mapping keys must be strings"
                )
            canonical_item = _canonical(value[key], schema)
            if isinstance(canonical_item, CalculationError):
                return canonical_item
            mapping_items[key] = canonical_item
        return _mapping({"entries": _mapping(mapping_items), "type": "Mapping"})
    if is_dataclass(value):
        schema_version = schema.get(type(value))
        if schema_version is not None:
            values: dict[str, CanonicalValue] = {}
            for field in fields(value):
                canonical_item = _canonical(getattr(value, field.name), schema)
                if isinstance(canonical_item, CalculationError):
                    return canonical_item
                values[field.name] = canonical_item
            return _mapping(
                {
                    "fields": _mapping(values),
                    "schema_version": schema_version,
                    "type": type(value).__name__,
                }
            )
    return _error(
        ErrorCode.SERIALIZATION_ERROR,
        f"unsupported canonical type: {type(value).__name__}",
    )


def to_canonical_value(value: object) -> CanonicalValue | CalculationError:
    """Return the immutable canonical representation, or a typed domain error."""
    return _canonical(value, PRICING_SCHEMA)


def canonicalize(
    value: object, schema: SchemaRegistry
) -> CanonicalValue | CalculationError:
    """Canonicalize ``value`` using an explicit registry of supported dataclasses.

    The registry maps each supported dataclass type to the canonical envelope
    schema version that produced its serialized form, letting downstream methods
    reuse the same deterministic rules as the Pricing Engine without duplicating
    them and without coupling to the Pricing Engine schema version.
    """
    return _canonical(value, schema)
