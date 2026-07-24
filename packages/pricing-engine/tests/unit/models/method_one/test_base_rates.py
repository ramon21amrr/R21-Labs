from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from lvfi_pricing.core import CalculationError, ErrorCode
from lvfi_pricing.models.method_one import (
    MethodOneBaseRateResult,
    MethodOneConfiguration,
    MethodOneContextualAverages,
    MethodOneSeriesRole,
    MethodOneWeightConfiguration,
    calculate_contextual_average,
    calculate_method_one_base_rates,
)
from lvfi_pricing.models.samples import (
    MatchPeriodCode,
    SampleQualityLevel,
    StatisticCode,
)
from tests.unit.models.method_one.test_averages import sample


def averages(
    values: tuple[float, float, float, float] = (2.0, 1.0, 3.0, 4.0),
    counts: tuple[int, int, int, int] = (10, 10, 10, 10),
) -> MethodOneContextualAverages:
    calculated = []
    for role, value, count in zip(MethodOneSeriesRole, values, counts, strict=True):
        average = calculate_contextual_average(sample((value,) * count, role=role))
        assert not isinstance(average, CalculationError)
        calculated.append(average)
    return MethodOneContextualAverages(
        calculated[0],
        calculated[1],
        calculated[2],
        calculated[3],
        "target",
        "competition",
        StatisticCode.GOALS,
        MatchPeriodCode.REGULATION_TIME,
        "home",
        "away",
    )


def calculate(
    source: MethodOneContextualAverages | None = None,
    configuration: MethodOneConfiguration | None = None,
) -> MethodOneBaseRateResult | CalculationError:
    return calculate_method_one_base_rates(
        averages() if source is None else source,
        MethodOneConfiguration("base-rates")
        if configuration is None
        else configuration,
    )


def result(
    source: MethodOneContextualAverages | None = None,
    configuration: MethodOneConfiguration | None = None,
) -> MethodOneBaseRateResult:
    calculated = calculate(source, configuration)
    assert isinstance(calculated, MethodOneBaseRateResult)
    return calculated


def failure(value: object) -> CalculationError:
    assert isinstance(value, CalculationError)
    return value


def test_default_formula_audit_public_api_and_immutability() -> None:
    calculated = result()
    assert (calculated.home_base_rate, calculated.away_base_rate) == (3.0, 2.0)
    assert calculated.explanation.home.own_production.value == 1.0
    assert calculated.explanation.home.opponent_concession.value == 2.0
    assert calculated.explanation.away.own_production.value == 1.5
    assert calculated.explanation.away.opponent_concession.value == 0.5
    assert calculated.statistic is StatisticCode.GOALS
    assert calculated.period is MatchPeriodCode.REGULATION_TIME
    assert (calculated.home_team_id, calculated.away_team_id) == ("home", "away")
    assert (calculated.match_id, calculated.competition_id) == ("target", "competition")
    assert calculated.explanation.averages == calculated.contextual_averages.values
    assert calculated.explanation.consolidated_quality is calculated.quality
    assert (
        calculated.method_version == calculated.explanation.formula_version == "1.0.0a5"
    )
    assert calculated.explanation.explanation_schema_version == 1
    assert calculated.result_schema_version == 2
    with pytest.raises(FrozenInstanceError):
        calculated.home_base_rate = 1.0  # type: ignore[misc]


def test_custom_weights_extremes_zero_and_determinism() -> None:
    source = averages(counts=(1, 10, 10, 1))
    custom = MethodOneConfiguration(
        "custom",
        MethodOneWeightConfiguration(0.25, 0.75),
        MethodOneWeightConfiguration(0.75, 0.25),
    )
    assert (
        result(source, custom).home_base_rate,
        result(source, custom).away_base_rate,
    ) == (3.5, 2.5)
    extremes = result(
        source,
        MethodOneConfiguration(
            "extremes",
            MethodOneWeightConfiguration(1.0, 0.0),
            MethodOneWeightConfiguration(0.0, 1.0),
        ),
    )
    assert (extremes.home_base_rate, extremes.away_base_rate) == (2.0, 1.0)
    zero = result(averages((0.0, 0.0, 0.0, 0.0)))
    assert (zero.home_base_rate, zero.away_base_rate) == (0.0, 0.0)
    assert result(source) == result(source)
    assert source == averages(counts=(1, 10, 10, 1))


@pytest.mark.parametrize("value", (-1.0, float("nan"), float("inf"), True))
def test_invalid_average_numbers_are_rejected(value: object) -> None:
    source = averages()
    object.__setattr__(source.home_production, "value", value)
    assert failure(calculate(source)).code is ErrorCode.INVALID_NUMBER


def test_average_roles_versions_quality_and_context_are_validated() -> None:
    source = averages()
    object.__setattr__(source, "away_concession", source.home_production)
    assert failure(calculate(source)).code is ErrorCode.INCONSISTENT_DATA
    source = averages()
    object.__setattr__(source.home_production, "average_schema_version", 2)
    assert failure(calculate(source)).code is ErrorCode.SCHEMA_VERSION_UNSUPPORTED
    source = averages()
    assert source.home_production.evidence is not None
    object.__setattr__(
        source.home_production.evidence, "common_contract_version", "bad"
    )
    assert failure(calculate(source)).code is ErrorCode.SCHEMA_VERSION_UNSUPPORTED
    source = averages()
    assert source.home_production.evidence is not None
    object.__setattr__(source.home_production.evidence, "subject_id", "away")
    assert failure(calculate(source)).code is ErrorCode.INCONSISTENT_DATA
    source = averages()
    assert source.away_concession.evidence is not None
    object.__setattr__(
        source.away_concession.evidence, "period", MatchPeriodCode.FIRST_HALF
    )
    assert failure(calculate(source)).code is ErrorCode.INCONSISTENT_DATA
    source = averages()
    assert source.home_concession.evidence is not None
    object.__setattr__(
        source.home_concession.evidence.quality, "calculation_allowed", False
    )
    assert failure(calculate(source)).code is ErrorCode.MODEL_NOT_APPLICABLE


def test_quality_consolidates_to_worst_and_preserves_warnings() -> None:
    for counts, level in (
        ((10, 10, 10, 10), SampleQualityLevel.ADEQUATE),
        ((10, 5, 10, 10), SampleQualityLevel.PARTIAL),
        ((10, 1, 10, 10), SampleQualityLevel.INSUFFICIENT),
    ):
        calculated = result(averages(counts=counts))
        assert calculated.quality.level is level
        assert calculated.explanation.qualities[1].level is level
        assert bool(calculated.warnings) is (level is not SampleQualityLevel.ADEQUATE)


def test_configuration_validation_boundaries() -> None:
    source = averages()
    assert failure(calculate(cast(Any, object()))).code is ErrorCode.INCONSISTENT_DATA
    assert (
        failure(calculate(source, cast(Any, object()))).code
        is ErrorCode.CONFIGURATION_ERROR
    )
    bad = MethodOneConfiguration(
        "bad", MethodOneWeightConfiguration(), MethodOneWeightConfiguration()
    )
    object.__setattr__(bad, "multiplier_resolutions", (object(),))
    assert failure(calculate(source, bad)).code is ErrorCode.INVALID_MULTIPLIER
    bad = MethodOneConfiguration(
        "bad", MethodOneWeightConfiguration(), MethodOneWeightConfiguration()
    )
    object.__setattr__(bad.home_weights, "weight_own", 2.0)
    assert failure(calculate(source, bad)).code is ErrorCode.INVALID_WEIGHT
    bad = MethodOneConfiguration(
        "bad", MethodOneWeightConfiguration(), MethodOneWeightConfiguration()
    )
    object.__setattr__(bad.home_weights, "weight_opponent", 0.4)
    assert failure(calculate(source, bad)).code is ErrorCode.WEIGHTS_SUM_INVALID


def test_remaining_configuration_and_numeric_error_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import lvfi_pricing.models.method_one.base_rates as base_rates

    source = averages()
    bad = MethodOneConfiguration(
        "bad", MethodOneWeightConfiguration(), MethodOneWeightConfiguration()
    )
    object.__setattr__(bad, "home_weights", object())
    assert failure(calculate(source, bad)).code is ErrorCode.INVALID_WEIGHT
    bad = MethodOneConfiguration(
        "bad", MethodOneWeightConfiguration(), MethodOneWeightConfiguration()
    )
    object.__setattr__(bad.home_weights, "configuration_version", "other")
    assert failure(calculate(source, bad)).code is ErrorCode.SCHEMA_VERSION_UNSUPPORTED
    bad = MethodOneConfiguration(
        "bad", MethodOneWeightConfiguration(), MethodOneWeightConfiguration()
    )
    object.__setattr__(bad, "formula_version", "other")
    assert failure(calculate(source, bad)).code is ErrorCode.SCHEMA_VERSION_UNSUPPORTED
    bad = MethodOneConfiguration(
        "bad", MethodOneWeightConfiguration(), MethodOneWeightConfiguration()
    )
    object.__setattr__(bad, "numeric_policy", object())
    assert failure(calculate(source, bad)).code is ErrorCode.CONFIGURATION_ERROR

    own = base_rates._participant(
        "home", source.home_production, float("inf"), source.away_concession, 0.0
    )
    assert failure(own).code is ErrorCode.INVALID_NUMBER
    opponent = base_rates._participant(
        "home", source.home_production, 0.0, source.away_concession, float("inf")
    )
    assert failure(opponent).code is ErrorCode.INVALID_NUMBER
    monkeypatch.setattr(
        base_rates,
        "stable_sum",
        lambda _: CalculationError(ErrorCode.INVALID_NUMBER, "bad"),
    )
    assert (
        failure(
            base_rates._participant(
                "home", source.home_production, 0.5, source.away_concession, 0.5
            )
        ).code
        is ErrorCode.INVALID_NUMBER
    )
    monkeypatch.setattr(base_rates, "stable_sum", lambda _: -1.0)
    assert (
        failure(
            base_rates._participant(
                "home", source.home_production, 0.5, source.away_concession, 0.5
            )
        ).code
        is ErrorCode.INVALID_NUMBER
    )


def test_calculation_propagates_participant_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import lvfi_pricing.models.method_one.base_rates as base_rates

    source, configuration = averages(), MethodOneConfiguration("x")
    original = base_rates._participant
    error = CalculationError(ErrorCode.INVALID_NUMBER, "bad")
    monkeypatch.setattr(base_rates, "_participant", lambda *_: error)
    assert calculate(source, configuration) is error
    calls = 0

    def second_participant(*args: Any) -> object:
        nonlocal calls
        calls += 1
        return original(*args) if calls == 1 else error

    monkeypatch.setattr(base_rates, "_participant", second_participant)
    assert calculate(source, configuration) is error


def test_public_exports_are_explicit_and_not_aliased_at_root() -> None:
    import lvfi_pricing
    from lvfi_pricing.models.method_one import __all__

    assert "calculate_method_one_base_rates" in __all__
    assert "MethodOneBaseRateResult" in __all__
    assert not hasattr(lvfi_pricing, "calculate_method_one_base_rates")

