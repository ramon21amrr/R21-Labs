"""Deterministic construction of Method 1 historical samples."""

from __future__ import annotations

from typing import Protocol

from lvfi_api.application.historical_queries import HistoricalQueryService
from lvfi_api.domain.historical_queries import (
    Match,
    MethodOneSample,
    MethodOneSampleMatch,
    MethodOneSampleParameters,
    MethodOneTeamSample,
)


class MethodOneSampleRepository(Protocol):
    """Read-only persistence boundary for the two independent sample series."""

    async def get_samples(
        self, target_match: Match
    ) -> tuple[tuple[MethodOneSampleMatch, ...], tuple[MethodOneSampleMatch, ...]]: ...


class MethodOneSampleService:
    """Build samples only; no Method 1 calculation or pricing is performed."""

    def __init__(
        self,
        historical_queries: HistoricalQueryService,
        repository: MethodOneSampleRepository,
    ) -> None:
        self._historical_queries = historical_queries
        self._repository = repository

    async def get_sample(self, match_id: int) -> MethodOneSample:
        target_match = await self._historical_queries.get_match(match_id)
        home_matches, away_matches = await self._repository.get_samples(target_match)
        parameters = MethodOneSampleParameters(
            requested_count=10,
            competition_id=target_match.competition.id,
            season_id=target_match.season.id,
            include_previous_season=False,
            ordering="played_on_desc_match_id_asc",
            statistic_periods=("goals_first_half", "goals_regulation_time"),
        )
        home_sample = self._team_sample(
            "home", parameters.requested_count, home_matches
        )
        away_sample = self._team_sample(
            "away", parameters.requested_count, away_matches
        )
        warnings = tuple(
            warning
            for warning in (
                "home_sample_incomplete" if not home_sample.complete else None,
                "away_sample_incomplete" if not away_sample.complete else None,
            )
            if warning is not None
        )
        return MethodOneSample(
            target_match=target_match,
            parameters=parameters,
            home_sample=home_sample,
            away_sample=away_sample,
            warnings=warnings,
        )

    @staticmethod
    def _team_sample(
        venue_condition: str,
        expected_count: int,
        matches: tuple[MethodOneSampleMatch, ...],
    ) -> MethodOneTeamSample:
        complete = len(matches) == expected_count
        return MethodOneTeamSample(
            venue_condition=venue_condition,
            expected_count=expected_count,
            found_count=len(matches),
            complete=complete,
            insufficient_reason=None if complete else "insufficient_eligible_matches",
            matches=matches,
        )
