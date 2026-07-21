from typing import cast

from lvfi_pricing.core.errors import CalculationError
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
    assert b'"package_version":"0.11.0"' in payload.canonical_bytes


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
