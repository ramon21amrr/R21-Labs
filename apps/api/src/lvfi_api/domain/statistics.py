"""Reusable, read-only contracts for deterministic LVFI statistics samples."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

Venue = Literal["home", "away", "overall"]
CompetitionScope = Literal["target_competition", "all_eligible"]
SeasonScope = Literal["current", "current_and_previous"]
Metric = Literal[
    "goals_scored",
    "goals_conceded",
    "result_win",
    "corners",
    "shots_on_target",
    "shots",
    "cards",
    "fouls",
]
AchievementComparator = Literal["at_least", "at_most", "equal"]
MethodTwoMetric = Literal[
    "goals_scored",
    "corners",
    "shots_on_target",
    "shots",
    "cards",
    "fouls",
]
MethodTwoComponent = Literal["production", "complement"]


@dataclass(frozen=True, slots=True)
class StatisticsSampleRequest:
    """Explicit filters, with no implicit season ordering or look-ahead."""

    team_id: int
    sample_size: Literal[5, 10, 15, 20]
    venue: Venue
    competition_scope: CompetitionScope
    season_scope: SeasonScope
    previous_season_id: int | None
    metric: Metric
    comparator: AchievementComparator | None
    achievement_target: int | None


@dataclass(frozen=True, slots=True)
class StatisticsTarget:
    """The analyzed match context used as the strict temporal cutoff."""

    match_id: int
    played_on: date
    competition_id: int
    competition_name: str
    season_id: int
    season_label: str
    home_team_id: int
    home_team_name: str
    away_team_id: int
    away_team_name: str


@dataclass(frozen=True, slots=True)
class StatisticsCandidate:
    """One selected candidate; an unavailable observation remains explicit."""

    match_id: int
    played_on: date
    competition_id: int
    competition_name: str
    season_id: int
    season_label: str
    home_team_id: int
    home_team_name: str
    away_team_id: int
    away_team_name: str
    venue: Literal["home", "away"]
    value: int | None
    unavailable_reason: str | None


@dataclass(frozen=True, slots=True)
class ValueFrequency:
    value: int
    count: int


@dataclass(frozen=True, slots=True)
class UnavailableValue:
    match_id: int
    reason: str


@dataclass(frozen=True, slots=True)
class StatisticsSample:
    """Public aggregate calculated only over explicitly available observations."""

    target: StatisticsTarget
    request: StatisticsSampleRequest
    ordering: str
    candidate_count: int
    used_count: int
    candidate_match_ids: tuple[int, ...]
    used_match_ids: tuple[int, ...]
    candidates: tuple[StatisticsCandidate, ...]
    used_matches: tuple[StatisticsCandidate, ...]
    valid_values: tuple[int, ...]
    unavailable_values: tuple[UnavailableValue, ...]
    available_count: int
    mean: float | None
    population_standard_deviation: float | None
    coefficient_of_variation: float | None
    frequencies: tuple[ValueFrequency, ...]
    achievement_count: int | None
    achievement_rate: float | None
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MethodTwoSampleRequest:
    """Internal APP-013 extension for a completed-match Method Two series."""

    team_id: int
    sample_size: Literal[5, 10, 15, 20]
    venue: Venue
    season_scope: SeasonScope
    previous_season_id: int | None
    metric: MethodTwoMetric
    component: MethodTwoComponent


@dataclass(frozen=True, slots=True)
class CompetitionReferenceRequest:
    """Internal APP-013 extension for the completed competition reference."""

    sample_size: Literal[5, 10, 15, 20]
    venue: Venue
    season_scope: SeasonScope
    previous_season_id: int | None
    metric: MethodTwoMetric
    component: MethodTwoComponent


@dataclass(frozen=True, slots=True)
class CompetitionReference:
    """Auditable M2 reference over bounded, completed competition matches.

    In ``overall`` context a selected match contributes its home and away real
    observations.  ``actual_match_count`` remains the requested game count;
    ``available_count`` is deliberately the count of usable observations.
    """

    target: StatisticsTarget
    request: CompetitionReferenceRequest
    ordering: str
    completed_predicate: str
    actual_match_count: int
    candidate_match_ids: tuple[int, ...]
    candidates: tuple[StatisticsCandidate, ...]
    used_match_ids: tuple[int, ...]
    valid_values: tuple[int, ...]
    unavailable_values: tuple[UnavailableValue, ...]
    available_count: int
    mean: float | None
    warnings: tuple[str, ...]
