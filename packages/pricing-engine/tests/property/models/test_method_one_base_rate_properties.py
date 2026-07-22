import math

from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.models.method_one import (
    MethodOneBaseRateResult,
    MethodOneConfiguration,
    MethodOneWeightConfiguration,
    calculate_method_one_base_rates,
)
from tests.unit.models.method_one.test_base_rates import averages

FINITE = st.floats(min_value=0, max_value=1e100, allow_nan=False, allow_infinity=False)
WEIGHT = st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)


@given(FINITE, FINITE, FINITE, FINITE, WEIGHT, WEIGHT)
def test_formula_envelope_determinism_and_immutable_inputs(
    home_production: float,
    home_concession: float,
    away_production: float,
    away_concession: float,
    home_weight: float,
    away_weight: float,
) -> None:
    source = averages(
        (home_production, home_concession, away_production, away_concession)
    )
    configuration = MethodOneConfiguration(
        "property",
        MethodOneWeightConfiguration(home_weight, 1.0 - home_weight),
        MethodOneWeightConfiguration(away_weight, 1.0 - away_weight),
    )
    first = calculate_method_one_base_rates(source, configuration)
    second = calculate_method_one_base_rates(source, configuration)
    assert isinstance(first, MethodOneBaseRateResult)
    assert first == second
    assert first.home_base_rate == math.fsum(
        (
            source.home_production.value * home_weight,
            source.away_concession.value * (1.0 - home_weight),
        )
    )
    assert first.away_base_rate == math.fsum(
        (
            source.away_production.value * away_weight,
            source.home_concession.value * (1.0 - away_weight),
        )
    )
    for rate, left, right in (
        (
            first.home_base_rate,
            source.home_production.value,
            source.away_concession.value,
        ),
        (
            first.away_base_rate,
            source.away_production.value,
            source.home_concession.value,
        ),
    ):
        lower, upper = min(left, right), max(left, right)
        assert (
            lower <= rate <= upper
            or math.isclose(rate, lower, rel_tol=1e-12, abs_tol=1e-12)
            or math.isclose(rate, upper, rel_tol=1e-12, abs_tol=1e-12)
        )
    assert source == averages(
        (home_production, home_concession, away_production, away_concession)
    )


@given(FINITE, FINITE, FINITE, FINITE)
def test_half_and_extreme_weights_have_expected_identities(
    home_production: float,
    home_concession: float,
    away_production: float,
    away_concession: float,
) -> None:
    source = averages(
        (home_production, home_concession, away_production, away_concession)
    )
    half = calculate_method_one_base_rates(source, MethodOneConfiguration("half"))
    own = calculate_method_one_base_rates(
        source,
        MethodOneConfiguration(
            "own",
            MethodOneWeightConfiguration(1.0, 0.0),
            MethodOneWeightConfiguration(1.0, 0.0),
        ),
    )
    opponent = calculate_method_one_base_rates(
        source,
        MethodOneConfiguration(
            "opponent",
            MethodOneWeightConfiguration(0.0, 1.0),
            MethodOneWeightConfiguration(0.0, 1.0),
        ),
    )
    assert isinstance(half, MethodOneBaseRateResult)
    assert isinstance(own, MethodOneBaseRateResult)
    assert isinstance(opponent, MethodOneBaseRateResult)
    assert half.home_base_rate == math.fsum(
        (source.home_production.value * 0.5, source.away_concession.value * 0.5)
    )
    assert half.away_base_rate == math.fsum(
        (source.away_production.value * 0.5, source.home_concession.value * 0.5)
    )
    assert (own.home_base_rate, own.away_base_rate) == (
        source.home_production.value,
        source.away_production.value,
    )
    assert (opponent.home_base_rate, opponent.away_base_rate) == (
        source.away_concession.value,
        source.home_concession.value,
    )
