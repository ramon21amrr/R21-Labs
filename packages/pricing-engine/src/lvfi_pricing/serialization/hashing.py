"""Canonical UTF-8 encoding and deterministic SHA-256 content identities."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from types import MappingProxyType
from typing import cast

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.engine.contracts import PricingResult

from .canonical import CANONICAL_SCHEMA_VERSION, to_canonical_value
from .contracts import CanonicalPayload, CanonicalValue

_PACKAGE_VERSION = "0.11.0"


def _json_value(value: CanonicalValue) -> object:
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _encode(canonical_value: CanonicalValue) -> bytes:
    return json.dumps(
        _json_value(canonical_value),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_bytes(value: object) -> bytes | CalculationError:
    """Encode a supported value as compact, sorted UTF-8 canonical JSON."""
    canonical_value = to_canonical_value(value)
    if isinstance(canonical_value, CalculationError):
        return canonical_value
    return _encode(canonical_value)


def sha256_canonical(value: object) -> str | CalculationError:
    """Return the lowercase SHA-256 digest of canonical bytes only."""
    payload = canonical_bytes(value)
    if isinstance(payload, CalculationError):
        return payload
    return hashlib.sha256(payload).hexdigest()


def serialize_pricing_result(
    result: PricingResult,
) -> CanonicalPayload | CalculationError:
    """Build the versioned result envelope; ``content_hash`` covers content only."""
    if not isinstance(result, PricingResult):
        return CalculationError(
            ErrorCode.CONFIGURATION_ERROR,
            "result must be a PricingResult",
            "result",
        )
    result_value = to_canonical_value(result)
    if isinstance(result_value, CalculationError):
        return result_value
    content = MappingProxyType(
        {
            "content": result_value,
            "package_version": _PACKAGE_VERSION,
            "root_type": "PricingResult",
            "schema_version": CANONICAL_SCHEMA_VERSION,
        }
    )
    content_bytes = _encode(content)
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    return CanonicalPayload(
        CANONICAL_SCHEMA_VERSION,
        "PricingResult",
        cast(CanonicalValue, content),
        content_bytes,
        content_hash,
    )
