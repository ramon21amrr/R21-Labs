from itertools import permutations

from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.core import CalculationError
from lvfi_pricing.models.method_one import (
    MethodOneWeightConfiguration,
)
from tests.unit.models.method_one.test_contracts import request


@given(st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False))
def test_valid_weight_pairs_are_deterministic(weight: float) -> None:
    value = MethodOneWeightConfiguration.create(
        weight_own=weight, weight_opponent=1 - weight
    )
    assert isinstance(value, MethodOneWeightConfiguration)
    assert value == MethodOneWeightConfiguration(
        value.weight_own, value.weight_opponent
    )


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_invalid_or_nonfinite_weight_values_return_errors(value: float) -> None:
    result = MethodOneWeightConfiguration.create(weight_own=value, weight_opponent=0.5)
    if (
        value < 0
        or value > 1
        or value != value
        or value in (float("inf"), float("-inf"))
    ):
        assert isinstance(result, CalculationError)


def test_series_permutations_canonicalize_to_same_order() -> None:
    baseline = request()
    references = baseline.series_references
    for permuted in permutations(references):
        rebuilt = type(baseline)(
            baseline.match_id,
            baseline.home_team_id,
            baseline.away_team_id,
            baseline.statistic,
            baseline.period,
            permuted,
            baseline.configuration,
            baseline.competition_id,
            baseline.data_cutoff_at,
        )
        assert rebuilt.series_references == references


def test_request_does_not_mutate_its_input_tuple() -> None:
    value = request()
    original = tuple(reversed(value.series_references))
    rebuilt = type(value)(
        value.match_id,
        value.home_team_id,
        value.away_team_id,
        value.statistic,
        value.period,
        original,
        value.configuration,
        value.competition_id,
        value.data_cutoff_at,
    )
    assert original == tuple(reversed(value.series_references))
    assert rebuilt.series_references == value.series_references
