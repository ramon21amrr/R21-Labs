"""Contratos e catálogo em memória de fixtures inteiramente sintéticas."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from lvfi_pricing.core.errors import CalculationError, ErrorCode

FIXTURE_SCHEMA_VERSION = 1
_FIXTURE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

type SafeFixtureValue = (
    None
    | bool
    | int
    | float
    | str
    | tuple["SafeFixtureValue", ...]
    | Mapping[str, "SafeFixtureValue"]
)


class FixtureCategory(StrEnum):
    """Categorias fechadas e estáveis; o valor público é minúsculo."""

    SMOKE = "smoke"
    BOUNDARY = "boundary"
    REGRESSION = "regression"
    INVALID_INPUT = "invalid_input"


def _freeze(value: object, path: str) -> SafeFixtureValue:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError(f"{path} must be finite")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, SafeFixtureValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} keys must be strings")
            frozen[key] = _freeze(item, f"{path}.{key}")
        return MappingProxyType(dict(sorted(frozen.items())))
    if isinstance(value, tuple):
        return tuple(
            _freeze(item, f"{path}[{index}]") for index, item in enumerate(value)
        )
    raise TypeError(f"{path} contains an unsupported value type")


def _invalid_fixture(field: str, message: str, value: object) -> CalculationError:
    return CalculationError(
        ErrorCode.INVALID_STATISTIC,
        message,
        field,
        {"value_type": type(value).__name__},
    )


@dataclass(frozen=True, slots=True)
class Fixture:
    """Fixture imutável, segura, sem I/O e com schema explícito."""

    fixture_id: str
    description: str
    category: FixtureCategory
    inputs: Mapping[str, SafeFixtureValue]
    expected: Mapping[str, SafeFixtureValue]
    metadata: Mapping[str, SafeFixtureValue]
    schema_version: int = FIXTURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.fixture_id, str) or not _FIXTURE_ID.fullmatch(
            self.fixture_id
        ):
            raise ValueError(
                "fixture_id must use lowercase letters, numbers, '-' or '_'"
            )
        if not isinstance(self.description, str) or not self.description:
            raise TypeError("description must be a non-empty string")
        if not isinstance(self.category, FixtureCategory):
            raise TypeError("category must be a FixtureCategory")
        if self.schema_version != FIXTURE_SCHEMA_VERSION:
            raise ValueError("unsupported fixture schema version")
        object.__setattr__(self, "inputs", _freeze(self.inputs, "inputs"))
        object.__setattr__(self, "expected", _freeze(self.expected, "expected"))
        object.__setattr__(self, "metadata", _freeze(self.metadata, "metadata"))

    @classmethod
    def create(
        cls,
        fixture_id: object,
        description: object,
        category: object,
        inputs: object,
        expected: object,
        metadata: object | None = None,
        schema_version: object = FIXTURE_SCHEMA_VERSION,
    ) -> Fixture | CalculationError:
        if not isinstance(fixture_id, str) or not _FIXTURE_ID.fullmatch(fixture_id):
            return _invalid_fixture("fixture_id", "fixture_id is invalid", fixture_id)
        if schema_version != FIXTURE_SCHEMA_VERSION:
            return CalculationError(
                ErrorCode.SCHEMA_VERSION_UNSUPPORTED,
                "fixture schema version is unsupported",
                "schema_version",
                {
                    "schema_version": schema_version
                    if isinstance(schema_version, int)
                    else -1
                },
            )
        if not isinstance(description, str) or not isinstance(
            category, FixtureCategory
        ):
            return _invalid_fixture("fixture", "fixture contract is invalid", category)
        if not isinstance(inputs, Mapping) or not isinstance(expected, Mapping):
            return _invalid_fixture(
                "fixture", "inputs and expected must be mappings", inputs
            )
        if metadata is not None and not isinstance(metadata, Mapping):
            return _invalid_fixture("metadata", "metadata must be a mapping", metadata)
        try:
            return cls(
                fixture_id,
                description,
                category,
                inputs,
                expected,
                {} if metadata is None else metadata,
                FIXTURE_SCHEMA_VERSION,
            )
        except TypeError as error:
            return _invalid_fixture("fixture", str(error), inputs)


def _fixture(
    fixture_id: str,
    description: str,
    category: FixtureCategory,
    inputs: Mapping[str, SafeFixtureValue],
    expected: Mapping[str, SafeFixtureValue],
) -> Fixture:
    return Fixture(fixture_id, description, category, inputs, expected, {})


SYNTHETIC_FIXTURES: tuple[Fixture, ...] = (
    _fixture(
        "fixture_zero",
        "zero is a valid neutral input",
        FixtureCategory.SMOKE,
        {"value": 0},
        {"valid": True},
    ),
    _fixture(
        "fixture_empty",
        "empty neutral structure",
        FixtureCategory.SMOKE,
        {},
        {"valid": True, "keys": 0},
    ),
    _fixture(
        "fixture_balanced",
        "balanced synthetic sides",
        FixtureCategory.REGRESSION,
        {"side_a": 1, "side_b": 1},
        {"valid": True, "balanced": True},
    ),
    _fixture(
        "fixture_home_edge",
        "synthetic advantage for side a",
        FixtureCategory.REGRESSION,
        {"side_a": 3, "side_b": 1},
        {"valid": True, "advantage": "side_a"},
    ),
    _fixture(
        "fixture_away_edge",
        "synthetic advantage for side b",
        FixtureCategory.REGRESSION,
        {"side_a": 1, "side_b": 3},
        {"valid": True, "advantage": "side_b"},
    ),
    _fixture(
        "fixture_boundary",
        "finite binary64 boundary value",
        FixtureCategory.BOUNDARY,
        {"value": 1.7976931348623157e308},
        {"valid": True},
    ),
    _fixture(
        "fixture_decimal",
        "binary64 decimal without rounding",
        FixtureCategory.BOUNDARY,
        {"value": 0.1},
        {"value": 0.1},
    ),
    _fixture(
        "fixture_invalid",
        "synthetic invalid input for the harness",
        FixtureCategory.INVALID_INPUT,
        {"value": -1},
        {"valid": False, "error_code": "invalid_statistic"},
    ),
)
