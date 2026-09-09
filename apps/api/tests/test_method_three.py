"""Contract coverage for the deterministic Method Three observed-frequency core."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from typing import Literal, cast

import pytest

from lvfi_api.application.method_three import MethodThreeObservedFrequencyService
from lvfi_api.domain.errors import InvalidQueryError, ResourceNotFoundError
from lvfi_api.domain.method_three import MethodThreeConfiguration
from lvfi_api.domain.statistics import (
    StatisticsCandidate,
    StatisticsSample,
    StatisticsSampleRequest,
    StatisticsTarget,
    UnavailableValue,
)

TARGET = StatisticsTarget(
    match_id=100,
    played_on=date(2026, 7, 10),
    competition_id=1,
    competition_name="League",
    season_id=10,
    season_label="2026",
    home_team_id=7,
    home_team_name="Home",
    away_team_id=8,
    away_team_name="Away",
)


def configuration(**changes: object) -> MethodThreeConfiguration:
    values: dict[str, object] = {
        "sample_size": 5,
        "competition_scope": "target_competition",
        "season_scope": "current",
        "previous_season_id": None,
        "metric": "corners",
        "comparator": "at_least",
        "achievement_target": 2,
    }
    values.update(changes)
    return MethodThreeConfiguration(**values)  # type: ignore[arg-type]


def statistics_sample(
    team_id: int,
    venue: Literal["home", "away"],
    values: tuple[int | None, ...],
    *,
    warnings: tuple[str, ...] = (),
    sample_size: int = 5,
) -> StatisticsSample:
    candidates = tuple(
        StatisticsCandidate(
            match_id=99 - index,
            played_on=TARGET.played_on
            if index == 0
            else TARGET.played_on - timedelta(index),
            competition_id=1,
            competition_name="League",
            season_id=10,
            season_label="2026",
            home_team_id=team_id if venue == "home" else 9,
            home_team_name="Subject" if venue == "home" else "Other",
            away_team_id=9 if venue == "home" else team_id,
            away_team_name="Other" if venue == "home" else "Subject",
            venue=venue,
            value=value,
            unavailable_reason="statistic_unavailable" if value is None else None,
        )
        for index, value in enumerate(values)
    )
    valid_values = tuple(value for value in values if value is not None)
    unavailable = tuple(
        UnavailableValue(candidate.match_id, "statistic_unavailable")
        for candidate in candidates
        if candidate.value is None
    )
    return StatisticsSample(
        target=TARGET,
        request=StatisticsSampleRequest(
            team_id=team_id,
            sample_size=cast(Literal[5, 10, 15, 20], sample_size),
            venue=venue,
            competition_scope="target_competition",
            season_scope="current",
            previous_season_id=None,
            metric="corners",
            comparator="at_least",
            achievement_target=2,
        ),
        ordering="played_on_desc_match_id_asc",
        candidate_count=len(candidates),
        used_count=len(valid_values),
        candidate_match_ids=tuple(candidate.match_id for candidate in candidates),
        used_match_ids=tuple(
            candidate.match_id
            for candidate in candidates
            if candidate.value is not None
        ),
        candidates=candidates,
        used_matches=tuple(
            candidate for candidate in candidates if candidate.value is not None
        ),
        valid_values=valid_values,
        unavailable_values=unavailable,
        available_count=len(valid_values),
        mean=None,
        population_standard_deviation=None,
        coefficient_of_variation=None,
        frequencies=(),
        achievement_count=None,
        achievement_rate=None,
        warnings=warnings,
    )


class SamplesFake:
    def __init__(
        self,
        home: StatisticsSample,
        away: StatisticsSample,
        *,
        target: StatisticsTarget | None = TARGET,
    ) -> None:
        self.home = home
        self.away = away
        self.target = target
        self.calls: list[StatisticsSampleRequest] = []

    async def get_target(self, match_id: int) -> StatisticsTarget | None:
        return self.target if match_id == TARGET.match_id else None

    async def get_sample(
        self, match_id: int, request: StatisticsSampleRequest
    ) -> StatisticsSample:
        assert match_id == TARGET.match_id
        self.calls.append(request)
        return self.home if request.team_id == TARGET.home_team_id else self.away


@pytest.mark.asyncio
async def test_method_three_returns_home_away_and_pooled_frequency_evidence() -> None:
    samples = SamplesFake(
        statistics_sample(7, "home", (0, 2, None, 3), warnings=("sample_partial",)),
        statistics_sample(8, "away", (1, None, 0), warnings=("unavailable_values",)),
    )

    result = await MethodThreeObservedFrequencyService(samples).execute(
        100, configuration()
    )

    assert result.method == "method_three_observed_frequency"
    assert result.method_version == "1.0.0"
    assert result.nominal_sample_size == 5
    assert result.home.frequency.event_count == 2
    assert result.home.frequency.valid_observation_count == 3
    assert result.home.frequency.frequency == pytest.approx(2 / 3)
    assert result.away.frequency.event_count == 0
    assert result.away.frequency.valid_observation_count == 2
    assert result.away.frequency.frequency == 0
    assert result.combined.event_count == 2
    assert result.combined.valid_observation_count == 5
    assert result.combined.frequency == pytest.approx(2 / 5)
    assert result.home.sample.used_match_ids == (99, 98, 96)
    assert result.away.sample.candidate_match_ids == (99, 98, 97)
    assert result.warnings == ("home:sample_partial", "away:unavailable_values")
    assert [(call.team_id, call.venue) for call in samples.calls] == [
        (7, "home"),
        (8, "away"),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("sample_size", [5, 10, 15, 20])
async def test_method_three_propagates_each_supported_nominal_sample_size(
    sample_size: int,
) -> None:
    samples = SamplesFake(
        statistics_sample(7, "home", (2,), sample_size=sample_size),
        statistics_sample(8, "away", (2,), sample_size=sample_size),
    )

    result = await MethodThreeObservedFrequencyService(samples).execute(
        100, configuration(sample_size=sample_size)
    )

    assert result.nominal_sample_size == sample_size
    assert [call.sample_size for call in samples.calls] == [sample_size, sample_size]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("comparator", "target", "values", "expected"),
    [
        ("at_most", 0, (0, 1, 2), 1),
        ("equal", 1, (0, 1, 2), 1),
    ],
)
async def test_method_three_supports_each_comparator(
    comparator: str, target: int, values: tuple[int, ...], expected: int
) -> None:
    samples = SamplesFake(
        statistics_sample(7, "home", values),
        statistics_sample(8, "away", values),
    )

    result = await MethodThreeObservedFrequencyService(samples).execute(
        100, configuration(comparator=comparator, achievement_target=target)
    )

    assert result.home.frequency.event_count == expected
    assert result.away.frequency.event_count == expected


@pytest.mark.asyncio
async def test_method_three_marks_empty_sides_and_combined_result_unavailable() -> None:
    samples = SamplesFake(
        statistics_sample(7, "home", (None,), warnings=("no_available_values",)),
        statistics_sample(8, "away", (), warnings=("no_candidate_matches",)),
    )

    result = await MethodThreeObservedFrequencyService(samples).execute(
        100, configuration()
    )

    assert result.home.frequency.frequency is None
    assert result.away.frequency.frequency is None
    assert result.combined.frequency is None
    assert result.warnings == (
        "home:no_available_values",
        "home:frequency_unavailable_no_valid_observations",
        "away:no_candidate_matches",
        "away:frequency_unavailable_no_valid_observations",
        "combined:frequency_unavailable_no_valid_observations",
    )


@pytest.mark.asyncio
async def test_method_three_is_deterministic_and_preserves_sample_order() -> None:
    samples = SamplesFake(
        statistics_sample(7, "home", (2, 0)), statistics_sample(8, "away", (3, 1))
    )
    service = MethodThreeObservedFrequencyService(samples)

    first = await service.execute(100, configuration())
    second = await service.execute(100, configuration())

    assert first == second
    assert first.home.sample.candidate_match_ids == (99, 98)
    assert first.home.sample.ordering == "played_on_desc_match_id_asc"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"sample_size": 6}, "unsupported sample size"),
        ({"previous_season_id": 9}, "previous season is unsupported"),
        (
            {"season_scope": "current_and_previous", "previous_season_id": None},
            "previous season is required",
        ),
        ({"achievement_target": -1}, "achievement target must be nonnegative"),
        ({"competition_scope": "invalid"}, "unsupported competition scope"),
        ({"season_scope": "invalid"}, "unsupported season scope"),
        ({"metric": "invalid"}, "unsupported metric"),
        ({"comparator": "invalid"}, "unsupported comparator"),
    ],
)
async def test_method_three_rejects_invalid_configuration(
    changes: dict[str, object], message: str
) -> None:
    samples = SamplesFake(
        statistics_sample(7, "home", (2,)), statistics_sample(8, "away", (2,))
    )

    with pytest.raises(InvalidQueryError, match=message):
        await MethodThreeObservedFrequencyService(samples).execute(
            100, configuration(**changes)
        )

    assert not samples.calls


@pytest.mark.asyncio
async def test_method_three_rejects_absent_target_and_invalid_sample_cutoff() -> None:
    missing = SamplesFake(
        statistics_sample(7, "home", (2,)),
        statistics_sample(8, "away", (2,)),
        target=None,
    )
    with pytest.raises(ResourceNotFoundError):
        await MethodThreeObservedFrequencyService(missing).execute(100, configuration())

    sample = statistics_sample(7, "home", (2,))
    after_cutoff = replace(
        sample,
        candidates=(
            replace(
                sample.candidates[0], played_on=TARGET.played_on + timedelta(days=1)
            ),
        ),
    )
    invalid = SamplesFake(after_cutoff, statistics_sample(8, "away", (2,)))
    with pytest.raises(InvalidQueryError, match="after cutoff"):
        await MethodThreeObservedFrequencyService(invalid).execute(100, configuration())


@pytest.mark.asyncio
async def test_method_three_rejects_same_day_target_id_or_inconsistent_target() -> None:
    sample = statistics_sample(7, "home", (2,))
    same_day_target = replace(
        sample,
        candidates=(replace(sample.candidates[0], match_id=TARGET.match_id),),
    )
    with pytest.raises(InvalidQueryError, match="after cutoff"):
        await MethodThreeObservedFrequencyService(
            SamplesFake(same_day_target, statistics_sample(8, "away", (2,)))
        ).execute(100, configuration())

    inconsistent = replace(sample, target=replace(TARGET, match_id=101))
    with pytest.raises(InvalidQueryError, match="inconsistent"):
        await MethodThreeObservedFrequencyService(
            SamplesFake(inconsistent, statistics_sample(8, "away", (2,)))
        ).execute(100, configuration())


@pytest.mark.asyncio
async def test_method_three_rejects_values_not_evidenced_by_valid_candidates() -> None:
    sample = statistics_sample(7, "home", (2,))
    inconsistent = replace(sample, valid_values=(99,))

    with pytest.raises(InvalidQueryError, match="evidence is inconsistent"):
        await MethodThreeObservedFrequencyService(
            SamplesFake(inconsistent, statistics_sample(8, "away", (2,)))
        ).execute(100, configuration())
