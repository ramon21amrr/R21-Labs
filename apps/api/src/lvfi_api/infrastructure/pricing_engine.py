"""Approved public-only boundary for the Method One application use case."""

from __future__ import annotations

from lvfi_pricing.models.method_one import (
    METHOD_ONE_CANONICAL_SCHEMA_VERSION,
    MethodOneFinalResult,
    MethodOneRequest,
    method_one_sha256,
    run_method_one,
    serialize_method_one_final_result,
)

PUBLIC_METHOD_ONE_SCHEMA_VERSION = METHOD_ONE_CANONICAL_SCHEMA_VERSION


class PublicMethodOneFacade:
    """Expose only stable Method One facade calls to application services."""

    @staticmethod
    def run(request: MethodOneRequest) -> object:
        return run_method_one(request)

    @staticmethod
    def serialize(result: MethodOneFinalResult) -> object:
        return serialize_method_one_final_result(result)

    @staticmethod
    def sha256(value: object) -> object:
        return method_one_sha256(value)


public_method_one = PublicMethodOneFacade()


def pricing_engine_is_available() -> bool:
    """Prove the adapter resolves only the public, versioned Method One facade."""
    return (
        callable(public_method_one.run)
        and callable(public_method_one.serialize)
        and callable(public_method_one.sha256)
        and PUBLIC_METHOD_ONE_SCHEMA_VERSION == 1
    )
