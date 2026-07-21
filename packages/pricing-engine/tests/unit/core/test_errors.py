from dataclasses import FrozenInstanceError

import pytest

from lvfi_pricing.core.errors import (
    CalculationError,
    CalculationWarning,
    ErrorCode,
    IssueSeverity,
)


def test_catalog_and_severity() -> None:
    expected = """SAMPLE_EMPTY SAMPLE_INSUFFICIENT MISSING_STATISTIC INVALID_STATISTIC
    INCONSISTENT_DATA INVALID_NUMBER INVALID_PROBABILITY INVALID_ODD
    FAIR_ODD_UNDEFINED INVALID_LAMBDA DIVISION_BY_ZERO INVALID_WEIGHT
    WEIGHTS_SUM_INVALID INVALID_MULTIPLIER CONFIGURATION_ERROR
    MODEL_NOT_APPLICABLE INVALID_MARKET UNSUPPORTED_MARKET INVALID_ASIAN_LINE
    NUMERIC_CONVERGENCE_FAILED PROBABILITY_SUM_INVALID RESIDUAL_MASS_EXCEEDED
    SCHEMA_VERSION_UNSUPPORTED SERIALIZATION_ERROR""".split()
    assert [item.name for item in ErrorCode] == expected
    assert [item.value for item in IssueSeverity] == ["info", "warning", "error"]


def test_issues_are_immutable_deterministic_and_safe() -> None:
    error = CalculationError(
        ErrorCode.INVALID_NUMBER, "bad", "x", {"b": 2, "a": "safe"}
    )
    assert error == CalculationError(
        ErrorCode.INVALID_NUMBER, "bad", "x", {"a": "safe", "b": 2}
    )
    assert (
        CalculationWarning(ErrorCode.INVALID_NUMBER, "check").severity
        is IssueSeverity.WARNING
    )
    assert dict(error.context) == {"a": "safe", "b": 2}
    with pytest.raises(FrozenInstanceError):
        error.message = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        error.context["x"] = 1  # type: ignore[index]
    with pytest.raises(TypeError):
        CalculationError(
            ErrorCode.INVALID_NUMBER,
            "bad",
            context={"object": object()},  # type: ignore[dict-item]
        )
    with pytest.raises(TypeError):
        CalculationError(ErrorCode.INVALID_NUMBER, "bad", context={"nan": float("nan")})
    with pytest.raises(TypeError):
        CalculationError(ErrorCode.INVALID_NUMBER, "bad", context={1: "bad"})  # type: ignore[dict-item]
    with pytest.raises(TypeError):
        CalculationError(ErrorCode.INVALID_NUMBER, "bad", context={"list": []})  # type: ignore[dict-item]
    assert CalculationError(
        ErrorCode.INVALID_NUMBER,
        "bad",
        context={"nested": {"x": 1}, "tuple": (True, None), "float": 1.0},
    )


def test_issue_field_validation() -> None:
    with pytest.raises(TypeError):
        CalculationError("invalid", "bad")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        CalculationError(ErrorCode.INVALID_NUMBER, 1)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        CalculationError(ErrorCode.INVALID_NUMBER, "bad", 1)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        CalculationWarning(ErrorCode.INVALID_NUMBER, "bad", severity="warning")  # type: ignore[arg-type]
