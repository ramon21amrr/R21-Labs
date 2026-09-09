"""Versioned contracts for Method Three observed-frequency results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from lvfi_api.domain.statistics import (
    AchievementComparator,
    CompetitionScope,
    Metric,
    SeasonScope,
    StatisticsSample,
    StatisticsTarget,
)

METHOD_THREE_NAME: Literal["method_three_observed_frequency"] = (
    "method_three_observed_frequency"
)
METHOD_THREE_VERSION: Literal["1.0.0"] = "1.0.0"


@dataclass(frozen=True, slots=True)
class MethodThreeConfiguration:
    """The explicit shared filters for the home and away APP-013 samples."""

    sample_size: Literal[5, 10, 15, 20]
    competition_scope: CompetitionScope
    season_scope: SeasonScope
    previous_season_id: int | None
    metric: Metric
    comparator: AchievementComparator
    achievement_target: int


@dataclass(frozen=True, slots=True)
class ObservedFrequency:
    """One auditable event count and its valid-observation denominator."""

    event_count: int
    valid_observation_count: int
    frequency: float | None


@dataclass(frozen=True, slots=True)
class MethodThreeSideResult:
    """One venue-conditioned frequency with its complete APP-013 evidence."""

    frequency: ObservedFrequency
    sample: StatisticsSample


@dataclass(frozen=True, slots=True)
class MethodThreeResult:
    """Deterministic Method Three output; no Pricing Engine artifact is involved."""

    method: Literal["method_three_observed_frequency"]
    method_version: Literal["1.0.0"]
    target: StatisticsTarget
    configuration: MethodThreeConfiguration
    nominal_sample_size: Literal[5, 10, 15, 20]
    home: MethodThreeSideResult
    away: MethodThreeSideResult
    combined: ObservedFrequency
    warnings: tuple[str, ...]
