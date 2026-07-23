from importlib.metadata import version

from lvfi_pricing.engine.contracts import PACKAGE_VERSION
from lvfi_pricing.models.method_one import MethodOnePricingResult, MethodOneRequest
from lvfi_pricing.models.samples import SampleSnapshot


def test_independent_version_axes() -> None:
    assert version("lvfi-pricing-engine") == "1.1.0a9"
    assert PACKAGE_VERSION == "1.0.0"
    assert SampleSnapshot.__dataclass_fields__["sample_schema_version"].default == 1
    assert MethodOneRequest.__dataclass_fields__["request_schema_version"].default == 2
    assert (
        MethodOnePricingResult.__dataclass_fields__[
            "integration_schema_version"
        ].default
        == 1
    )

