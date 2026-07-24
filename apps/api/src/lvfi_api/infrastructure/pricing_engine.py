"""Approved public boundary for a future Method One application use case."""

from lvfi_pricing.models.method_one import (
    METHOD_ONE_CANONICAL_SCHEMA_VERSION,
    run_method_one,
)

PUBLIC_METHOD_ONE_SCHEMA_VERSION = METHOD_ONE_CANONICAL_SCHEMA_VERSION


def pricing_engine_is_available() -> bool:
    """Prove the future adapter resolves only the public Method One facade."""
    return callable(run_method_one) and PUBLIC_METHOD_ONE_SCHEMA_VERSION == 1
