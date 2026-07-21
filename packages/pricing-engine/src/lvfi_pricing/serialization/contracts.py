"""Immutable public contracts for canonical Pricing Engine payloads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

CanonicalValue = (
    None
    | bool
    | int
    | str
    | tuple["CanonicalValue", ...]
    | Mapping[str, "CanonicalValue"]
)


@dataclass(frozen=True, slots=True)
class CanonicalPayload:
    """Versioned, immutable content identity for a supported public contract."""

    schema_version: int
    root_type: str
    canonical_value: CanonicalValue
    canonical_bytes: bytes
    content_hash: str
    hash_algorithm: str = "sha256"
