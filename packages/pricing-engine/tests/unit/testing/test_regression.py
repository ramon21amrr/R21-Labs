from dataclasses import FrozenInstanceError

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy
from lvfi_pricing.testing import Fixture, FixtureCategory, run_regression
from lvfi_pricing.testing.regression import RegressionResult


def fixture(expected: dict[str, object]) -> Fixture:
    return Fixture("case_001", "safe", FixtureCategory.SMOKE, {}, expected, {})  # type: ignore[arg-type]


def test_pass_and_fail_with_recursive_differences() -> None:
    current = fixture({"a": 1, "nested": (True, 0.1), "same": "x"})
    assert run_regression(
        current, lambda _: {"a": 1, "nested": (True, 0.1), "same": "x"}
    ).passed
    result = run_regression(
        current, lambda _: {"a": "1", "nested": (1, 0.2), "extra": 3}
    )
    assert not result.passed
    assert [difference.path for difference in result.differences] == [
        "$.same",
        "$.extra",
        "$.a",
        "$.nested[0]",
        "$.nested[1]",
    ]


def test_missing_length_bool_and_float_policy() -> None:
    result = run_regression(
        fixture({"a": (1, 2), "b": True}), lambda _: {"a": (1,), "b": 1}
    )
    assert [difference.reason.value for difference in result.differences] == [
        "length",
        "type",
    ]
    policy = NumericPolicy(0.1, 0.0, 1e-12, 1e-14)
    assert run_regression(
        fixture({"value": 1.0}), lambda _: {"value": 1.05}, policy
    ).passed
    assert not run_regression(
        fixture({"value": 1.0}), lambda _: {"value": 1.2}, policy
    ).passed


def test_tuple_and_mapping_type_mismatches_are_reported() -> None:
    tuple_result = run_regression(fixture({"value": (1,)}), lambda _: {"value": 1})
    mapping_result = run_regression(
        fixture({"value": {"a": 1}}), lambda _: {"value": (1,)}
    )
    assert tuple_result.differences[0].reason.value == "type"
    assert mapping_result.differences[0].reason.value == "type"


def test_typed_and_unexpected_executor_errors_and_unsafe_result() -> None:
    typed = CalculationError(ErrorCode.INVALID_STATISTIC, "invalid")
    assert run_regression(fixture({}), lambda _: typed).errors == (typed,)
    assert run_regression(
        fixture({}), lambda _: (_ for _ in ()).throw(typed)
    ).errors == (typed,)
    unexpected = run_regression(fixture({}), lambda _: 1)  # type: ignore[arg-type, return-value]
    assert unexpected.errors[0].code is ErrorCode.SERIALIZATION_ERROR
    raised = run_regression(
        fixture({}), lambda _: (_ for _ in ()).throw(RuntimeError())
    )
    assert raised.errors[0].code is ErrorCode.CONFIGURATION_ERROR
    unsafe = run_regression(
        fixture({}),
        lambda _: {"bad": [1]},  # type: ignore[dict-item]
    )
    assert unsafe.errors[0].code is ErrorCode.SERIALIZATION_ERROR


def test_unsafe_nested_result_and_warnings_are_typed() -> None:
    unsafe = run_regression(
        fixture({"value": (1,)}), lambda _: {"value": (float("nan"),)}
    )
    assert unsafe.errors[0].code is ErrorCode.SERIALIZATION_ERROR
    warning = CalculationWarning(ErrorCode.INVALID_STATISTIC, "synthetic warning")
    result = RegressionResult("case_001", True, warnings=(warning,))
    assert result.warnings == (warning,)


def test_repeatability_and_result_immutability() -> None:
    current = fixture({"a": 1})
    first = run_regression(current, lambda _: {"a": 2})
    second = run_regression(current, lambda _: {"a": 2})
    assert first == second
    try:
        first.passed = True  # type: ignore[misc]
    except FrozenInstanceError:
        pass
