from dataclasses import replace
from typing import cast

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.domain import PoissonRate
from lvfi_pricing.engine import (
    PricingRequest,
    PricingResult,
    ThreeWayResultRequest,
    run_pricing_engine,
)
from lvfi_pricing.serialization import CanonicalPayload, serialize_pricing_result


def test_serializes_complete_synthetic_pricing_result() -> None:
    request = PricingRequest.create(
        PoissonRate(1.5), PoissonRate(1.0), (ThreeWayResultRequest(),)
    )
    assert isinstance(request, PricingRequest)
    result = run_pricing_engine(request)
    assert isinstance(result, PricingResult)
    payload = serialize_pricing_result(result)
    assert isinstance(payload, CanonicalPayload)
    assert payload.schema_version == 1
    assert payload.root_type == "PricingResult"
    repeated = serialize_pricing_result(result)
    assert isinstance(repeated, CanonicalPayload)
    assert payload.content_hash == repeated.content_hash
    assert b'"package_version":"1.0.1"' in payload.canonical_bytes
    assert result.request.engine_version == "1.0.1"
    assert result.metadata.package_version == "1.0.1"


def test_serializes_typed_warning_with_immutable_context() -> None:
    request = PricingRequest.create(
        PoissonRate(1.5), PoissonRate(1.0), (ThreeWayResultRequest(),)
    )
    assert isinstance(request, PricingRequest)
    result = run_pricing_engine(request)
    assert isinstance(result, PricingResult)
    warning = CalculationWarning(
        ErrorCode.CONFIGURATION_ERROR,
        "synthetic warning",
        context={"source": "synthetic"},
    )
    payload = serialize_pricing_result(replace(result, warnings=(warning,)))
    assert isinstance(payload, CanonicalPayload)
    assert b"synthetic warning" in payload.canonical_bytes
    assert b"synthetic" in payload.canonical_bytes


def test_result_serializer_rejects_invalid_root_and_invalid_nested_value() -> None:
    assert isinstance(
        serialize_pricing_result(cast(PricingResult, object())), CalculationError
    )
    request = PricingRequest.create(
        PoissonRate(1.5), PoissonRate(1.0), (ThreeWayResultRequest(),)
    )
    assert isinstance(request, PricingRequest)
    result = run_pricing_engine(request)
    assert isinstance(result, PricingResult)
    object.__setattr__(result, "errors", (object(),))
    assert isinstance(serialize_pricing_result(result), CalculationError)
