import math

from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.core import CalculationError
from lvfi_pricing.models.method_one import (
    MethodOneAdjustedRateResult,
    MethodOneMultiplierCandidate,
    MultiplierAppliesTo,
    MultiplierCategory,
    MultiplierScope,
    apply_method_one_multipliers,
    resolve_method_one_multipliers,
)
from lvfi_pricing.models.samples import MatchPeriodCode, StatisticCode
from tests.unit.models.method_one.test_base_rates import averages, result
from tests.unit.models.method_one.test_multipliers import candidate

VALID = st.floats(min_value=0.9, max_value=1.1, allow_nan=False, allow_infinity=False)
RATE = st.floats(min_value=0.0, max_value=1e100, allow_nan=False, allow_infinity=False)
INVALID = st.one_of(
    st.floats(max_value=0.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=1.1000000001, allow_nan=False, allow_infinity=False),
    st.just(float("nan")),
    st.just(float("inf")),
    st.booleans(),
)


def resolve(values: tuple[object, ...]) -> object:
    return resolve_method_one_multipliers(
        values,  # type: ignore[arg-type]
        match_id="target",
        competition_id="competition",
        statistic=StatisticCode.GOALS,
        period=MatchPeriodCode.REGULATION_TIME,
    )


@given(VALID, VALID, VALID)
def test_precedence_is_permutation_invariant_and_selects_one(
    global_value: float, competition_value: float, match_value: float
) -> None:
    values = (
        candidate(value=global_value),
        candidate(value=competition_value, scope=MultiplierScope.COMPETITION),
        candidate(value=match_value, scope=MultiplierScope.MATCH),
    )
    first = resolve(values)
    second = resolve(tuple(reversed(values)))
    assert isinstance(first, tuple)
    assert first == second
    selected = [item for item in first if item.selected is not None]
    assert len(selected) == 1
    assert selected[0].selected is values[2]


@given(RATE, RATE, VALID, VALID)
def test_valid_application_is_finite_deterministic_and_does_not_mutate_inputs(
    home_rate: float, away_rate: float, home_factor: float, away_factor: float
) -> None:
    source = averages((home_rate, away_rate, away_rate, home_rate))
    base = result(source)
    inputs = (
        candidate(MultiplierCategory.RECENT_FORM, home_factor),
        candidate(
            MultiplierCategory.RECENT_FORM,
            away_factor,
            applies_to=MultiplierAppliesTo.AWAY,
        ),
    )
    before = tuple(inputs)
    resolutions = resolve(inputs)
    assert isinstance(resolutions, tuple)
    first = apply_method_one_multipliers(base, resolutions)
    second = apply_method_one_multipliers(base, resolutions)
    assert isinstance(first, MethodOneAdjustedRateResult)
    assert first == second
    assert math.isfinite(first.home_adjusted_rate)
    assert math.isfinite(first.away_adjusted_rate)
    assert inputs == before
    assert first.quality is base.quality


@given(RATE, RATE)
def test_absence_is_neutral_and_preserves_base_rates(
    home_rate: float, away_rate: float
) -> None:
    base = result(averages((home_rate, away_rate, away_rate, home_rate)))
    resolutions = resolve(())
    assert isinstance(resolutions, tuple)
    adjusted = apply_method_one_multipliers(base, resolutions)
    assert isinstance(adjusted, MethodOneAdjustedRateResult)
    assert adjusted.home_adjusted_rate == base.home_base_rate
    assert adjusted.away_adjusted_rate == base.away_base_rate


@given(INVALID)
def test_invalid_multiplier_values_are_always_rejected(value: object) -> None:
    created = MethodOneMultiplierCandidate.create(
        category=MultiplierCategory.RECENT_FORM,
        value=value,
        scope=MultiplierScope.GLOBAL,
        applies_to=MultiplierAppliesTo.HOME,
        statistic=StatisticCode.GOALS,
        period=MatchPeriodCode.REGULATION_TIME,
        catalog_order=30,
        catalog_version="lvfi-method-one-adjustments@1.0.0",
        source="source",
        justification="reason",
    )
    assert isinstance(created, CalculationError)
