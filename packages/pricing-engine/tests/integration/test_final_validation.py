"""Final synthetic end-to-end validation for LVFI-ENG-002-T13."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, fields, is_dataclass

import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.domain import PoissonRate, QuarterLine
from lvfi_pricing.engine import (
    AsianHandicapMainLineRequest,
    AsianHandicapRequest,
    AsianTotalMainLineRequest,
    AsianTotalRequest,
    BothTeamsToScoreRequest,
    DoubleChanceRequest,
    MarketRequest,
    PricingRequest,
    PricingResult,
    ThreeWayResultRequest,
    TotalGoalsRequest,
    run_pricing_engine,
)
from lvfi_pricing.markets import HalfGoalLine
from lvfi_pricing.serialization import CanonicalPayload, serialize_pricing_result
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection

RATE_CASES = (
    (0.0, 0.0),
    (0.5, 0.5),
    (1.0, 1.0),
    (1.5, 1.0),
    (1.0, 1.5),
    (2.5, 1.2),
    (5.0, 3.0),
    (10.0, 10.0),
)

EXPECTED_HASHES = {
    (0.0, 0.0): "8051a1b099137b2c56df3733e1e418d9ed9f95df3c35761c42b89b71bb311c75",
    (0.5, 0.5): "21271b4f51985ee5bec7c635dc9a25f15b3f5304571c761fc68fb4ac790e2e9b",
    (1.0, 1.0): "174828b2a00fabb07fedd8621d6ac696695ae006df18f0eeb9296c853e1c0e51",
    (1.5, 1.0): "1b9791d0dd26fbb7bca068d18dc259a5e07ccf6e3fe7ea1bd4a699f59006f10b",
    (1.0, 1.5): "3f271310adaa3ad25689a03f748c8467a2b8b982dcfa0301e9c5c0f6446b1ad9",
    (2.5, 1.2): "4b545f5fb97be85c2adb8d042d601b0ebf53dc4e0acae8408a3e5ceeac6c9210",
    (5.0, 3.0): "f175b1729f579a7048b045c1219f7007c0f51fb6b78b6d7263d62a20c7c42004",
    (10.0, 10.0): "11bdfc2a7addcf241a248f2a6bdfa888e7d4a6aa639095a809f59a11bba5d670",
}


def _markets(*, include_asian_total_main: bool) -> tuple[MarketRequest, ...]:
    values: tuple[MarketRequest, ...] = (
        ThreeWayResultRequest(),
        DoubleChanceRequest(),
        BothTeamsToScoreRequest(),
        TotalGoalsRequest(HalfGoalLine(5)),
        AsianHandicapRequest(HandicapSelection.HOME, QuarterLine(0)),
        AsianHandicapRequest(HandicapSelection.AWAY, QuarterLine(1)),
        AsianHandicapRequest(HandicapSelection.HOME, QuarterLine(2)),
        AsianTotalRequest(AsianTotalSelection.OVER, QuarterLine(8)),
        AsianTotalRequest(AsianTotalSelection.UNDER, QuarterLine(9)),
        AsianTotalRequest(AsianTotalSelection.OVER, QuarterLine(10)),
        AsianHandicapMainLineRequest(),
    )
    return (
        values + (AsianTotalMainLineRequest(),) if include_asian_total_main else values
    )


def _request(
    home: float,
    away: float,
    *,
    reverse: bool = False,
    include_asian_total_main: bool | None = None,
) -> PricingRequest:
    markets = _markets(
        include_asian_total_main=(home, away) != (0.0, 0.0)
        if include_asian_total_main is None
        else include_asian_total_main
    )
    original = tuple(reversed(markets)) if reverse else markets
    request = PricingRequest.create(PoissonRate(home), PoissonRate(away), original)
    assert isinstance(request, PricingRequest)
    assert original == (tuple(reversed(markets)) if reverse else markets)
    return request


def _result(home: float, away: float, *, reverse: bool = False) -> PricingResult:
    result = run_pricing_engine(_request(home, away, reverse=reverse))
    assert isinstance(result, PricingResult)
    return result


def _payload(result: PricingResult) -> CanonicalPayload:
    payload = serialize_pricing_result(result)
    assert isinstance(payload, CanonicalPayload)
    return payload


def _assert_safe_immutable(value: object) -> None:
    assert not isinstance(value, (list, dict, set))
    if isinstance(value, float):
        assert math.isfinite(value)
        return
    if isinstance(value, tuple):
        for item in value:
            _assert_safe_immutable(item)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            assert isinstance(key, str)
            _assert_safe_immutable(item)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_safe_immutable(getattr(value, field.name))


@pytest.mark.parametrize(("home", "away"), RATE_CASES)
def test_complete_requests_are_deterministic_canonical_and_regressive(
    home: float, away: float
) -> None:
    first = _result(home, away)
    reordered = _result(home, away, reverse=True)
    assert first == reordered
    assert first.request.requested_markets == reordered.request.requested_markets
    assert first.metadata.package_version == "1.0.0"
    assert first.metadata.deterministic
    assert not first.errors
    assert first.metadata.warnings_count == len(first.warnings)
    _assert_safe_immutable(first)

    payload = _payload(first)
    assert payload == _payload(reordered)
    assert payload.content_hash == EXPECTED_HASHES[(home, away)]
    assert len(payload.content_hash) == 64
    assert payload.content_hash == payload.content_hash.lower()
    assert payload.content_hash.encode("ascii") not in payload.canonical_bytes
    for forbidden in (
        b"C:\\Users",
        b"private-user",
        b".xlsx",
        b".xlsm",
        b"http://",
    ):
        assert forbidden not in payload.canonical_bytes


def test_zero_rates_total_main_line_fails_fast_with_typed_error() -> None:
    result = run_pricing_engine(_request(0.0, 0.0, include_asian_total_main=True))
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.FAIR_ODD_UNDEFINED
    assert result.field == "candidates"


def test_business_input_changes_change_canonical_content_and_hash() -> None:
    line_markets = (AsianTotalRequest(AsianTotalSelection.OVER, QuarterLine(9)),)
    changed_line_markets = (
        AsianTotalRequest(AsianTotalSelection.OVER, QuarterLine(10)),
    )
    changed_selection_markets = (
        AsianTotalRequest(AsianTotalSelection.UNDER, QuarterLine(9)),
    )
    inputs = (
        (1.5, line_markets),
        (1.5001, line_markets),
        (1.5, changed_line_markets),
        (1.5, changed_selection_markets),
    )
    hashes: set[str] = set()
    for home, markets in inputs:
        request = PricingRequest.create(PoissonRate(home), PoissonRate(1.0), markets)
        assert isinstance(request, PricingRequest)
        result = run_pricing_engine(request)
        assert isinstance(result, PricingResult)
        hashes.add(_payload(result).content_hash)
    assert len(hashes) == 4


def test_public_result_contract_is_frozen() -> None:
    result = _result(1.5, 1.0)
    with pytest.raises(FrozenInstanceError):
        result.errors = ()  # type: ignore[misc]
