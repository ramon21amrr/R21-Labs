import dataclasses
from pathlib import Path
from typing import cast

import pytest

from lvfi_pricing.core.errors import CalculationError, ErrorCode
from lvfi_pricing.testing import (
    FIXTURE_SCHEMA_VERSION,
    SYNTHETIC_FIXTURES,
    Fixture,
    FixtureCategory,
)
from lvfi_pricing.testing.fixtures import SafeFixtureValue


def test_valid_fixture_is_immutable_and_freezes_mappings() -> None:
    fixture = Fixture(
        "case_001", "safe", FixtureCategory.SMOKE, {"x": (True, 0.1)}, {"ok": True}, {}
    )
    assert fixture.inputs["x"] == (True, 0.1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        fixture.fixture_id = "other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        fixture.inputs["x"] = ()  # type: ignore[index]


@pytest.mark.parametrize("fixture_id", ["", "UPPER", "has space", "../path", "équipe"])
def test_invalid_fixture_id_returns_typed_error(fixture_id: str) -> None:
    result = Fixture.create(fixture_id, "safe", FixtureCategory.SMOKE, {}, {})
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.INVALID_STATISTIC


def test_schema_category_and_safe_value_rules() -> None:
    result = Fixture.create(
        "case_001", "safe", FixtureCategory.SMOKE, {}, {}, schema_version=2
    )
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.SCHEMA_VERSION_UNSUPPORTED
    assert FIXTURE_SCHEMA_VERSION == 1
    for value in [[1], {1}, Path("local"), float("nan"), float("inf"), object()]:
        with pytest.raises(TypeError):
            Fixture(
                "case_001",
                "safe",
                FixtureCategory.SMOKE,
                cast(dict[str, SafeFixtureValue], {"value": value}),
                {},
                {},
            )


def test_constructor_rejects_invalid_contract_fields() -> None:
    with pytest.raises(ValueError):
        Fixture("", "safe", FixtureCategory.SMOKE, {}, {}, {})
    with pytest.raises(TypeError):
        Fixture("case_001", "", FixtureCategory.SMOKE, {}, {}, {})
    with pytest.raises(ValueError):
        Fixture("case_001", "safe", FixtureCategory.SMOKE, {}, {}, {}, 2)


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"category": "smoke"}, ErrorCode.INVALID_STATISTIC),
        ({"inputs": []}, ErrorCode.INVALID_STATISTIC),
        ({"expected": []}, ErrorCode.INVALID_STATISTIC),
        ({"metadata": []}, ErrorCode.INVALID_STATISTIC),
        ({"schema_version": "1"}, ErrorCode.SCHEMA_VERSION_UNSUPPORTED),
    ],
)
def test_factory_rejects_invalid_contract_shapes(
    kwargs: dict[str, object], code: ErrorCode
) -> None:
    arguments: dict[str, object] = {
        "fixture_id": "case_001",
        "description": "safe",
        "category": FixtureCategory.SMOKE,
        "inputs": {},
        "expected": {},
    }
    arguments.update(kwargs)
    result = Fixture.create(**arguments)
    assert isinstance(result, CalculationError)
    assert result.code is code


def test_factory_freezes_nested_values_and_metadata() -> None:
    result = Fixture.create(
        "case_001",
        "safe",
        FixtureCategory.BOUNDARY,
        {
            "nested": {
                "none": None,
                "bool": True,
                "int": 1,
                "float": 0.1,
                "text": "x",
                "tuple": (1,),
            }
        },
        {"valid": True},
        {"public": "synthetic"},
    )
    assert isinstance(result, Fixture)
    assert result.metadata["public"] == "synthetic"
    assert result.inputs["nested"] == {
        "none": None,
        "bool": True,
        "int": 1,
        "float": 0.1,
        "text": "x",
        "tuple": (1,),
    }


def test_factory_rejects_mapping_with_non_string_key() -> None:
    result = Fixture.create("case_001", "safe", FixtureCategory.SMOKE, {1: "bad"}, {})
    assert isinstance(result, CalculationError)
    assert result.code is ErrorCode.INVALID_STATISTIC


def test_no_coercion_and_categories_are_stable() -> None:
    with pytest.raises(TypeError):
        Fixture("case_001", "safe", "smoke", {}, {}, {})  # type: ignore[arg-type]
    fixture = Fixture("case_001", "safe", FixtureCategory.SMOKE, {"value": "1"}, {}, {})
    assert fixture.inputs["value"] == "1"
    assert [category.value for category in FixtureCategory] == [
        "smoke",
        "boundary",
        "regression",
        "invalid_input",
    ]


def test_synthetic_catalog_is_exactly_eight_safe_and_deterministic() -> None:
    assert len(SYNTHETIC_FIXTURES) == 8
    assert [fixture.fixture_id for fixture in SYNTHETIC_FIXTURES] == [
        "fixture_zero",
        "fixture_empty",
        "fixture_balanced",
        "fixture_home_edge",
        "fixture_away_edge",
        "fixture_boundary",
        "fixture_decimal",
        "fixture_invalid",
    ]
    assert len({fixture.fixture_id for fixture in SYNTHETIC_FIXTURES}) == 8
    assert all(fixture.schema_version == 1 for fixture in SYNTHETIC_FIXTURES)
    assert all(
        "\\" not in fixture.fixture_id and "/" not in fixture.fixture_id
        for fixture in SYNTHETIC_FIXTURES
    )
