"""Executor e comparação recursiva determinísticos para fixtures."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy, is_close

from .fixtures import Fixture, SafeFixtureValue

_DEFAULT_POLICY = NumericPolicy()


class DifferenceKind(StrEnum):
    VALUE = "value"
    TYPE = "type"
    MISSING = "missing"
    EXTRA = "extra"
    LENGTH = "length"


@dataclass(frozen=True, slots=True)
class RegressionDifference:
    path: str
    expected: SafeFixtureValue
    actual: SafeFixtureValue
    reason: DifferenceKind


@dataclass(frozen=True, slots=True)
class RegressionResult:
    fixture_id: str
    passed: bool
    differences: tuple[RegressionDifference, ...] = ()
    errors: tuple[CalculationError, ...] = ()
    warnings: tuple[CalculationWarning, ...] = ()


Executor = Callable[[Fixture], Mapping[str, SafeFixtureValue] | CalculationError]


def _compare(
    expected: SafeFixtureValue,
    actual: object,
    path: str,
    policy: NumericPolicy,
    out: list[RegressionDifference],
) -> None:
    if isinstance(expected, bool):
        if not isinstance(actual, bool) or expected != actual:
            out.append(
                RegressionDifference(
                    path,
                    expected,
                    _safe_or_none(actual),
                    DifferenceKind.TYPE
                    if not isinstance(actual, bool)
                    else DifferenceKind.VALUE,
                )
            )
        return
    if expected is None or isinstance(expected, (int, str)):
        if type(expected) is not type(actual) or expected != actual:
            out.append(
                RegressionDifference(
                    path,
                    expected,
                    _safe_or_none(actual),
                    DifferenceKind.TYPE
                    if type(expected) is not type(actual)
                    else DifferenceKind.VALUE,
                )
            )
        return
    if isinstance(expected, float):
        if (
            not isinstance(actual, float)
            or not math.isfinite(actual)
            or not is_close(expected, actual, policy)
        ):
            out.append(
                RegressionDifference(
                    path,
                    expected,
                    _safe_or_none(actual),
                    DifferenceKind.TYPE
                    if not isinstance(actual, float)
                    else DifferenceKind.VALUE,
                )
            )
        return
    if isinstance(expected, tuple):
        if not isinstance(actual, tuple):
            out.append(
                RegressionDifference(
                    path,
                    expected,
                    _safe_or_none(actual),
                    DifferenceKind.TYPE,
                )
            )
            return
        if len(expected) != len(actual):
            out.append(
                RegressionDifference(path, expected, actual, DifferenceKind.LENGTH)
            )
        for index, item in enumerate(expected[: len(actual)]):
            _compare(item, actual[index], f"{path}[{index}]", policy, out)
        return
    # SafeFixtureValue is exhausted above; only a mapping remains here.
    if not isinstance(actual, Mapping):
        out.append(
            RegressionDifference(
                path,
                expected,
                _safe_or_none(actual),
                DifferenceKind.TYPE,
            )
        )
        return
    expected_keys = set(expected)
    actual_keys = set(actual)
    for key in sorted(expected_keys - actual_keys):
        out.append(
            RegressionDifference(
                f"{path}.{key}", expected[key], None, DifferenceKind.MISSING
            )
        )
    for key in sorted(actual_keys - expected_keys):
        out.append(
            RegressionDifference(
                f"{path}.{key}",
                None,
                _safe_or_none(actual[key]),
                DifferenceKind.EXTRA,
            )
        )
    for key in sorted(expected_keys & actual_keys):
        _compare(expected[key], actual[key], f"{path}.{key}", policy, out)


def _safe(value: object) -> bool:
    if value is None or isinstance(value, (bool, int, str)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, tuple):
        return all(_safe(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _safe(item) for key, item in value.items())
    return False


def _safe_or_none(value: object) -> SafeFixtureValue:
    return cast(SafeFixtureValue, value) if _safe(value) else None


def run_regression(
    fixture: Fixture, executor: Executor, policy: NumericPolicy = _DEFAULT_POLICY
) -> RegressionResult:
    """Executa uma fixture sem I/O e totaliza diferenças em ordem estável."""
    try:
        actual = executor(fixture)
    except CalculationError as error:
        return RegressionResult(fixture.fixture_id, False, errors=(error,))
    except Exception:
        unexpected_error = CalculationError(
            ErrorCode.CONFIGURATION_ERROR,
            "executor raised an unexpected exception",
            context={"exception": "unexpected"},
        )
        return RegressionResult(fixture.fixture_id, False, errors=(unexpected_error,))
    if isinstance(actual, CalculationError):
        return RegressionResult(fixture.fixture_id, False, errors=(actual,))
    if not isinstance(actual, Mapping) or not _safe(actual):
        unsafe_error = CalculationError(
            ErrorCode.SERIALIZATION_ERROR, "executor returned an unsafe result"
        )
        return RegressionResult(fixture.fixture_id, False, errors=(unsafe_error,))
    differences: list[RegressionDifference] = []
    _compare(fixture.expected, actual, "$", policy, differences)
    return RegressionResult(fixture.fixture_id, not differences, tuple(differences))
