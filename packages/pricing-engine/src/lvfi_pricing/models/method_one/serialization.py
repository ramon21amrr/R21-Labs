"""Canonical serialization, deterministic bytes and SHA-256 for Method One.

Method One owns a canonical representation that reuses the Pricing Engine
serialization primitives (sorted UTF-8 JSON, ``float.hex()``, typed tuple and
mapping envelopes, enum mapping) while keeping its own explicit schema version
and registry. Pricing Engine contracts that appear nested inside a Method One
result keep the Pricing Engine canonical schema version, so the same nested
``PricingResult`` always produces identical bytes whether it is serialized
directly or as part of a Method One result.

Canonical rules (shared with the Pricing Engine):

* compact UTF-8 JSON, ``separators=(",", ":")``, ``sort_keys=True``;
* no whitespace, no BOM, no trailing newline;
* ``bool``/``int``/``str``/``None`` encoded verbatim, ``bool`` before ``int``;
* finite ``float`` encoded via ``float.hex()`` (binary64 exact, locale-free);
* timezone-aware ``datetime`` normalized to UTC ISO 8601 (``+00:00``);
* ``Enum`` encoded as ``{"enum", "type", "value"}``;
* ``tuple`` and ``Mapping`` wrapped in explicit ``{"type", ...}`` envelopes;
* dataclasses emitted as ``{"fields", "schema_version", "type"}`` with fields
  sorted by name and nested values canonicalized recursively.

The serialization never changes Method One mathematics, contracts, schemas or
frozen values: it only reads existing immutable state and hashes it.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import cast

from lvfi_pricing.core.errors import CalculationError, ErrorCode
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
from lvfi_pricing.serialization import (
    PRICING_SCHEMA,
    CanonicalValue,
    SchemaRegistry,
    canonical_json_bytes,
    canonicalize,
)

from .averages import MethodOneContextualAverages
from .base_rates import (
    MethodOneBaseRateExplanation,
    MethodOneBaseRateResult,
    MethodOneParticipantBaseRateExplanation,
    MethodOneWeightedComponent,
)
from .contracts import (
    DISTRIBUTION_VERSION,
    METHOD_ONE_VERSION,
    ContextualAverage,
    ContextualAverageEvidence,
    MethodOneConfiguration,
    MethodOneMetadata,
    MethodOneMultiplierCandidate,
    MethodOneMultiplierResolution,
    MethodOneRateExplanation,
    MethodOneRecencyConfiguration,
    MethodOneRequest,
    MethodOneResult,
    MethodOneSeriesReference,
    MethodOneWeightConfiguration,
)
from .multipliers import (
    MethodOneAdjustedRateExplanation,
    MethodOneAdjustedRateResult,
    MethodOneMultiplierApplicationStep,
    MethodOneMultiplierCatalog,
    MethodOneMultiplierCatalogEntry,
)
from .orchestration import MethodOneFinalExplanation, MethodOneFinalResult
from .pricing import MethodOnePricingExplanation, MethodOnePricingResult

METHOD_ONE_CANONICAL_SCHEMA_VERSION = 1
HASH_ALGORITHM = "sha256"

# Method One and shared sample contracts are serialized under the Method One
# canonical schema version. Pricing Engine contracts that are nested inside a
# Method One result keep their own canonical schema version (reused, not
# duplicated) through ``PRICING_SCHEMA``. The two groups are disjoint, so the
# merge is unambiguous.
_METHOD_ONE_TYPES: tuple[type, ...] = (
    MethodOneWeightConfiguration,
    MethodOneRecencyConfiguration,
    MethodOneMultiplierCandidate,
    MethodOneMultiplierResolution,
    MethodOneConfiguration,
    MethodOneSeriesReference,
    MethodOneRequest,
    ContextualAverage,
    ContextualAverageEvidence,
    MethodOneRateExplanation,
    MethodOneMetadata,
    MethodOneResult,
    MethodOneContextualAverages,
    MethodOneWeightedComponent,
    MethodOneParticipantBaseRateExplanation,
    MethodOneBaseRateExplanation,
    MethodOneBaseRateResult,
    MethodOneMultiplierCatalogEntry,
    MethodOneMultiplierCatalog,
    MethodOneMultiplierApplicationStep,
    MethodOneAdjustedRateExplanation,
    MethodOneAdjustedRateResult,
    MethodOnePricingExplanation,
    MethodOnePricingResult,
    MethodOneFinalExplanation,
    MethodOneFinalResult,
    MatchIdentity,
    MatchObservation,
    ObservationValue,
    SampleFilter,
    SampleDefinition,
    SampleExclusion,
    DataSnapshotMetadata,
    SampleCounts,
    SampleQuality,
    SampleSnapshot,
)

_METHOD_ONE_SCHEMA: SchemaRegistry = MappingProxyType(
    {
        **{
            dataclass_type: METHOD_ONE_CANONICAL_SCHEMA_VERSION
            for dataclass_type in _METHOD_ONE_TYPES
        },
        **dict(PRICING_SCHEMA),
    }
)


def method_one_canonical_value(value: object) -> CanonicalValue | CalculationError:
    """Return the immutable canonical representation of a Method One value."""
    return canonicalize(value, _METHOD_ONE_SCHEMA)


def method_one_canonical_bytes(value: object) -> bytes | CalculationError:
    """Encode a Method One value as compact, sorted UTF-8 canonical JSON."""
    canonical_value = method_one_canonical_value(value)
    if isinstance(canonical_value, CalculationError):
        return canonical_value
    return canonical_json_bytes(canonical_value)


def method_one_sha256(value: object) -> str | CalculationError:
    """Return the lowercase SHA-256 digest of the canonical bytes of ``value``."""
    payload = method_one_canonical_bytes(value)
    if isinstance(payload, CalculationError):
        return payload
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class MethodOnePayload:
    """Versioned, immutable content identity for a Method One final result."""

    schema_version: int
    root_type: str
    canonical_value: CanonicalValue
    canonical_bytes: bytes
    content_hash: str
    method_version: str
    package_version: str
    hash_algorithm: str = HASH_ALGORITHM


def _final_result_envelope(
    result_value: CanonicalValue,
) -> tuple[MappingProxyType[str, CanonicalValue], bytes, str]:
    content: MappingProxyType[str, CanonicalValue] = MappingProxyType(
        {
            "content": result_value,
            "method_version": METHOD_ONE_VERSION,
            "package_version": DISTRIBUTION_VERSION,
            "root_type": "MethodOneFinalResult",
            "schema_version": METHOD_ONE_CANONICAL_SCHEMA_VERSION,
        }
    )
    content_bytes = canonical_json_bytes(content)
    return content, content_bytes, hashlib.sha256(content_bytes).hexdigest()


def serialize_method_one_final_result(
    result: MethodOneFinalResult,
) -> MethodOnePayload | CalculationError:
    """Build the versioned final-result envelope; ``content_hash`` is over content."""
    if not isinstance(result, MethodOneFinalResult):
        return CalculationError(
            ErrorCode.CONFIGURATION_ERROR,
            "result must be a MethodOneFinalResult",
            "result",
        )
    result_value = method_one_canonical_value(result)
    if isinstance(result_value, CalculationError):
        return result_value
    content, content_bytes, content_hash = _final_result_envelope(result_value)
    return MethodOnePayload(
        METHOD_ONE_CANONICAL_SCHEMA_VERSION,
        "MethodOneFinalResult",
        cast(CanonicalValue, content),
        content_bytes,
        content_hash,
        METHOD_ONE_VERSION,
        DISTRIBUTION_VERSION,
    )


@dataclass(frozen=True, slots=True)
class MethodOneIdentity:
    """Stable, comparable identity isolating input, configuration and result.

    ``input_hash`` covers the request and the multiplier candidates (the full
    input including samples and configuration); ``configuration_hash`` isolates
    the :class:`MethodOneConfiguration` so the same configuration can be
    recognized across different samples; ``result_hash`` is the content hash of
    the versioned final-result envelope. Two identities are equal when every
    hash and version match.
    """

    input_hash: str
    configuration_hash: str
    result_hash: str
    schema_version: int
    method_version: str
    package_version: str
    hash_algorithm: str = HASH_ALGORITHM


def method_one_identity(
    result: MethodOneFinalResult,
) -> MethodOneIdentity | CalculationError:
    """Build the comparable input/configuration/result identity of ``result``."""
    if not isinstance(result, MethodOneFinalResult):
        return CalculationError(
            ErrorCode.CONFIGURATION_ERROR,
            "result must be a MethodOneFinalResult",
            "result",
        )
    configuration = method_one_sha256(result.request.configuration)
    if isinstance(configuration, CalculationError):
        return configuration
    input_digest = method_one_sha256((result.request, result.multiplier_candidates))
    if isinstance(input_digest, CalculationError):
        return input_digest
    payload = serialize_method_one_final_result(result)
    if isinstance(payload, CalculationError):
        return payload
    return MethodOneIdentity(
        input_digest,
        configuration,
        payload.content_hash,
        METHOD_ONE_CANONICAL_SCHEMA_VERSION,
        METHOD_ONE_VERSION,
        DISTRIBUTION_VERSION,
    )


__all__ = (
    "HASH_ALGORITHM",
    "METHOD_ONE_CANONICAL_SCHEMA_VERSION",
    "MethodOneIdentity",
    "MethodOnePayload",
    "method_one_canonical_bytes",
    "method_one_canonical_value",
    "method_one_identity",
    "method_one_sha256",
    "serialize_method_one_final_result",
)
