from hypothesis import given
from hypothesis import strategies as st

from lvfi_pricing.models.method_one import (
    MethodOneFinalResult,
    MethodOneMultiplierCandidate,
    MultiplierCategory,
    run_method_one,
)
from tests.unit.models.method_one.test_multipliers import candidate
from tests.unit.models.method_one.test_orchestration import request

_CANDIDATES = (
    candidate(),
    candidate(MultiplierCategory.MATCH_PACE, 0.95),
)


@given(st.permutations(_CANDIDATES))
def test_candidate_permutations_are_deterministic(
    candidates: list[MethodOneMultiplierCandidate],
) -> None:
    value = run_method_one(request(), tuple(candidates))
    baseline = run_method_one(request(), _CANDIDATES)
    assert isinstance(value, MethodOneFinalResult)
    assert value == baseline
