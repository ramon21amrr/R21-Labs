"""Use case for reusable, non-pricing statistics samples."""

from __future__ import annotations

from collections import Counter
from math import sqrt
from typing import Protocol

from lvfi_api.domain.errors import InvalidQueryError, ResourceNotFoundError
from lvfi_api.domain.statistics import (
    CompetitionReference,
    CompetitionReferenceRequest,
    MethodTwoSampleRequest,
    StatisticsCandidate,
    StatisticsSample,
    StatisticsSampleRequest,
    StatisticsTarget,
    UnavailableValue,
    ValueFrequency,
)


class StatisticsSampleRepository(Protocol):
    async def get_target(self, match_id: int) -> StatisticsTarget | None: ...

    async def get_previous_season_competition(
        self, previous_season_id: int
    ) -> int | None: ...

    async def list_candidates(
        self, target: StatisticsTarget, request: StatisticsSampleRequest
    ) -> tuple[StatisticsCandidate, ...]: ...

    async def list_method_two_candidates(
        self, target: StatisticsTarget, request: MethodTwoSampleRequest
    ) -> tuple[StatisticsCandidate, ...]: ...

    async def list_method_two_candidate_pair(
        self, target: StatisticsTarget, request: MethodTwoSampleRequest
    ) -> tuple[tuple[StatisticsCandidate, ...], tuple[StatisticsCandidate, ...]]: ...

    async def get_competition_reference(
        self, target: StatisticsTarget, request: CompetitionReferenceRequest
    ) -> CompetitionReference: ...

    async def get_competition_reference_pair(
        self, target: StatisticsTarget, request: CompetitionReferenceRequest
    ) -> tuple[CompetitionReference, CompetitionReference]: ...


class StatisticsSampleService:
    """Validate explicit filters and calculate aggregates without missing-as-zero."""

    def __init__(self, repository: StatisticsSampleRepository) -> None:
        self._repository = repository

    async def get_target(self, match_id: int) -> StatisticsTarget | None:
        """Expose the read-only target context for a composed statistics method."""
        return await self._repository.get_target(match_id)

    async def get_sample(
        self, match_id: int, request: StatisticsSampleRequest
    ) -> StatisticsSample:
        target = await self.get_target(match_id)
        if target is None:
            raise ResourceNotFoundError("match")
        if request.team_id not in {target.home_team_id, target.away_team_id}:
            raise InvalidQueryError("sample team is not a target participant")
        await self._validate_season(
            target, request.season_scope, request.previous_season_id
        )

        candidates = await self._repository.list_candidates(target, request)
        values = tuple(item.value for item in candidates if item.value is not None)
        used = tuple(item for item in candidates if item.value is not None)
        unavailable = tuple(
            UnavailableValue(item.match_id, item.unavailable_reason or "unavailable")
            for item in candidates
            if item.value is None
        )
        mean = sum(values) / len(values) if values else None
        population_standard_deviation = (
            sqrt(sum((value - mean) ** 2 for value in values) / len(values))
            if mean is not None
            else None
        )
        if mean is None or mean == 0 or population_standard_deviation is None:
            coefficient_of_variation = None
        else:
            coefficient_of_variation = population_standard_deviation / mean
        frequencies = tuple(
            ValueFrequency(value, count)
            for value, count in sorted(Counter(values).items())
        )
        achievement_count, achievement_rate = self._achievement(values, request)
        warnings: list[str] = []
        if not candidates:
            warnings.append("no_candidate_matches")
        if len(candidates) < request.sample_size:
            warnings.append("sample_partial")
        if unavailable:
            warnings.append("unavailable_values")
        if not values:
            warnings.append("no_available_values")
        if 0 < len(values) < 5:
            warnings.append("low_available_observations")
        return StatisticsSample(
            target=target,
            request=request,
            ordering="played_on_desc_match_id_asc",
            candidate_count=len(candidates),
            used_count=len(used),
            candidate_match_ids=tuple(item.match_id for item in candidates),
            used_match_ids=tuple(item.match_id for item in used),
            candidates=candidates,
            used_matches=used,
            valid_values=values,
            unavailable_values=unavailable,
            available_count=len(values),
            mean=mean,
            population_standard_deviation=population_standard_deviation,
            coefficient_of_variation=coefficient_of_variation,
            frequencies=frequencies,
            achievement_count=achievement_count,
            achievement_rate=achievement_rate,
            warnings=tuple(warnings),
        )

    async def get_method_two_sample(
        self, match_id: int, request: MethodTwoSampleRequest
    ) -> StatisticsSample:
        """Return a completed-match sample through the APP-013 aggregation path."""
        target = await self.get_target(match_id)
        if target is None:
            raise ResourceNotFoundError("match")
        if request.team_id not in {target.home_team_id, target.away_team_id}:
            raise InvalidQueryError("sample team is not a target participant")
        await self._validate_season(
            target, request.season_scope, request.previous_season_id
        )
        candidates = await self._repository.list_method_two_candidates(target, request)
        return self._sample(
            target,
            StatisticsSampleRequest(
                team_id=request.team_id,
                sample_size=request.sample_size,
                venue=request.venue,
                competition_scope="target_competition",
                season_scope=request.season_scope,
                previous_season_id=request.previous_season_id,
                metric=request.metric,
                comparator=None,
                achievement_target=None,
            ),
            candidates,
        )

    async def get_method_two_competition_reference(
        self, match_id: int, request: CompetitionReferenceRequest
    ) -> CompetitionReference:
        """Return the completed competition universe through the same APP-013 port."""
        target = await self.get_target(match_id)
        if target is None:
            raise ResourceNotFoundError("match")
        await self._validate_season(
            target, request.season_scope, request.previous_season_id
        )
        return await self._repository.get_competition_reference(target, request)

    async def get_method_two_sample_pair(
        self, match_id: int, request: MethodTwoSampleRequest
    ) -> tuple[StatisticsSample, StatisticsSample]:
        """Materialize production and complement from one APP-013 game selection."""
        target = await self.get_target(match_id)
        if target is None:
            raise ResourceNotFoundError("match")
        if request.team_id not in {target.home_team_id, target.away_team_id}:
            raise InvalidQueryError("sample team is not a target participant")
        await self._validate_season(
            target, request.season_scope, request.previous_season_id
        )
        production, complement = await self._repository.list_method_two_candidate_pair(
            target, request
        )

        def sample(candidates: tuple[StatisticsCandidate, ...]) -> StatisticsSample:
            return self._sample(
                target,
                StatisticsSampleRequest(
                    team_id=request.team_id,
                    sample_size=request.sample_size,
                    venue=request.venue,
                    competition_scope="target_competition",
                    season_scope=request.season_scope,
                    previous_season_id=request.previous_season_id,
                    metric=request.metric,
                    comparator=None,
                    achievement_target=None,
                ),
                candidates,
            )

        return sample(production), sample(complement)

    async def get_method_two_competition_reference_pair(
        self, match_id: int, request: CompetitionReferenceRequest
    ) -> tuple[CompetitionReference, CompetitionReference]:
        """Materialize both reference components from one APP-013 game selection."""
        target = await self.get_target(match_id)
        if target is None:
            raise ResourceNotFoundError("match")
        await self._validate_season(
            target, request.season_scope, request.previous_season_id
        )
        return await self._repository.get_competition_reference_pair(target, request)

    async def _validate_season(
        self,
        target: StatisticsTarget,
        season_scope: str,
        previous_season_id: int | None,
    ) -> None:
        if season_scope == "current_and_previous":
            if previous_season_id is None:
                raise InvalidQueryError("previous season is required")
            previous_competition = (
                await self._repository.get_previous_season_competition(
                    previous_season_id
                )
            )
            if previous_competition != target.competition_id:
                raise InvalidQueryError("previous season is incompatible")
        elif previous_season_id is not None:
            raise InvalidQueryError("previous season is unsupported")

    def _sample(
        self,
        target: StatisticsTarget,
        request: StatisticsSampleRequest,
        candidates: tuple[StatisticsCandidate, ...],
    ) -> StatisticsSample:
        values = tuple(item.value for item in candidates if item.value is not None)
        used = tuple(item for item in candidates if item.value is not None)
        unavailable = tuple(
            UnavailableValue(item.match_id, item.unavailable_reason or "unavailable")
            for item in candidates
            if item.value is None
        )
        mean = sum(values) / len(values) if values else None
        population_standard_deviation = (
            sqrt(sum((value - mean) ** 2 for value in values) / len(values))
            if mean is not None
            else None
        )
        coefficient_of_variation = (
            None
            if mean is None or mean == 0 or population_standard_deviation is None
            else population_standard_deviation / mean
        )
        frequencies = tuple(
            ValueFrequency(value, count)
            for value, count in sorted(Counter(values).items())
        )
        achievement_count, achievement_rate = self._achievement(values, request)
        warnings: list[str] = []
        if not candidates:
            warnings.append("no_candidate_matches")
        if len(candidates) < request.sample_size:
            warnings.append("sample_partial")
        if unavailable:
            warnings.append("unavailable_values")
        if not values:
            warnings.append("no_available_values")
        if 0 < len(values) < 5:
            warnings.append("low_available_observations")
        return StatisticsSample(
            target=target,
            request=request,
            ordering="played_on_desc_match_id_asc",
            candidate_count=len(candidates),
            used_count=len(used),
            candidate_match_ids=tuple(item.match_id for item in candidates),
            used_match_ids=tuple(item.match_id for item in used),
            candidates=candidates,
            used_matches=used,
            valid_values=values,
            unavailable_values=unavailable,
            available_count=len(values),
            mean=mean,
            population_standard_deviation=population_standard_deviation,
            coefficient_of_variation=coefficient_of_variation,
            frequencies=frequencies,
            achievement_count=achievement_count,
            achievement_rate=achievement_rate,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _achievement(
        values: tuple[int, ...], request: StatisticsSampleRequest
    ) -> tuple[int | None, float | None]:
        if request.comparator is None or request.achievement_target is None:
            return None, None
        target = request.achievement_target
        if request.comparator == "at_least":
            count = sum(value >= target for value in values)
        elif request.comparator == "at_most":
            count = sum(value <= target for value in values)
        else:
            count = sum(value == target for value in values)
        return count, (count / len(values) if values else None)
