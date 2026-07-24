"""Tests for the central, deterministic persistence metadata."""

from __future__ import annotations

from lvfi_api.persistence.metadata import NAMING_CONVENTION, metadata


def test_metadata_uses_the_declared_constraint_naming_convention() -> None:
    assert metadata.naming_convention == NAMING_CONVENTION
    assert NAMING_CONVENTION["pk"] == "pk_%(table_name)s"
