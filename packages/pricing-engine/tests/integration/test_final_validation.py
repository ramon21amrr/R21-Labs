"""Final synthetic end-to-end validation for LVFI-ENG-002-T13."""

from __future__ import annotations

import gzip
import json
import math
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path
from typing import cast

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
from tests.integration.pricing_engine_baselines import (
    MATHEMATICAL_CHANGE_CASES,
    OPERATIONAL_ENGINE_VERSION,
    OPERATIONAL_HASHES,
    VERSION_ONLY_CASES,
)

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
    assert first.metadata.package_version == OPERATIONAL_ENGINE_VERSION
    assert first.metadata.deterministic
    assert not first.errors
    assert first.metadata.warnings_count == len(first.warnings)
    _assert_safe_immutable(first)

    payload = _payload(first)
    assert payload == _payload(reordered)
    assert payload.content_hash == OPERATIONAL_HASHES[(home, away)]
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


def _audit_projection(value: object, *, mask_mass: bool) -> object:
    if isinstance(value, list):
        return [_audit_projection(item, mask_mass=mask_mass) for item in value]
    if not isinstance(value, dict):
        return "<VERSION>" if value in {"1.0.0", "1.0.1"} else value
    projected = {
        key: _audit_projection(item, mask_mass=mask_mass) for key, item in value.items()
    }
    if mask_mass and set(value) == {"fields", "schema_version", "type"}:
        fields = projected["fields"]
        assert isinstance(fields, dict)
        for field in ("total_probability", "residual_mass", "probability", "fair_odds"):
            if field in fields:
                fields[field] = "<CANONICAL_MASS>"
    return projected


def _payload_baselines() -> dict[str, object]:
    fixture = Path(__file__).with_name("pricing_engine_payload_baselines.json.gz")
    loaded = cast(dict[str, object], json.loads(gzip.decompress(fixture.read_bytes())))
    assert loaded["fixture_schema"] == 1
    assert loaded["historical_engine_version"] == "1.0.0"
    assert loaded["operational_engine_version"] == OPERATIONAL_ENGINE_VERSION
    return loaded


def _case_key(home: float, away: float) -> str:
    return f"{home:.1f}x{away:.1f}"


def test_versioned_baselines_preserve_only_authorized_payload_differences() -> None:
    baseline = _payload_baselines()
    stored = baseline["payloads"]
    assert isinstance(stored, dict)
    for home, away in (*VERSION_ONLY_CASES, *MATHEMATICAL_CHANGE_CASES):
        record = stored[_case_key(home, away)]
        assert isinstance(record, dict)
        historical = record["historical"]
        operational = record["operational"]
        assert isinstance(historical, dict)
        assert isinstance(operational, dict)
        assert historical["content_hash"] != operational["content_hash"]
        assert operational["content_hash"] == OPERATIONAL_HASHES[(home, away)]
        payload = _payload(_result(home, away))
        assert payload.content_hash == operational["content_hash"]
        assert payload.canonical_bytes.decode() == operational["canonical_json"]
        historical_json = json.loads(historical["canonical_json"])
        operational_json = json.loads(operational["canonical_json"])
        if (home, away) in VERSION_ONLY_CASES:
            assert _audit_projection(
                historical_json, mask_mass=False
            ) == _audit_projection(operational_json, mask_mass=False)
        else:
            assert _audit_projection(
                historical_json, mask_mass=True
            ) == _audit_projection(operational_json, mask_mass=True)
