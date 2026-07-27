"""Public query contracts for normalized historical football data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import TypeVar


@dataclass(frozen=True, slots=True)
class Reference:
    """A stable public identifier and human-readable label."""

    id: int
    display_name: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Season:
    """A public season belonging to one competition."""

    id: int
    competition: Reference
    label: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Match:
    """The public, normalized view of one historical match."""

    id: int
    played_on: date
    competition: Reference
    season: Season
    home_team: Reference
    away_team: Reference
    has_statistics: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class StatisticsPeriod:
    """Observed statistics for one team and one match period."""

    goals: int
    shots: int
    shots_on_target: int
    corners: int
    fouls: int | None
    cards: int | None


@dataclass(frozen=True, slots=True)
class TeamStatistics:
    """First-half and full-match observations for one team."""

    first_half: StatisticsPeriod
    full_match: StatisticsPeriod


@dataclass(frozen=True, slots=True)
class MatchStatistics:
    """Canonical statistics already normalized by the controlled import."""

    match_id: int
    home: TeamStatistics
    away: TeamStatistics


@dataclass(frozen=True, slots=True)
class MatchFilters:
    """Supported, exact filters for historical match listing."""

    competition_id: int | None = None
    season_id: int | None = None
    home_team_id: int | None = None
    away_team_id: int | None = None
    team_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Page[T]:
    """Deterministic offset-page result for public list endpoints."""

    items: tuple[T, ...]
    page: int
    page_size: int
    total: int
