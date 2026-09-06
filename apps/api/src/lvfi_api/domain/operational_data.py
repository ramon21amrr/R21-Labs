"""Immutable commands and records for local operational football data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from lvfi_api.historical_import import STATISTIC_FIELDS, normalized_key

StatisticAvailability = Literal["available", "missing"]


@dataclass(frozen=True)
class FutureMatchDraft:
    played_on: date
    competition: str
    season: str
    home_team: str
    away_team: str
    actor: str


@dataclass(frozen=True)
class FutureMatch:
    match_id: int
    played_on: date
    competition: str
    season: str
    home_team: str
    away_team: str
    actor: str
    created_at: datetime


@dataclass(frozen=True)
class StatisticRevisionDraft:
    match_id: int
    statistic_field: str
    availability: StatisticAvailability
    new_value: int | None
    actor: str
    reason: str


@dataclass(frozen=True)
class StatisticRevision:
    revision_id: int
    match_id: int
    statistic_field: str
    previous_value: int | None
    availability: StatisticAvailability
    new_value: int | None
    actor: str
    reason: str
    created_at: datetime


def valid_future_match(draft: FutureMatchDraft) -> bool:
    values = (
        draft.competition,
        draft.season,
        draft.home_team,
        draft.away_team,
        draft.actor,
    )
    return all(value.strip() for value in values) and (
        normalized_key(draft.home_team) != normalized_key(draft.away_team)
    )


def valid_statistic_revision(draft: StatisticRevisionDraft) -> bool:
    if (
        draft.match_id < 1
        or draft.statistic_field not in STATISTIC_FIELDS
        or not draft.actor.strip()
        or not draft.reason.strip()
    ):
        return False
    if draft.availability == "missing":
        return draft.new_value is None
    return (
        isinstance(draft.new_value, int)
        and not isinstance(draft.new_value, bool)
        and draft.new_value >= 0
    )
