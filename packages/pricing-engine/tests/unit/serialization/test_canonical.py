from collections.abc import Mapping
from types import MappingProxyType

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.domain import Probability
from lvfi_pricing.serialization import to_canonical_value


def test_primitives_and_float_are_typed_and_immutable() -> None:
    assert to_canonical_value(None) is None
    assert to_canonical_value(True) is True
    assert to_canonical_value(-2) == -2
    assert to_canonical_value("ação") == "ação"
    assert to_canonical_value(-0.0) == {"type": "Float", "value": "0x0.0p+0"}


def test_tuple_mapping_and_contract_are_canonical() -> None:
    mapping = MappingProxyType({"z": 2, "a": 1})
    canonical = to_canonical_value((mapping, Probability(0.5), "x"))
    assert not isinstance(canonical, CalculationError)
    assert isinstance(canonical, Mapping)
    assert canonical["type"] == "Tuple"
    items = canonical["items"]
    assert isinstance(items, tuple)
    first, second, _ = items
    assert isinstance(first, Mapping)
    assert isinstance(first["entries"], Mapping)
    assert first["entries"] == {"a": 1, "z": 2}
    assert isinstance(second, Mapping)
    assert second["type"] == "Probability"


def test_enum_and_nested_rejections_are_typed() -> None:
    enum_value = to_canonical_value(ErrorCode.INVALID_NUMBER)
    assert not isinstance(enum_value, CalculationError)
    assert isinstance(enum_value, Mapping)
    assert enum_value["enum"] == "ErrorCode"
    for value in (
        (object(),),
        MappingProxyType({"x": object()}),
        MappingProxyType({1: 1}),
    ):
        assert isinstance(to_canonical_value(value), CalculationError)

    invalid_probability = object.__new__(Probability)
    object.__setattr__(invalid_probability, "value", float("nan"))
    assert isinstance(to_canonical_value(invalid_probability), CalculationError)


def test_rejects_non_finite_mutable_and_unknown_values() -> None:
    for value in (float("nan"), float("inf"), {}, [], b"x", object()):
        result = to_canonical_value(value)
        assert isinstance(result, CalculationError)
    nan_result = to_canonical_value(float("nan"))
    assert isinstance(nan_result, CalculationError)
    assert nan_result.code is ErrorCode.INVALID_NUMBER
