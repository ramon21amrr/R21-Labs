"""Testes unitários da matriz auditável de placares."""

import math
from dataclasses import FrozenInstanceError

import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy
from lvfi_pricing.distributions import (
    PoissonDistribution,
    ScoreProbabilityMatrix,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.distributions import score_matrix as matrix_module
from lvfi_pricing.domain import PoissonRate


def distribution(value: float) -> PoissonDistribution:
    rate = PoissonRate.create(value)
    assert isinstance(rate, PoissonRate)
    result = build_poisson_distribution(rate)
    assert isinstance(result, PoissonDistribution)
    return result


@pytest.mark.parametrize(
    ("home_rate", "away_rate"),
    [
        (0.0, 0.0),
        (0.0, 1.5),
        (1.5, 0.0),
        (0.5, 0.5),
        (1.5, 1.0),
        (2.5, 1.2),
        (5.0, 3.0),
        (10.0, 10.0),
    ],
)
def test_matrix_reference_cases(home_rate: float, away_rate: float) -> None:
    home = distribution(home_rate)
    away = distribution(away_rate)
    matrix = build_score_probability_matrix(home, away)
    assert isinstance(matrix, ScoreProbabilityMatrix)
    assert matrix.home_max_goals == home.max_count
    assert matrix.away_max_goals == away.max_count
    assert matrix.probabilities[0][0] == home.probabilities[0] * away.probabilities[0]
    assert math.isclose(
        matrix.total_probability,
        home.cumulative_probability * away.cumulative_probability,
        abs_tol=1e-12,
    )
    assert math.isclose(
        matrix.residual_mass,
        home.residual_mass
        + away.residual_mass
        - home.residual_mass * away.residual_mass,
        abs_tol=1e-12,
    )
    assert all(
        math.isfinite(cell) and cell >= 0.0
        for row in matrix.probabilities
        for cell in row
    )


def test_matrix_access_immutability_and_determinism() -> None:
    matrix = build_score_probability_matrix(distribution(1.0), distribution(1.5))
    assert isinstance(matrix, ScoreProbabilityMatrix)
    assert matrix.probability_at(1, 1) == matrix.probabilities[1][1]
    for home, away in ((-1, 0), (True, 0), (0, "1"), (100, 0)):
        result = matrix.probability_at(home, away)
        assert isinstance(result, CalculationError)
        assert result.code is ErrorCode.INVALID_NUMBER
    with pytest.raises(FrozenInstanceError):
        matrix.total_probability = 1.0  # type: ignore[misc]
    with pytest.raises(TypeError):
        matrix.probabilities[0][0] = 1.0  # type: ignore[index]
    assert matrix == build_score_probability_matrix(
        distribution(1.0), distribution(1.5)
    )


def test_matrix_rejects_invalid_inputs_and_distribution_contracts() -> None:
    valid = distribution(0.0)
    for home, away, code in (
        (object(), valid, ErrorCode.CONFIGURATION_ERROR),
        (valid, object(), ErrorCode.CONFIGURATION_ERROR),
        (valid, valid, ErrorCode.CONFIGURATION_ERROR),
    ):
        policy = object() if home is valid and away is valid else NumericPolicy()
        result = build_score_probability_matrix(home, away, policy)  # type: ignore[arg-type]
        assert isinstance(result, CalculationError)
        assert result.code is code
    inconsistent = PoissonDistribution(valid.rate, (1.0,), 0, 0.5, 0.5, True)
    result = build_score_probability_matrix(inconsistent, valid)
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.RESIDUAL_MASS_EXCEEDED


def test_matrix_constructor_rejects_inconsistent_contract() -> None:
    home = distribution(0.0)
    away = distribution(0.0)
    with pytest.raises(CalculationError, match="matrix limits"):
        ScoreProbabilityMatrix(home, away, ((1.0,),), 1, 0, 1.0, 0.0)
    with pytest.raises(CalculationError, match="matrix dimensions"):
        ScoreProbabilityMatrix(home, away, ((1.0,),) * 11, 10, 10, 1.0, 0.0)


def test_matrix_validation_failure_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    valid = distribution(0.0)
    unconverged = PoissonDistribution(valid.rate, (1.0,), 0, 1.0, 0.0, False)
    inconsistent_total = PoissonDistribution(valid.rate, (1.0,), 0, 0.5, 0.5, True)
    for invalid in (unconverged, inconsistent_total):
        result = build_score_probability_matrix(invalid, valid)
        assert isinstance(result, CalculationError)
    inconsistent_residual = PoissonDistribution(valid.rate, (1.0,), 0, 1.0, 0.5, True)
    result = build_score_probability_matrix(
        inconsistent_residual,
        valid,
        NumericPolicy(probability_sum_tolerance=0.0, poisson_residual_tolerance=0.5),
    )
    assert isinstance(result, CalculationError)
    probabilities = ((2.0, -1.0) + (0.0,) * 9,) + ((0.0,) * 11,) * 10
    with pytest.raises(CalculationError, match="matrix cells must"):
        ScoreProbabilityMatrix(valid, valid, probabilities, 10, 10, 1.0, 0.0)
    probabilities = ((0.9, 0.1) + (0.0,) * 9,) + ((0.0,) * 11,) * 10
    with pytest.raises(CalculationError, match="matrix cells are"):
        ScoreProbabilityMatrix(valid, valid, probabilities, 10, 10, 1.0, 0.0)
    base = ((1.0,) + (0.0,) * 10,) + ((0.0,) * 11,) * 10
    with pytest.raises(CalculationError, match="warnings"):
        ScoreProbabilityMatrix(valid, valid, base, 10, 10, 1.0, 0.0, (object(),))  # type: ignore[arg-type]
    with pytest.raises(CalculationError, match="matrix total"):
        ScoreProbabilityMatrix(valid, valid, base, 10, 10, float("nan"), 0.0)
    with pytest.raises(CalculationError, match="matrix mass"):
        ScoreProbabilityMatrix(valid, valid, base, 10, 10, 0.5, 0.5)
    with pytest.raises(CalculationError, match="distribution must converge"):
        ScoreProbabilityMatrix(unconverged, valid, base, 10, 10, 1.0, 0.0)
    monkeypatch.setattr(
        matrix_module,
        "stable_sum",
        lambda _: CalculationError(ErrorCode.INVALID_NUMBER, "bad"),
    )
    result = build_score_probability_matrix(valid, valid)
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.PROBABILITY_SUM_INVALID
    monkeypatch.setattr(matrix_module, "_valid_distribution", lambda *_: None)
    result = build_score_probability_matrix(valid, valid)
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.PROBABILITY_SUM_INVALID
    monkeypatch.setattr(matrix_module, "stable_sum", lambda _: 2.0)
    result = build_score_probability_matrix(valid, valid)
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.RESIDUAL_MASS_EXCEEDED
