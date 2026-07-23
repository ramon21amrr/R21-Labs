from lvfi_pricing.core import CalculationError
from lvfi_pricing.models.method_one import (
    MethodOneAdjustedRateResult,
    MultiplierAppliesTo,
    MultiplierCategory,
    apply_method_one_multipliers,
    price_method_one,
    resolve_method_one_multipliers,
)
from lvfi_pricing.models.samples import MatchPeriodCode, StatisticCode
from tests.unit.models.method_one.test_base_rates import result
from tests.unit.models.method_one.test_multipliers import candidate


def integrated(
    period: MatchPeriodCode, with_multiplier: bool
) -> MethodOneAdjustedRateResult:
    base = result()
    object.__setattr__(base, "period", period)
    candidates = (
        (
            candidate(
                MultiplierCategory.HOME_FIELD_ADVANTAGE,
                1.1,
                applies_to=MultiplierAppliesTo.HOME,
                period=period,
            ),
        )
        if with_multiplier
        else ()
    )
    resolutions = resolve_method_one_multipliers(
        candidates,
        match_id=base.match_id,
        competition_id=base.competition_id,
        statistic=StatisticCode.GOALS,
        period=period,
    )
    assert isinstance(resolutions, tuple)
    value = apply_method_one_multipliers(base, resolutions)
    assert isinstance(value, MethodOneAdjustedRateResult)
    return value


def test_end_to_end_regulation_and_first_half_are_priced() -> None:
    regulation = integrated(MatchPeriodCode.REGULATION_TIME, False)
    first_half = integrated(MatchPeriodCode.FIRST_HALF, True)
    regulation_priced = price_method_one(regulation)
    first_half_priced = price_method_one(first_half)
    assert not isinstance(regulation_priced, CalculationError)
    assert not isinstance(first_half_priced, CalculationError)
    assert regulation_priced.period is MatchPeriodCode.REGULATION_TIME
    assert first_half_priced.period is MatchPeriodCode.FIRST_HALF
    assert first_half_priced.home_poisson_rate.value == first_half.home_adjusted_rate
    assert first_half.home_adjusted_rate > first_half.home_base_rate
