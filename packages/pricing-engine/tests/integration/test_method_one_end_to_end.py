import pytest

from lvfi_pricing.models.method_one import (
    MethodOneFinalResult,
    MethodOnePublicationState,
    run_method_one,
)
from tests.unit.models.method_one.test_multipliers import candidate
from tests.unit.models.method_one.test_orchestration import request


@pytest.mark.parametrize("count", (10, 5, 1))
def test_method_one_end_to_end_with_synthetic_samples(count: int) -> None:
    value = run_method_one(request(count), (candidate(),))
    assert isinstance(value, MethodOneFinalResult)
    assert value.pricing.pricing_result.request == value.pricing.pricing_request
    assert value.explanation.adjusted_rates is value.adjusted_rates
    assert value.publication_state in (
        MethodOnePublicationState.PUBLISHABLE,
        MethodOnePublicationState.CONDITIONAL,
        MethodOnePublicationState.AUDIT_ONLY,
    )
