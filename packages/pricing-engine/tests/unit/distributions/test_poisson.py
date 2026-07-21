"""Testes unitários do núcleo Poisson adaptativo."""

from dataclasses import FrozenInstanceError
from math import isclose

import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy
from lvfi_pricing.distributions import (
    PoissonDistribution,
    build_poisson_distribution,
    poisson_pmf,
)
from lvfi_pricing.distributions import poisson as poisson_module
from lvfi_pricing.domain import PoissonRate


def rate(value: float) -> PoissonRate:
    result = PoissonRate.create(value)
    assert isinstance(result, PoissonRate)
    return result


@pytest.mark.parametrize(
    ("lambda_value", "count", "expected"),
    [
        (0.0, 0, 1.0),
        (0.0, 1, 0.0),
        (1.0, 0, 0.36787944117144233),
        (1.0, 1, 0.36787944117144233),
        (1.0, 2, 0.18393972058572117),
    ],
)
def test_pmf_known_values(lambda_value: float, count: int, expected: float) -> None:
    result = poisson_pmf(rate(lambda_value), count)
    assert isinstance(result, float)
    assert result == expected


@pytest.mark.parametrize("count", [-1, True, 1.0, "1"])
def test_pmf_rejects_invalid_counts(count: object) -> None:
    result = poisson_pmf(rate(1.0), count)
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.INVALID_NUMBER


def test_pmf_rejects_non_rate_and_is_deterministic() -> None:
    assert poisson_pmf(1.0, 0).code is ErrorCode.INVALID_LAMBDA  # type: ignore[union-attr,arg-type]
    assert poisson_pmf(rate(2.5), 7) == poisson_pmf(rate(2.5), 7)


@pytest.mark.parametrize("lambda_value", [0.0, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0])
def test_adaptive_distribution_reference_cases(lambda_value: float) -> None:
    result = build_poisson_distribution(rate(lambda_value))
    assert isinstance(result, PoissonDistribution)
    assert result.max_count == len(result.probabilities) - 1
    assert result.max_count >= 10
    assert result.probabilities[0] == poisson_pmf(result.rate, 0)
    assert result.cumulative_probability == sum(result.probabilities) or isclose(
        result.cumulative_probability, sum(result.probabilities), abs_tol=1e-15
    )
    assert result.residual_mass == 1.0 - result.cumulative_probability
    assert result.residual_mass <= NumericPolicy().poisson_residual_tolerance
    assert result.converged is True
    assert result.warnings == ()
    assert all(probability >= 0.0 for probability in result.probabilities)


def test_support_expands_beyond_initial_limit_and_result_is_immutable() -> None:
    result = build_poisson_distribution(rate(20.0))
    assert isinstance(result, PoissonDistribution)
    assert result.max_count > 10
    with pytest.raises(FrozenInstanceError):
        result.max_count = 0  # type: ignore[misc]
    with pytest.raises(TypeError):
        result.probabilities[0] = 0.0  # type: ignore[index]
    assert result == build_poisson_distribution(rate(20.0))


def test_explicit_zero_tolerance_and_invalid_policy() -> None:
    strict = NumericPolicy(poisson_residual_tolerance=0.0)
    result = build_poisson_distribution(rate(0.0), strict)
    assert isinstance(result, PoissonDistribution)
    assert result.residual_mass == 0.0
    invalid = build_poisson_distribution(rate(1.0), object())  # type: ignore[arg-type]
    assert isinstance(invalid, CalculationError)
    assert invalid.code is ErrorCode.CONFIGURATION_ERROR


def test_distribution_rejects_non_rate() -> None:
    result = build_poisson_distribution(1.0)  # type: ignore[arg-type]
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.INVALID_LAMBDA


def test_non_convergence_reports_safe_deterministic_context() -> None:
    result = build_poisson_distribution(rate(1_000.0))
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.NUMERIC_CONVERGENCE_FAILED
    assert result.context == {
        "max_count": 1_000,
        "rate": 1_000.0,
        "residual_mass": 1.0,
        "tolerance": 1e-14,
    }
    assert "traceback" not in str(result.context).lower()


def test_constructor_validates_contract() -> None:
    valid_rate = rate(0.0)
    with pytest.raises(CalculationError, match="max_count"):
        PoissonDistribution(valid_rate, (1.0,), 1, 1.0, 0.0, True)
    with pytest.raises(CalculationError, match="warnings"):
        PoissonDistribution(valid_rate, (1.0,), 0, 1.0, 0.0, True, ())
        PoissonDistribution(valid_rate, (1.0,), 0, 1.0, 0.0, True, (object(),))  # type: ignore[arg-type]
    with pytest.raises(CalculationError, match="probabilities"):
        PoissonDistribution(valid_rate, (float("nan"),), 0, 1.0, 0.0, True)
    with pytest.raises(CalculationError, match="finite"):
        PoissonDistribution(valid_rate, (1.0,), 0, float("inf"), 0.0, True)


def test_internal_sum_failures_are_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(poisson_module, "stable_sum", lambda _: 2.0)
    result = build_poisson_distribution(rate(0.0))
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.PROBABILITY_SUM_INVALID

    monkeypatch.setattr(
        poisson_module,
        "stable_sum",
        lambda _: CalculationError(ErrorCode.INVALID_NUMBER, "bad"),
    )
    result = build_poisson_distribution(rate(0.0))
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.PROBABILITY_SUM_INVALID


def test_negative_residual_and_internal_pmf_failure_are_typed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(poisson_module, "_validated_total", lambda *_: 2.0)
    result = build_poisson_distribution(rate(0.0))
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.PROBABILITY_SUM_INVALID

    monkeypatch.setattr(
        poisson_module,
        "poisson_pmf",
        lambda *_: CalculationError(ErrorCode.INVALID_LAMBDA, "bad"),
    )
    result = build_poisson_distribution(rate(0.0))
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.INVALID_LAMBDA


def test_constructor_rejects_rate_and_non_finite_residual() -> None:
    with pytest.raises(CalculationError, match="rate"):
        PoissonDistribution(0.0, (1.0,), 0, 1.0, 0.0, True)  # type: ignore[arg-type]
    with pytest.raises(CalculationError, match="finite"):
        PoissonDistribution(rate(0.0), (1.0,), 0, 1.0, float("nan"), True)
