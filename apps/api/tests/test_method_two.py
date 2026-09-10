"""Deterministic contract coverage for the APP-013 composed Method Two."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal, cast

import pytest

from lvfi_api.application.method_two import (
    MethodTwoAdjustedPoissonService,
    _json_bytes,
    poisson_probability,
)
from lvfi_api.domain.errors import InvalidQueryError, ResourceNotFoundError
from lvfi_api.domain.method_two import MethodTwoConfiguration
from lvfi_api.domain.statistics import (
    CompetitionReference,
    CompetitionReferenceRequest,
    MethodTwoSampleRequest,
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


def configuration(**changes: object) -> MethodTwoConfiguration:
    values: dict[str, object] = {
        "sample_size": 5,
        "context": "venue",
        "season_scope": "current",
        "previous_season_id": None,
        "metric": "fouls",
    }
    values.update(changes)
    return MethodTwoConfiguration(**values)  # type: ignore[arg-type]


def _candidate(
    match_id: int, value: int | None, venue: Literal["home", "away"]
) -> StatisticsCandidate:
    return StatisticsCandidate(
        match_id=match_id,
        played_on=TARGET.played_on - timedelta(100 - match_id),
        competition_id=1,
        competition_name="League",
        season_id=10,
        season_label="2026",
        home_team_id=7 if venue == "home" else 9,
        home_team_name="Home" if venue == "home" else "Other",
        away_team_id=9 if venue == "home" else 8,
        away_team_name="Other" if venue == "home" else "Away",
        venue=venue,
        value=value,
        unavailable_reason="statistic_unavailable" if value is None else None,
    )


def sample(
    team_id: int,
    venue: Literal["home", "away", "overall"],
    values: tuple[int | None, ...],
    *,
    metric: str = "fouls",
    sample_size: int = 5,
) -> StatisticsSample:
    candidate_venue: Literal["home", "away"] = "home" if venue != "away" else "away"
    candidates = tuple(
        _candidate(99 - index, value, candidate_venue)
        for index, value in enumerate(values)
    )
    valid = tuple(value for value in values if value is not None)
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
            metric=cast(Any, metric),
            comparator=None,
            achievement_target=None,
        ),
        ordering="played_on_desc_match_id_asc",
        candidate_count=len(candidates),
        used_count=len(valid),
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
        valid_values=valid,
        unavailable_values=unavailable,
        available_count=len(valid),
        mean=sum(valid) / len(valid) if valid else None,
        population_standard_deviation=None,
        coefficient_of_variation=None,
        frequencies=(),
        achievement_count=None,
        achievement_rate=None,
        warnings=("unavailable_values",) if unavailable else (),
    )


def reference(
    venue: Literal["home", "away", "overall"],
    values: tuple[int | None, ...],
    *,
    component: Literal["production", "complement"] = "production",
    sample_size: int = 5,
) -> CompetitionReference:
    candidates = tuple(
        _candidate(90 - index, value, "home" if venue != "away" else "away")
        for index, value in enumerate(values)
    )
    valid = tuple(value for value in values if value is not None)
    unavailable = tuple(
        UnavailableValue(candidate.match_id, "statistic_unavailable")
        for candidate in candidates
        if candidate.value is None
    )
    return CompetitionReference(
        target=TARGET,
        request=CompetitionReferenceRequest(
            sample_size=cast(Literal[5, 10, 15, 20], sample_size),
            venue=venue,
            season_scope="current",
            previous_season_id=None,
            metric="fouls",
            component=component,
        ),
        ordering="played_on_desc_match_id_asc",
        completed_predicate="match_statistics.match_id_is_not_null",
        actual_match_count=min(sample_size, len(candidates)),
        candidate_match_ids=tuple(candidate.match_id for candidate in candidates),
        candidates=candidates,
        used_match_ids=tuple(
            candidate.match_id
            for candidate in candidates
            if candidate.value is not None
        ),
        valid_values=valid,
        unavailable_values=unavailable,
        available_count=len(valid),
        mean=sum(valid) / len(valid) if valid else None,
        warnings=("unavailable_values",) if unavailable else (),
    )


class App013Fake:
    def __init__(
        self,
        *,
        target: StatisticsTarget | None = TARGET,
        team_values: dict[tuple[int, str], StatisticsSample] | None = None,
        references: dict[tuple[str, str], CompetitionReference] | None = None,
    ) -> None:
        self.target = target
        self.team_values = team_values or {
            (7, "production"): sample(7, "home", (4, 2, 3)),
            (8, "complement"): sample(8, "away", (6, 4, 5)),
            (8, "production"): sample(8, "away", (2, 4, 3)),
            (7, "complement"): sample(7, "home", (3, 5, 4)),
        }
        self.references = references or {
            ("home", "production"): reference("home", (2, 4, 3)),
            ("away", "complement"): reference(
                "away", (4, 6, 5), component="complement"
            ),
            ("away", "production"): reference("away", (2, 3, 4)),
            ("home", "complement"): reference(
                "home", (3, 4, 5), component="complement"
            ),
        }
        self.sample_calls: list[MethodTwoSampleRequest] = []
        self.reference_calls: list[CompetitionReferenceRequest] = []
        self.sample_pair_calls: list[MethodTwoSampleRequest] = []
        self.reference_pair_calls: list[CompetitionReferenceRequest] = []

    async def get_target(self, match_id: int) -> StatisticsTarget | None:
        return self.target if match_id == TARGET.match_id else None

    async def get_method_two_sample(
        self, match_id: int, request: MethodTwoSampleRequest
    ) -> StatisticsSample:
        assert match_id == TARGET.match_id
        self.sample_calls.append(request)
        return self.team_values[(request.team_id, request.component)]

    async def get_method_two_competition_reference(
        self, match_id: int, request: CompetitionReferenceRequest
    ) -> CompetitionReference:
        assert match_id == TARGET.match_id
        self.reference_calls.append(request)
        return self.references[(request.venue, request.component)]

    async def get_method_two_sample_pair(
        self, match_id: int, request: MethodTwoSampleRequest
    ) -> tuple[StatisticsSample, StatisticsSample]:
        assert match_id == TARGET.match_id
        self.sample_pair_calls.append(request)
        return (
            self.team_values[(request.team_id, "production")],
            self.team_values[(request.team_id, "complement")],
        )

    async def get_method_two_competition_reference_pair(
        self, match_id: int, request: CompetitionReferenceRequest
    ) -> tuple[CompetitionReference, CompetitionReference]:
        assert match_id == TARGET.match_id
        self.reference_pair_calls.append(request)
        return (
            self.references[(request.venue, "production")],
            self.references[(request.venue, "complement")],
        )


@pytest.mark.asyncio
async def test_method_two_composes_app013_evidence_and_approved_lambdas() -> None:
    app013 = App013Fake()
    result = await MethodTwoAdjustedPoissonService(app013).execute(100, configuration())

    assert result.status == "completed"
    assert result.home_lambda == pytest.approx(3.0)
    assert result.away_lambda == pytest.approx(3.0)
    assert result.total_lambda == pytest.approx(6.0)
    assert (
        result.evidence.completed_predicate == "match_statistics.match_id_is_not_null"
    )
    assert result.evidence.away_complement.semantic == "fouls_suffered"
    assert (
        result.evidence.away_complement.source_field_projection
        == "opponent_fouls_committed"
    )
    assert result.evidence.home_production.sample.valid_values == (4, 2, 3)
    assert [
        (call.team_id, call.venue, call.component) for call in app013.sample_pair_calls
    ] == [
        (7, "home", "production"),
        (8, "away", "production"),
    ]
    assert [(call.venue, call.component) for call in app013.reference_pair_calls] == [
        ("home", "production"),
        ("away", "complement"),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("sample_size", [5, 10, 15, 20])
async def test_method_two_propagates_requested_n_and_partial_actual_n(
    sample_size: int,
) -> None:
    app013 = App013Fake()
    result = await MethodTwoAdjustedPoissonService(app013).execute(
        100, configuration(sample_size=sample_size)
    )

    assert result.status == "completed"
    assert [call.sample_size for call in app013.sample_pair_calls] == [sample_size] * 2
    assert [call.sample_size for call in app013.reference_pair_calls] == [
        sample_size
    ] * 2
    home_sample = result.evidence.home_production.sample
    home_reference = result.evidence.home_production_reference.sample
    assert isinstance(home_sample, StatisticsSample)
    assert isinstance(home_reference, CompetitionReference)
    assert home_sample.candidate_count == 3
    assert home_reference.actual_match_count == 3


@pytest.mark.asyncio
async def test_method_two_overall_context_is_deterministic() -> None:
    app013 = App013Fake(
        team_values={
            (7, "production"): sample(7, "overall", (4, 2)),
            (8, "complement"): sample(8, "overall", (6, 4)),
            (8, "production"): sample(8, "overall", (2, 4)),
            (7, "complement"): sample(7, "overall", (3, 5)),
        },
        references={
            ("overall", "production"): reference("overall", (2, 4)),
            ("overall", "complement"): reference(
                "overall", (4, 6), component="complement"
            ),
        },
    )
    service = MethodTwoAdjustedPoissonService(app013)

    first = await service.execute(100, configuration(context="overall"))
    second = await service.execute(100, configuration(context="overall"))

    assert first == second
    assert first.evidence_fingerprint == second.evidence_fingerprint
    assert {call.venue for call in app013.sample_pair_calls} == {"overall"}
    assert {call.venue for call in app013.reference_pair_calls} == {"overall"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("metric", "semantic", "projection"),
    [
        ("goals_scored", "goals_conceded", "opponent_goals_scored"),
        ("corners", "corners_conceded", "opponent_corners"),
        ("shots_on_target", "shots_on_target_conceded", "opponent_shots_on_target"),
        ("shots", "shots_conceded", "opponent_shots"),
        ("cards", "cards_generated", "opponent_cards_received"),
        ("fouls", "fouls_suffered", "opponent_fouls_committed"),
    ],
)
async def test_method_two_maps_only_real_opponent_complements(
    metric: str, semantic: str, projection: str
) -> None:
    result = await MethodTwoAdjustedPoissonService(App013Fake()).execute(
        100, configuration(metric=metric)
    )

    assert result.evidence.away_complement.semantic == semantic
    assert result.evidence.away_complement.source_field_projection == projection
    assert result.evidence.home_complement.semantic == semantic


@pytest.mark.asyncio
async def test_method_two_blocks_missing_without_converting_it_to_zero() -> None:
    app013 = App013Fake(
        team_values={
            (7, "production"): sample(7, "home", (None,)),
            (8, "complement"): sample(8, "away", (6,)),
            (8, "production"): sample(8, "away", (2,)),
            (7, "complement"): sample(7, "home", (3,)),
        }
    )
    result = await MethodTwoAdjustedPoissonService(app013).execute(100, configuration())

    assert result.status == "blocked"
    assert result.home_lambda is None
    assert "home_production:no_available_values" in result.blocking_reasons
    assert result.evidence.home_production.sample.valid_values == ()
    assert result.evidence.home_production.sample.unavailable_values[0].match_id == 99


@pytest.mark.asyncio
async def test_method_two_blocks_zero_competition_reference_explicitly() -> None:
    app013 = App013Fake(
        references={
            ("home", "production"): reference("home", (0,)),
            ("away", "complement"): reference("away", (4,), component="complement"),
            ("away", "production"): reference("away", (2,)),
            ("home", "complement"): reference("home", (3,), component="complement"),
        }
    )
    result = await MethodTwoAdjustedPoissonService(app013).execute(100, configuration())

    assert result.status == "blocked"
    assert result.total_lambda is None
    assert "home_production_reference:zero_reference_mean" in result.blocking_reasons


@pytest.mark.asyncio
async def test_method_two_blocks_missing_competition_reference_explicitly() -> None:
    app013 = App013Fake(
        references={
            ("home", "production"): reference("home", (None,)),
            ("away", "complement"): reference("away", (4,), component="complement"),
            ("away", "production"): reference("away", (2,)),
            ("home", "complement"): reference("home", (3,), component="complement"),
        }
    )
    result = await MethodTwoAdjustedPoissonService(app013).execute(100, configuration())

    assert result.status == "blocked"
    assert "home_production_reference:no_available_values" in result.blocking_reasons


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"sample_size": 6}, "unsupported sample size"),
        ({"context": "home"}, "unsupported context"),
        ({"season_scope": "invalid"}, "unsupported season scope"),
        ({"metric": "result_win"}, "unsupported metric"),
        ({"previous_season_id": 9}, "previous season is unsupported"),
        (
            {"season_scope": "current_and_previous", "previous_season_id": None},
            "previous season is required",
        ),
    ],
)
async def test_method_two_rejects_invalid_configuration(
    changes: dict[str, object], message: str
) -> None:
    with pytest.raises(InvalidQueryError, match=message):
        await MethodTwoAdjustedPoissonService(App013Fake()).execute(
            100, configuration(**changes)
        )


@pytest.mark.asyncio
async def test_method_two_rejects_unknown_target() -> None:
    with pytest.raises(ResourceNotFoundError, match="match"):
        await MethodTwoAdjustedPoissonService(App013Fake(target=None)).execute(
            100, configuration()
        )


@pytest.mark.parametrize(
    ("value", "rate", "expected"),
    [
        (0, 3.0, pytest.approx(0.049787068367863944)),
        (2, 3.0, pytest.approx(0.22404180765538775)),
    ],
)
def test_method_two_poisson_probability_is_unrounded_and_rejects_negative_inputs(
    value: int, rate: float, expected: object
) -> None:
    assert poisson_probability(value, rate) == expected
    with pytest.raises(InvalidQueryError):
        poisson_probability(-1, rate)
    with pytest.raises(InvalidQueryError):
        poisson_probability(value, -1.0)


def test_method_two_canonical_hash_supports_lists() -> None:
    assert _json_bytes([1, 2]) == b"[1,2]"
