from typing import cast

from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.testing import Fixture, FixtureCategory, run_regression
from lvfi_pricing.testing.fixtures import SafeFixtureValue

safe_scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
)
safe_mappings = st.dictionaries(st.text(min_size=1), safe_scalars, max_size=4)


@given(safe_mappings)
def test_safe_mapping_comparison_is_reflexive(values: dict[str, object]) -> None:
    safe_values = cast(dict[str, SafeFixtureValue], values)
    fixture = Fixture("case_001", "safe", FixtureCategory.SMOKE, {}, safe_values, {})
    assert run_regression(fixture, lambda _: safe_values).passed


@given(safe_mappings)
def test_changed_safe_value_is_detected(values: dict[str, object]) -> None:
    values["stable_key"] = 1
    safe_values = cast(dict[str, SafeFixtureValue], values)
    fixture = Fixture("case_001", "safe", FixtureCategory.SMOKE, {}, safe_values, {})
    changed = {**safe_values, "stable_key": 2}
    assert not run_regression(fixture, lambda _: changed).passed


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_float_comparison_is_repeatable(value: float) -> None:
    fixture = Fixture(
        "case_001", "safe", FixtureCategory.SMOKE, {}, {"value": value}, {}
    )
    first = run_regression(fixture, lambda _: {"value": value})
    second = run_regression(fixture, lambda _: {"value": value})
    assert first == second and first.passed
