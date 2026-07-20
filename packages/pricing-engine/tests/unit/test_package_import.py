from importlib import import_module
from types import ModuleType

import pytest


def test_package_import(capsys: pytest.CaptureFixture[str]) -> None:
    module = import_module("lvfi_pricing")
    captured = capsys.readouterr()

    assert isinstance(module, ModuleType)
    assert module.__name__ == "lvfi_pricing"
    assert vars(module)["__all__"] == ()
    assert captured.out == ""
    assert captured.err == ""
