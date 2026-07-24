from lvfi_pricing.models.method_one import (
    METHOD_ONE_CANONICAL_SCHEMA_VERSION,
    MethodOneConfiguration,
    MethodOneFinalResult,
    MethodOneIdentity,
    MethodOnePayload,
    MethodOneRequest,
    MethodOneWeightConfiguration,
    method_one_canonical_bytes,
    method_one_identity,
    run_method_one,
    serialize_method_one_final_result,
)
from lvfi_pricing.models.samples import MatchPeriodCode, StatisticCode
from lvfi_pricing.serialization import sha256_canonical
from tests.unit.models.method_one.test_multipliers import candidate
from tests.unit.models.method_one.test_orchestration import request

FROZEN_FINAL_RESULT_HASH = (
    "46fa5524f9d9650d773b531e93676c3c5b6c3b5d281c0bd716ba703476e04480"
)


def _final_result() -> MethodOneFinalResult:
    value = run_method_one(request(), (candidate(),))
    assert isinstance(value, MethodOneFinalResult)
    return value


def test_serializes_end_to_end_method_one_run() -> None:
    payload = serialize_method_one_final_result(_final_result())
    assert isinstance(payload, MethodOnePayload)
    assert payload.schema_version == METHOD_ONE_CANONICAL_SCHEMA_VERSION
    assert payload.root_type == "MethodOneFinalResult"
    assert payload.content_hash == FROZEN_FINAL_RESULT_HASH


def test_repeated_runs_produce_identical_payload_and_identity() -> None:
    first_payload = serialize_method_one_final_result(_final_result())
    second_payload = serialize_method_one_final_result(_final_result())
    assert isinstance(first_payload, MethodOnePayload)
    assert isinstance(second_payload, MethodOnePayload)
    assert first_payload.canonical_bytes == second_payload.canonical_bytes
    assert first_payload.content_hash == second_payload.content_hash

    first_identity = method_one_identity(_final_result())
    second_identity = method_one_identity(_final_result())
    assert isinstance(first_identity, MethodOneIdentity)
    assert first_identity == second_identity


def test_nested_pricing_result_reuses_pricing_engine_serialization() -> None:
    result = _final_result()
    nested = result.pricing.pricing_result
    # Canonicalizing the nested PricingResult through the Method One registry
    # produces bytes identical to the Pricing Engine serializer (no duplicated
    # serializer, exact same content hash).
    method_one_digest = method_one_canonical_bytes(nested)
    engine_digest = sha256_canonical(nested)
    assert isinstance(method_one_digest, bytes)
    assert isinstance(engine_digest, str)
    assert method_one_digest == method_one_canonical_bytes(nested)
    from hashlib import sha256

    assert sha256(method_one_digest).hexdigest() == engine_digest


def test_identity_diverges_when_multiplier_input_changes() -> None:
    baseline = method_one_identity(_final_result())
    divergent = run_method_one(request(), ())
    assert isinstance(divergent, MethodOneFinalResult)
    other = method_one_identity(divergent)
    assert isinstance(baseline, MethodOneIdentity)
    assert isinstance(other, MethodOneIdentity)
    # Same configuration (default weights/recency) but different multiplier input.
    assert baseline.configuration_hash == other.configuration_hash
    assert baseline.input_hash != other.input_hash
    assert baseline.result_hash != other.result_hash
    assert baseline != other


def test_identity_diverges_when_configuration_changes() -> None:
    result = _final_result()
    asymmetric = MethodOneConfiguration(
        "asymmetric",
        MethodOneWeightConfiguration(0.6, 0.4),
        MethodOneWeightConfiguration(0.6, 0.4),
    )
    other_request = MethodOneRequest(
        result.match_id,
        result.home_team_id,
        result.away_team_id,
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        result.request.series_references,
        asymmetric,
        result.competition_id,
    )
    rerun = run_method_one(other_request, (candidate(),))
    assert isinstance(rerun, MethodOneFinalResult)
    baseline = method_one_identity(result)
    changed = method_one_identity(rerun)
    assert isinstance(baseline, MethodOneIdentity)
    assert isinstance(changed, MethodOneIdentity)
    assert baseline.configuration_hash != changed.configuration_hash
    assert baseline.result_hash != changed.result_hash


def test_public_api_is_importable_from_method_one_package() -> None:
    import lvfi_pricing.models.method_one as method_one

    for name in (
        "serialize_method_one_final_result",
        "method_one_identity",
        "method_one_canonical_bytes",
        "method_one_canonical_value",
        "method_one_sha256",
        "MethodOnePayload",
        "MethodOneIdentity",
        "METHOD_ONE_CANONICAL_SCHEMA_VERSION",
    ):
        assert name in method_one.__all__
        assert hasattr(method_one, name)


def test_serialization_does_not_mutate_the_result() -> None:
    result = _final_result()
    first = serialize_method_one_final_result(result)
    second = serialize_method_one_final_result(result)
    assert isinstance(first, MethodOnePayload)
    assert isinstance(second, MethodOnePayload)
    assert first.canonical_bytes == second.canonical_bytes
    assert result.pricing.pricing_result is result.pricing.pricing_result
