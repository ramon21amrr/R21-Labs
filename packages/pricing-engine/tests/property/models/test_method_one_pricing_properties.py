import math

from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.core import CalculationError
from lvfi_pricing.engine import PricingResult, run_pricing_engine
from lvfi_pricing.models.method_one import (
    build_method_one_pricing_request,
    price_method_one,
)
from tests.unit.models.method_one.test_pricing import adjusted

RATE = st.floats(min_value=0.0, max_value=3.0, allow_nan=False, allow_infinity=False)


@given(RATE, RATE)
def test_valid_rates_are_preserved_and_match_direct_engine(
    home: float, away: float
) -> None:
    source = adjusted()
    object.__setattr__(source, "home_adjusted_rate", home)
    object.__setattr__(source, "away_adjusted_rate", away)
    object.__setattr__(source.explanation, "home_adjusted_rate", home)
    object.__setattr__(source.explanation, "away_adjusted_rate", away)
    request = build_method_one_pricing_request(source)
    priced = price_method_one(source)
    assert not isinstance(request, CalculationError)
    assert not isinstance(priced, CalculationError)
    assert request.home_rate.value == (0.0 if home == 0 else home)
    assert request.away_rate.value == (0.0 if away == 0 else away)
    direct = run_pricing_engine(request)
    assert isinstance(direct, PricingResult)
    assert priced.pricing_result == direct
    assert source.home_adjusted_rate == home
    assert source.away_adjusted_rate == away
    assert math.isfinite(priced.home_poisson_rate.value)


@given(RATE, RATE)
def test_request_and_pricing_are_deterministic(home: float, away: float) -> None:
    source = adjusted()
    for field, value in (("home_adjusted_rate", home), ("away_adjusted_rate", away)):
        object.__setattr__(source, field, value)
        object.__setattr__(source.explanation, field, value)
    first = build_method_one_pricing_request(source)
    second = build_method_one_pricing_request(source)
    priced_first = price_method_one(source)
    priced_second = price_method_one(source)
    assert first == second
    assert priced_first == priced_second
