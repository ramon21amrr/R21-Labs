"""Distribuições matemáticas puras e auditáveis."""

from .poisson import PoissonDistribution, build_poisson_distribution, poisson_pmf

__all__ = ("PoissonDistribution", "build_poisson_distribution", "poisson_pmf")
