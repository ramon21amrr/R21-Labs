"""Infraestrutura segura e determinística para testes do Pricing Engine."""

from .fixtures import (
    FIXTURE_SCHEMA_VERSION,
    SYNTHETIC_FIXTURES,
    Fixture,
    FixtureCategory,
)
from .regression import (
    DifferenceKind,
    RegressionDifference,
    RegressionResult,
    run_regression,
)

__all__ = (
    "FIXTURE_SCHEMA_VERSION",
    "SYNTHETIC_FIXTURES",
    "Fixture",
    "FixtureCategory",
    "DifferenceKind",
    "RegressionDifference",
    "RegressionResult",
    "run_regression",
)
