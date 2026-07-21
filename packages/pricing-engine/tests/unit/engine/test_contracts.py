from typing import cast

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy
from lvfi_pricing.domain import PoissonRate, QuarterLine
from lvfi_pricing.engine import (
    AsianHandicapRequest,
    AsianTotalRequest,
    DoubleChanceRequest,
    PricingRequest,
    ThreeWayResultRequest,
)
from lvfi_pricing.markets import HalfGoalLine
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection


def test_request_is_immutable_canonical_and_rejects_duplicates() -> None:
    request = PricingRequest.create(
        PoissonRate(1.0),
        PoissonRate(1.0),
        (DoubleChanceRequest(), ThreeWayResultRequest()),
        NumericPolicy(),
    )
    assert isinstance(request, PricingRequest)
    assert request.requested_markets == (ThreeWayResultRequest(), DoubleChanceRequest())
    duplicate = PricingRequest.create(
        PoissonRate(1.0),
        PoissonRate(1.0),
        (ThreeWayResultRequest(), ThreeWayResultRequest()),
    )
    assert isinstance(duplicate, CalculationError)
    assert duplicate.code is ErrorCode.INVALID_MARKET


def test_request_validation_branches() -> None:
    rate = PoissonRate(1.0)
    invalids = (
        ("bad", rate, (ThreeWayResultRequest(),)),
        (rate, rate, ()),
        (rate, rate, [ThreeWayResultRequest()]),
        (rate, rate, (object(),)),
        (
            rate,
            rate,
            (AsianHandicapRequest(cast(HandicapSelection, "home"), QuarterLine(0)),),
        ),
        (
            rate,
            rate,
            (AsianTotalRequest(AsianTotalSelection.OVER, cast(QuarterLine, "line")),),
        ),
    )
    for home, away, markets in invalids:
        value = PricingRequest.create(home, away, markets)
        assert isinstance(value, CalculationError)
    schema = PricingRequest.create(
        rate, rate, (ThreeWayResultRequest(),), request_schema_version=2
    )
    assert isinstance(schema, CalculationError)
    assert schema.code is ErrorCode.SCHEMA_VERSION_UNSUPPORTED
    policy = PricingRequest.create(
        rate, rate, (ThreeWayResultRequest(),), numeric_policy="bad"
    )
    assert isinstance(policy, CalculationError)
    version = PricingRequest.create(
        rate, rate, (ThreeWayResultRequest(),), engine_version="bad"
    )
    assert isinstance(version, CalculationError)
    assert version.code is ErrorCode.CONFIGURATION_ERROR
    assert HalfGoalLine(1).half_units == 1
    assert HandicapSelection.HOME.value == "home"
