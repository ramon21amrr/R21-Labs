"""Distribuições matemáticas puras e auditáveis."""

from .goal_difference import (
    GoalDifferenceDistribution,
    build_goal_difference_distribution,
)
from .poisson import PoissonDistribution, build_poisson_distribution, poisson_pmf
from .score_matrix import ScoreProbabilityMatrix, build_score_probability_matrix

__all__ = (
    "GoalDifferenceDistribution",
    "PoissonDistribution",
    "ScoreProbabilityMatrix",
    "build_goal_difference_distribution",
    "build_poisson_distribution",
    "build_score_probability_matrix",
    "poisson_pmf",
)
