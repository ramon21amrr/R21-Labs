"""Synthetic contract coverage for reusable, non-pricing statistics samples."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from typing import Any, Literal, cast

import pytest
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.application.statistics import StatisticsSampleService
from lvfi_api.domain.errors import InvalidQueryError, ResourceNotFoundError
from lvfi_api.domain.statistics import (
    StatisticsCandidate,
    StatisticsSampleRequest,
    StatisticsTarget,
)
from lvfi_api.persistence.statistics import SqlAlchemyStatisticsSampleRepository

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


def request(**changes: object) -> StatisticsSampleRequest:
    values: dict[str, Any] = {
        "team_id": 7,
        "sample_size": 5,
        "venue": "overall",
        "competition_scope": "target_competition",
        "season_scope": "current",
        "previous_season_id": None,
        "metric": "corners",
        "comparator": "at_least",
        "achievement_target": 2,
    }
    values.update(changes)
    return StatisticsSampleRequest(**values)


def candidate(
    match_id: int,
    value: int | None,
    *,
    played_on: date = date(2026, 7, 9),
    venue: str = "home",
    reason: str | None = None,
) -> StatisticsCandidate:
    return StatisticsCandidate(
        match_id=match_id,
        played_on=played_on,
        competition_id=1,
        competition_name="League",
        season_id=10,
        season_label="2026",
        home_team_id=7 if venue == "home" else 9,
        home_team_name="Home" if venue == "home" else "Other",
        away_team_id=9 if venue == "home" else 7,
        away_team_name="Other" if venue == "home" else "Home",
        venue=cast(Literal["home", "away"], venue),
        value=value,
        unavailable_reason=reason,
    )


class RepositoryFake:
    def __init__(
        self,
        candidates: tuple[StatisticsCandidate, ...] = (),
        *,
        target: StatisticsTarget | None = TARGET,
        previous_competition: int | None = 1,
    ) -> None:
        self.candidates = candidates
        self.target = target
        self.previous_competition = previous_competition
        self.requests: list[StatisticsSampleRequest] = []

    async def get_target(self, match_id: int) -> StatisticsTarget | None:
        return (
            self.target
            if self.target is not None and match_id == TARGET.match_id
            else None
        )

    async def get_previous_season_competition(
        self, previous_season_id: int
    ) -> int | None:
        return self.previous_competition

    async def list_candidates(
        self, target: StatisticsTarget, sample_request: StatisticsSampleRequest
    ) -> tuple[StatisticsCandidate, ...]:
        assert target == TARGET
        self.requests.append(sample_request)
        return self.candidates


@pytest.mark.asyncio
@pytest.mark.parametrize("sample_size", [5, 10, 15, 20])
@pytest.mark.parametrize("venue", ["home", "away", "overall"])
@pytest.mark.parametrize("competition_scope", ["target_competition", "all_eligible"])
async def test_service_preserves_configurable_sample_dimensions(
    sample_size: int, venue: str, competition_scope: str
) -> None:
    repository = RepositoryFake((candidate(1, 0),))
    configured = request(
        sample_size=sample_size,
        venue=venue,
        competition_scope=competition_scope,
    )

    sample = await StatisticsSampleService(repository).get_sample(100, configured)

    assert repository.requests == [configured]
    assert sample.request == configured
    assert sample.candidate_match_ids == (1,)
    assert sample.valid_values == (0,)
    assert sample.mean == 0


@pytest.mark.asyncio
async def test_service_current_and_explicit_previous_season_are_distinct() -> None:
    repository = RepositoryFake((candidate(1, 3),))
    service = StatisticsSampleService(repository)

    current = await service.get_sample(100, request())
    previous = await service.get_sample(
        100,
        request(season_scope="current_and_previous", previous_season_id=9),
    )

    assert current.request.previous_season_id is None
    assert previous.request.season_scope == "current_and_previous"
    assert previous.request.previous_season_id == 9
    with pytest.raises(InvalidQueryError):
        await service.get_sample(100, request(season_scope="current_and_previous"))
    with pytest.raises(InvalidQueryError):
        await service.get_sample(100, request(previous_season_id=9))
    with pytest.raises(InvalidQueryError):
        await StatisticsSampleService(
            RepositoryFake(previous_competition=99)
        ).get_sample(
            100, request(season_scope="current_and_previous", previous_season_id=9)
        )


@pytest.mark.asyncio
async def test_service_keeps_missing_values_out_of_statistics_and_zero_is_valid() -> (
    None
):
    repository = RepositoryFake(
        (
            candidate(9, 0),
            candidate(8, None, reason="statistic_unavailable"),
            candidate(7, 4),
        )
    )

    sample = await StatisticsSampleService(repository).get_sample(100, request())

    assert sample.candidate_count == 3
    assert sample.used_count == sample.available_count == 2
    assert sample.candidate_match_ids == (9, 8, 7)
    assert sample.used_match_ids == (9, 7)
    assert sample.valid_values == (0, 4)
    assert sample.unavailable_values[0].match_id == 8
    assert sample.unavailable_values[0].reason == "statistic_unavailable"
    assert sample.mean == 2
    assert sample.population_standard_deviation == 2
    assert sample.coefficient_of_variation == 1
    assert [(item.value, item.count) for item in sample.frequencies] == [(0, 1), (4, 1)]
    assert sample.achievement_count == 1
    assert sample.achievement_rate == 0.5
    assert "unavailable_values" in sample.warnings
    assert "low_available_observations" in sample.warnings


@pytest.mark.asyncio
async def test_service_reports_empty_and_partial_samples_deterministically() -> None:
    service = StatisticsSampleService(RepositoryFake())

    sample = await service.get_sample(100, request())

    assert sample.candidate_count == sample.used_count == sample.available_count == 0
    assert (
        sample.candidate_match_ids == sample.used_match_ids == sample.valid_values == ()
    )
    assert (
        sample.mean
        is sample.population_standard_deviation
        is sample.coefficient_of_variation
        is None
    )
    assert sample.achievement_count == 0
    assert sample.achievement_rate is None
    assert sample.warnings == (
        "no_candidate_matches",
        "sample_partial",
        "no_available_values",
    )


@pytest.mark.asyncio
async def test_service_uses_population_sd_and_null_cv_for_zero_mean() -> None:
    service = StatisticsSampleService(
        RepositoryFake((candidate(3, 1), candidate(2, 2), candidate(1, 3)))
    )
    sample = await service.get_sample(
        100, request(comparator=None, achievement_target=None)
    )
    zero_mean = await StatisticsSampleService(
        RepositoryFake((candidate(4, 0), candidate(3, 0)))
    ).get_sample(100, request())

    assert sample.mean == 2
    assert sample.population_standard_deviation == pytest.approx((2 / 3) ** 0.5)
    assert sample.coefficient_of_variation == pytest.approx(((2 / 3) ** 0.5) / 2)
    assert sample.achievement_count is sample.achievement_rate is None
    assert zero_mean.mean == zero_mean.population_standard_deviation == 0
    assert zero_mean.coefficient_of_variation is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("comparator", "target", "expected"),
    [("at_least", 2, 2), ("at_most", 2, 2), ("equal", 2, 1)],
)
async def test_service_calculates_frequency_and_achievement(
    comparator: str, target: int, expected: int
) -> None:
    sample = await StatisticsSampleService(
        RepositoryFake((candidate(3, 1), candidate(2, 2), candidate(1, 3)))
    ).get_sample(100, request(comparator=comparator, achievement_target=target))

    assert sample.achievement_count == expected
    assert sample.achievement_rate == pytest.approx(expected / 3)
    assert [(item.value, item.count) for item in sample.frequencies] == [
        (1, 1),
        (2, 1),
        (3, 1),
    ]


@pytest.mark.asyncio
async def test_service_sanitizes_target_absence_and_rejects_non_participant() -> None:
    with pytest.raises(ResourceNotFoundError):
        await StatisticsSampleService(RepositoryFake(target=None)).get_sample(
            100, request()
        )
    with pytest.raises(InvalidQueryError):
        await StatisticsSampleService(RepositoryFake()).get_sample(
            100, request(team_id=99)
        )


class MappingResult:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    def mappings(self) -> MappingResult:
        return self

    def one_or_none(self) -> dict[str, object] | None:
        return self.rows[0] if self.rows else None

    def all(self) -> list[dict[str, object]]:
        return self.rows


class SessionFake:
    def __init__(self, results: list[MappingResult], *, fail: bool = False) -> None:
        self.results = results
        self.fail = fail
        self.statements: list[Any] = []

    async def execute(self, statement: Any) -> MappingResult:
        self.statements.append(statement)
        if self.fail:
            raise SQLAlchemyError("synthetic persistence failure")
        return self.results.pop(0)


class ProviderFake:
    def __init__(self, session: SessionFake) -> None:
        self.session_value = session

    @asynccontextmanager
    async def session(self) -> Any:
        yield self.session_value


def target_row() -> dict[str, object]:
    return {
        "match_id": 100,
        "played_on": date(2026, 7, 10),
        "competition_id": 1,
        "competition_name": "League",
        "season_id": 10,
        "season_label": "2026",
        "home_team_id": 7,
        "home_team_name": "Home",
        "away_team_id": 8,
        "away_team_name": "Away",
    }


def candidate_row(
    match_id: int, value: int | None, reason: str | None = None
) -> dict[str, object]:
    return {
        **target_row(),
        "match_id": match_id,
        "played_on": date(2026, 7, 9),
        "away_team_id": 9,
        "away_team_name": "Other",
        "venue": "home",
        "value": value,
        "unavailable_reason": reason,
    }


@pytest.mark.asyncio
async def test_repository_uses_bounded_temporal_deterministic_revision_query() -> None:
    session = SessionFake(
        [
            MappingResult([target_row()]),
            MappingResult(
                [
                    candidate_row(99, None, "statistic_unavailable"),
                    candidate_row(98, 7),
                    candidate_row(97, 0),
                ]
            ),
        ]
    )
    repository = SqlAlchemyStatisticsSampleRepository(ProviderFake(session))

    target = await repository.get_target(100)
    assert target == TARGET
    candidates = await repository.list_candidates(TARGET, request(sample_size=5))

    assert [(item.match_id, item.value) for item in candidates] == [
        (99, None),
        (98, 7),
        (97, 0),
    ]
    assert candidates[0].unavailable_reason == "statistic_unavailable"
    rendered = str(session.statements[1])
    assert "LIMIT" in rendered
    assert "matches.played_on <" in rendered
    assert "matches.id <" in rendered
    assert "matches.played_on DESC" in rendered
    assert "matches.id ASC" in rendered
    assert "row_number() OVER" in rendered
    assert "statistic_revisions.created_at DESC" in rendered
    assert "statistic_revisions.id DESC" in rendered
    assert "availability" in rendered and "new_value" in rendered
    assert "method_one" not in rendered.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("metric", "expected_fields"),
    [
        ("goals_scored", ("home_goals_full_match", "away_goals_full_match")),
        ("goals_conceded", ("home_goals_full_match", "away_goals_full_match")),
        ("result_win", ("home_goals_full_match", "away_goals_full_match")),
        ("corners", ("home_corners_full_match", "away_corners_full_match")),
        (
            "shots_on_target",
            ("home_shots_on_target_full_match", "away_shots_on_target_full_match"),
        ),
        ("shots", ("home_shots_full_match", "away_shots_full_match")),
        ("cards", ("home_cards_full_match", "away_cards_full_match")),
        ("fouls", ("home_fouls_full_match", "away_fouls_full_match")),
    ],
)
async def test_repository_supports_all_statistic_groups(
    metric: str, expected_fields: tuple[str, str]
) -> None:
    session = SessionFake([MappingResult([])])
    repository = SqlAlchemyStatisticsSampleRepository(ProviderFake(session))

    assert await repository.list_candidates(TARGET, request(metric=metric)) == ()

    rendered = str(session.statements[0])
    assert all(field in rendered for field in expected_fields)


@pytest.mark.asyncio
async def test_repository_compiles_scope_and_previous_season_filters() -> None:
    session = SessionFake([MappingResult([]), MappingResult([])])
    repository = SqlAlchemyStatisticsSampleRepository(ProviderFake(session))

    await repository.list_candidates(
        TARGET,
        request(
            competition_scope="target_competition",
            season_scope="current",
        ),
    )
    await repository.list_candidates(
        TARGET,
        request(
            competition_scope="all_eligible",
            season_scope="current_and_previous",
            previous_season_id=9,
        ),
    )

    current_rendered, previous_rendered = map(str, session.statements)
    current_where = current_rendered.split("WHERE", maxsplit=1)[1]
    assert "statistics_candidate_seasons.competition_id" in current_where
    assert "statistics_candidate_seasons.label" in current_where
    assert "SELECT seasons.label" in previous_rendered


@pytest.mark.asyncio
async def test_repository_sanitizes_target_and_candidate_persistence_failures() -> None:
    failing_target = SqlAlchemyStatisticsSampleRepository(
        ProviderFake(SessionFake([], fail=True))
    )
    with pytest.raises(Exception, match="statistics query failed"):
        await failing_target.get_target(100)

    failing_candidates = SqlAlchemyStatisticsSampleRepository(
        ProviderFake(SessionFake([], fail=True))
    )
    with pytest.raises(Exception, match="statistics query failed"):
        await failing_candidates.list_candidates(TARGET, request())
