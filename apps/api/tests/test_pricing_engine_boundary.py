"""Guard the approved public-only Pricing Engine import boundary."""

from __future__ import annotations

import inspect

from lvfi_api.infrastructure import pricing_engine


def test_pricing_engine_boundary_imports_only_public_method_one_api() -> None:
    source = inspect.getsource(pricing_engine)

    assert pricing_engine.pricing_engine_is_available() is True
    assert "from lvfi_pricing.models.method_one import" in source
    assert "lvfi_pricing.models.method_one." not in source
    assert "run_method_one(" not in source.replace(
        "def pricing_engine_is_available", ""
    )
