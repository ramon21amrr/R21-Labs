from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from lvfi_pricing.core import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.domain import PoissonRate
from lvfi_pricing.engine import (
    PricingRequest,
    PricingResult,
    ThreeWayResultRequest,
    run_pricing_engine,
)
from lvfi_pricing.models.method_one import (
    METHOD_ONE_MULTIPLIER_CATALOG,
    MethodOneAdjustedRateResult,
    MethodOnePricingResult,
    apply_method_one_multipliers,
    build_method_one_pricing_request,
    price_method_one,
    resolve_method_one_multipliers,
)
from lvfi_pricing.models.method_one import pricing as implementation
from lvfi_pricing.models.samples import StatisticCode
from tests.unit.models.method_one.test_base_rates import result


def adjusted() -> MethodOneAdjustedRateResult:
    base = result()
    resolutions = resolve_method_one_multipliers(
        (),
        match_id=base.match_id,
        competition_id=base.competition_id,
        statistic=base.statistic,
        period=base.period,
    )
    assert isinstance(resolutions, tuple)
    value = apply_method_one_multipliers(base, resolutions)
    assert isinstance(value, MethodOneAdjustedRateResult)
    return value


def failure(value: object) -> CalculationError:
    assert isinstance(value, CalculationError)
    return value


def test_builds_deterministic_request_and_normalizes_negative_zero() -> None:
    value = adjusted()
    object.__setattr__(value, "home_adjusted_rate", -0.0)
    object.__setattr__(value.explanation, "home_adjusted_rate", -0.0)
    first = build_method_one_pricing_request(value)
    second = build_method_one_pricing_request(value)
    assert isinstance(first, PricingRequest)
    assert first == second
    assert first.home_rate.value == 0.0
    assert first.home_rate.value.hex() == "0x0.0p+0"
    assert first.away_rate.value == value.away_adjusted_rate
    assert first.requested_markets == (ThreeWayResultRequest(),)


def test_prices_explicitly_and_retains_all_t06_information() -> None:
    value = adjusted()
    priced = price_method_one(value)
    direct_request = build_method_one_pricing_request(value)
    assert isinstance(priced, MethodOnePricingResult)
    assert isinstance(direct_request, PricingRequest)
    assert priced.adjusted_rates is value
    assert priced.pricing_request == direct_request
    assert priced.pricing_result.request == direct_request
    assert priced.home_poisson_rate == direct_request.home_rate
    assert priced.away_poisson_rate == direct_request.away_rate
    assert priced.quality is value.quality
    assert priced.warnings is value.warnings
    assert priced.blockers is value.blockers
    assert priced.explanation.engine_called
    assert priced.explanation.catalog_version == "lvfi-method-one-adjustments@1.0.0"
    assert priced.pricing_engine_version == "1.0.0"
    assert priced.integration_schema_version == 1
    assert priced.deterministic
    with pytest.raises(FrozenInstanceError):
        cast(Any, priced).pricing_result = object()


@pytest.mark.parametrize("field", ("home_adjusted_rate", "away_adjusted_rate"))
@pytest.mark.parametrize("value", (-1.0, float("nan"), float("inf"), True))
def test_invalid_adjusted_rates_are_rejected(field: str, value: object) -> None:
    source = adjusted()
    object.__setattr__(source, field, value)
    object.__setattr__(source.explanation, field, value)
    assert (
        failure(build_method_one_pricing_request(source)).code
        is ErrorCode.INVALID_NUMBER
    )


@pytest.mark.parametrize(
    ("field", "value", "code"),
    (
        ("method_version", "bad", ErrorCode.SCHEMA_VERSION_UNSUPPORTED),
        ("adjusted_rate_schema_version", 2, ErrorCode.SCHEMA_VERSION_UNSUPPORTED),
        ("deterministic", False, ErrorCode.SCHEMA_VERSION_UNSUPPORTED),
        ("match_id", "", ErrorCode.INCONSISTENT_DATA),
        ("competition_id", "bad id", ErrorCode.INCONSISTENT_DATA),
        ("statistic", StatisticCode.CORNERS, ErrorCode.MODEL_NOT_APPLICABLE),
        ("period", cast(Any, object()), ErrorCode.MODEL_NOT_APPLICABLE),
        ("quality", object(), ErrorCode.INCONSISTENT_DATA),
        ("warnings", cast(Any, []), ErrorCode.INCONSISTENT_DATA),
        ("blockers", cast(Any, []), ErrorCode.INCONSISTENT_DATA),
    ),
)
def test_rejects_invalid_handoff_contract_fields(
    field: str, value: object, code: ErrorCode
) -> None:
    source = adjusted()
    object.__setattr__(source, field, value)
    assert failure(build_method_one_pricing_request(source)).code is code


@pytest.mark.parametrize(
    "mutation",
    (
        lambda source: object.__setattr__(source, "explanation", object()),
        lambda source: object.__setattr__(
            source.explanation, "explanation_schema_version", 2
        ),
        lambda source: object.__setattr__(source.explanation, "catalog_version", "bad"),
        lambda source: object.__setattr__(source.explanation, "deterministic", False),
        lambda source: object.__setattr__(
            source.explanation, "home_adjusted_rate", 9.0
        ),
        lambda source: object.__setattr__(source.explanation, "resolutions", ()),
        lambda source: object.__setattr__(source.explanation, "quality", object()),
        lambda source: object.__setattr__(
            source.explanation,
            "warnings",
            (CalculationWarning(ErrorCode.SAMPLE_INSUFFICIENT, "warning"),),
        ),
        lambda source: object.__setattr__(
            source.explanation,
            "blockers",
            (CalculationError(ErrorCode.SAMPLE_EMPTY, "blocker"),),
        ),
    ),
)
def test_rejects_incoherent_explanation(mutation: object) -> None:
    source = adjusted()
    cast(Any, mutation)(source)
    assert (
        failure(build_method_one_pricing_request(source)).code
        is ErrorCode.INCONSISTENT_DATA
    )


def test_rejects_bad_resolution_collection_and_blocked_quality() -> None:
    source = adjusted()
    object.__setattr__(source, "resolutions", cast(Any, []))
    object.__setattr__(source.explanation, "resolutions", cast(Any, []))
    assert (
        failure(build_method_one_pricing_request(source)).code
        is ErrorCode.INVALID_MULTIPLIER
    )
    source = adjusted()
    item = source.resolutions[0]
    object.__setattr__(item, "catalog_version", "bad")
    assert (
        failure(build_method_one_pricing_request(source)).code
        is ErrorCode.INVALID_MULTIPLIER
    )
    source = adjusted()
    object.__setattr__(source.quality, "calculation_allowed", False)
    assert (
        failure(build_method_one_pricing_request(source)).code
        is ErrorCode.MODEL_NOT_APPLICABLE
    )


def test_public_api_and_root_alias_boundary() -> None:
    import lvfi_pricing
    from lvfi_pricing.models import method_one

    assert "build_method_one_pricing_request" in method_one.__all__
    assert "price_method_one" in method_one.__all__
    assert not hasattr(lvfi_pricing, "price_method_one")
    assert len(METHOD_ONE_MULTIPLIER_CATALOG.entries) == 22


def test_engine_and_poisson_typed_failures_propagate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = adjusted()
    error = CalculationError(ErrorCode.INVALID_LAMBDA, "bad", "lambda")
    monkeypatch.setattr(PoissonRate, "create", lambda value: error)
    assert build_method_one_pricing_request(source) is error
    monkeypatch.undo()
    request = build_method_one_pricing_request(source)
    assert isinstance(request, PricingRequest)
    engine_error = CalculationError(ErrorCode.NUMERIC_CONVERGENCE_FAILED, "bad")
    monkeypatch.setattr(
        implementation, "run_pricing_engine", lambda value: engine_error
    )
    assert price_method_one(source) is engine_error


def test_source_has_no_io_serialization_or_internal_engine_imports() -> None:
    source = implementation.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read()
    for forbidden in (
        "serialize_",
        "hashlib",
        "datetime",
        "open(",
        "requests",
        "settlement",
    ):
        assert forbidden not in text


def test_internal_validation_and_late_failures_are_typed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert (
        failure(implementation._validate_adjusted_rates(object())).code
        is ErrorCode.INCONSISTENT_DATA
    )
    source = adjusted()
    calls = 0
    error = CalculationError(ErrorCode.INVALID_LAMBDA, "bad", "lambda")
    original_create = PoissonRate.create

    def create(value: object) -> PoissonRate | CalculationError:
        nonlocal calls
        calls += 1
        return original_create(value) if calls == 1 else error

    monkeypatch.setattr(PoissonRate, "create", create)
    assert build_method_one_pricing_request(source) is error
    monkeypatch.undo()
    assert (
        failure(price_method_one(cast(Any, object()))).code
        is ErrorCode.INCONSISTENT_DATA
    )
    original_run = run_pricing_engine

    def mutate(request: PricingRequest) -> PricingResult | CalculationError:
        object.__setattr__(source, "method_version", "bad")
        return original_run(request)

    monkeypatch.setattr(implementation, "run_pricing_engine", mutate)
    assert (
        failure(price_method_one(source)).code is ErrorCode.SCHEMA_VERSION_UNSUPPORTED
    )
