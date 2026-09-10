"""Deterministic adjusted-Poisson Method Two composed through APP-013."""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from datetime import date
from math import exp, factorial
from typing import Any, Literal, Protocol, cast

from lvfi_api.domain.errors import InvalidQueryError, ResourceNotFoundError
from lvfi_api.domain.method_two import (
    METHOD_TWO_CONFIGURATION_SCHEMA_VERSION,
    METHOD_TWO_EVIDENCE_SCHEMA_VERSION,
    METHOD_TWO_NAME,
    METHOD_TWO_RESULT_SCHEMA_VERSION,
    METHOD_TWO_VERSION,
    MethodTwoConfiguration,
    MethodTwoEvidence,
    MethodTwoResult,
    MethodTwoSeries,
)
from lvfi_api.domain.statistics import (
    CompetitionReference,
    CompetitionReferenceRequest,
    MethodTwoSampleRequest,
    StatisticsSample,
    StatisticsTarget,
)


class MethodTwoStatistics(Protocol):
    """The internal completed-match APP-013 port used by Method Two only."""

    async def get_target(self, match_id: int) -> StatisticsTarget | None: ...

    async def get_method_two_sample_pair(
        self, match_id: int, request: MethodTwoSampleRequest
    ) -> tuple[StatisticsSample, StatisticsSample]: ...

    async def get_method_two_competition_reference_pair(
        self, match_id: int, request: CompetitionReferenceRequest
    ) -> tuple[CompetitionReference, CompetitionReference]: ...


_COMPLEMENT_SEMANTICS: dict[str, tuple[str, str]] = {
    "goals_scored": ("goals_conceded", "opponent_goals_scored"),
    "corners": ("corners_conceded", "opponent_corners"),
    "shots_on_target": (
        "shots_on_target_conceded",
        "opponent_shots_on_target",
    ),
    "shots": ("shots_conceded", "opponent_shots"),
    "fouls": ("fouls_suffered", "opponent_fouls_committed"),
    "cards": ("cards_generated", "opponent_cards_received"),
}


class MethodTwoAdjustedPoissonService:
    """Build λ by the approved formula without local match selection or rounding."""

    def __init__(self, statistics: MethodTwoStatistics) -> None:
        self._statistics = statistics

    async def execute(
        self, match_id: int, configuration: MethodTwoConfiguration
    ) -> MethodTwoResult:
        _validate_configuration(configuration)
        target = await self._statistics.get_target(match_id)
        if target is None:
            raise ResourceNotFoundError("match")
        (
            home_production,
            away_complement,
            away_production,
            home_complement,
        ) = await self._team_series(match_id, target, configuration)
        references = await self._reference_series(match_id, configuration)
        evidence = MethodTwoEvidence(
            evidence_schema_version=cast(
                Literal[1], METHOD_TWO_EVIDENCE_SCHEMA_VERSION
            ),
            target=target,
            configuration=configuration,
            completed_predicate="match_statistics.match_id_is_not_null",
            home_production=home_production,
            away_complement=away_complement,
            away_production=away_production,
            home_complement=home_complement,
            home_production_reference=references[0],
            away_complement_reference=references[1],
            away_production_reference=references[2],
            home_complement_reference=references[3],
        )
        configuration_fingerprint = _sha256(
            {
                "configuration": configuration,
                "configuration_schema_version": METHOD_TWO_CONFIGURATION_SCHEMA_VERSION,
                "method": METHOD_TWO_NAME,
                "method_version": METHOD_TWO_VERSION,
            }
        )
        evidence_fingerprint = _sha256(evidence)
        blocking_reasons = _blocking_reasons(evidence)
        if blocking_reasons:
            return _result(
                evidence,
                configuration_fingerprint,
                evidence_fingerprint,
                "blocked",
                None,
                None,
                tuple(blocking_reasons),
            )
        home_lambda = _lambda(
            home_production.sample,
            away_complement.sample,
            references[0].sample,
            references[1].sample,
        )
        away_lambda = _lambda(
            away_production.sample,
            home_complement.sample,
            references[2].sample,
            references[3].sample,
        )
        return _result(
            evidence,
            configuration_fingerprint,
            evidence_fingerprint,
            "completed",
            home_lambda,
            away_lambda,
            (),
        )

    async def _team_series(
        self,
        match_id: int,
        target: StatisticsTarget,
        configuration: MethodTwoConfiguration,
    ) -> tuple[MethodTwoSeries, MethodTwoSeries, MethodTwoSeries, MethodTwoSeries]:
        complement_semantic, complement_projection = _COMPLEMENT_SEMANTICS[
            configuration.metric
        ]
        home_venue: Literal["home", "away", "overall"]
        away_venue: Literal["home", "away", "overall"]
        home_venue, away_venue = (
            ("home", "away")
            if configuration.context == "venue"
            else ("overall", "overall")
        )
        (
            home_production,
            home_complement,
        ) = await self._statistics.get_method_two_sample_pair(
            match_id,
            MethodTwoSampleRequest(
                team_id=target.home_team_id,
                sample_size=configuration.sample_size,
                venue=home_venue,
                season_scope=configuration.season_scope,
                previous_season_id=configuration.previous_season_id,
                metric=configuration.metric,
                component="production",
            ),
        )
        (
            away_production,
            away_complement,
        ) = await self._statistics.get_method_two_sample_pair(
            match_id,
            MethodTwoSampleRequest(
                team_id=target.away_team_id,
                sample_size=configuration.sample_size,
                venue=away_venue,
                season_scope=configuration.season_scope,
                previous_season_id=configuration.previous_season_id,
                metric=configuration.metric,
                component="production",
            ),
        )
        return (
            MethodTwoSeries(
                "home_production",
                configuration.metric,
                "own_real_observation",
                home_production,
            ),
            MethodTwoSeries(
                "away_complement",
                complement_semantic,
                complement_projection,
                away_complement,
            ),
            MethodTwoSeries(
                "away_production",
                configuration.metric,
                "own_real_observation",
                away_production,
            ),
            MethodTwoSeries(
                "home_complement",
                complement_semantic,
                complement_projection,
                home_complement,
            ),
        )

    async def _reference_series(
        self, match_id: int, configuration: MethodTwoConfiguration
    ) -> tuple[MethodTwoSeries, MethodTwoSeries, MethodTwoSeries, MethodTwoSeries]:
        complement_semantic, complement_projection = _COMPLEMENT_SEMANTICS[
            configuration.metric
        ]
        home_venue: Literal["home", "away", "overall"]
        away_venue: Literal["home", "away", "overall"]
        home_venue, away_venue = (
            ("home", "away")
            if configuration.context == "venue"
            else ("overall", "overall")
        )
        (
            home_production,
            home_complement,
        ) = await self._statistics.get_method_two_competition_reference_pair(
            match_id,
            CompetitionReferenceRequest(
                sample_size=configuration.sample_size,
                venue=home_venue,
                season_scope=configuration.season_scope,
                previous_season_id=configuration.previous_season_id,
                metric=configuration.metric,
                component="production",
            ),
        )
        (
            away_production,
            away_complement,
        ) = await self._statistics.get_method_two_competition_reference_pair(
            match_id,
            CompetitionReferenceRequest(
                sample_size=configuration.sample_size,
                venue=away_venue,
                season_scope=configuration.season_scope,
                previous_season_id=configuration.previous_season_id,
                metric=configuration.metric,
                component="complement",
            ),
        )
        return (
            MethodTwoSeries(
                "home_production_reference",
                configuration.metric,
                "own_real_observation",
                home_production,
            ),
            MethodTwoSeries(
                "away_complement_reference",
                complement_semantic,
                complement_projection,
                away_complement,
            ),
            MethodTwoSeries(
                "away_production_reference",
                configuration.metric,
                "own_real_observation",
                away_production,
            ),
            MethodTwoSeries(
                "home_complement_reference",
                complement_semantic,
                complement_projection,
                home_complement,
            ),
        )


def poisson_probability(value: int, rate: float) -> float:
    """The approved Poisson PMF, retained separately from display formatting."""
    if value < 0 or rate < 0:
        raise InvalidQueryError("poisson values must be nonnegative")
    return exp(-rate) * rate**value / factorial(value)


def _validate_configuration(configuration: MethodTwoConfiguration) -> None:
    if configuration.sample_size not in {5, 10, 15, 20}:
        raise InvalidQueryError("unsupported sample size")
    if configuration.context not in {"venue", "overall"}:
        raise InvalidQueryError("unsupported context")
    if configuration.season_scope not in {"current", "current_and_previous"}:
        raise InvalidQueryError("unsupported season scope")
    if configuration.metric not in _COMPLEMENT_SEMANTICS:
        raise InvalidQueryError("unsupported metric")
    if configuration.season_scope == "current" and configuration.previous_season_id:
        raise InvalidQueryError("previous season is unsupported")
    if (
        configuration.season_scope == "current_and_previous"
        and configuration.previous_season_id is None
    ):
        raise InvalidQueryError("previous season is required")


def _blocking_reasons(evidence: MethodTwoEvidence) -> list[str]:
    reasons: list[str] = []
    for series in (
        evidence.home_production,
        evidence.away_complement,
        evidence.away_production,
        evidence.home_complement,
    ):
        if series.sample.mean is None:
            reasons.append(f"{series.name}:no_available_values")
    for series in (
        evidence.home_production_reference,
        evidence.away_complement_reference,
        evidence.away_production_reference,
        evidence.home_complement_reference,
    ):
        if series.sample.mean is None:
            reasons.append(f"{series.name}:no_available_values")
        elif series.sample.mean == 0:
            reasons.append(f"{series.name}:zero_reference_mean")
    return reasons


def _lambda(
    production: StatisticsSample | CompetitionReference,
    complement: StatisticsSample | CompetitionReference,
    production_reference: StatisticsSample | CompetitionReference,
    complement_reference: StatisticsSample | CompetitionReference,
) -> float:
    assert production.mean is not None
    assert complement.mean is not None
    assert production_reference.mean is not None
    assert complement_reference.mean is not None
    return (
        (production.mean / production_reference.mean)
        * (complement.mean / complement_reference.mean)
        * production_reference.mean
    )


def _result(
    evidence: MethodTwoEvidence,
    configuration_fingerprint: str,
    evidence_fingerprint: str,
    status: Literal["completed", "blocked"],
    home_lambda: float | None,
    away_lambda: float | None,
    blocking_reasons: tuple[str, ...],
) -> MethodTwoResult:
    total_lambda = (
        home_lambda + away_lambda
        if home_lambda is not None and away_lambda is not None
        else None
    )
    result_payload = {
        "away_lambda": away_lambda,
        "blocking_reasons": blocking_reasons,
        "configuration_fingerprint": configuration_fingerprint,
        "evidence_fingerprint": evidence_fingerprint,
        "home_lambda": home_lambda,
        "method": METHOD_TWO_NAME,
        "method_version": METHOD_TWO_VERSION,
        "result_schema_version": METHOD_TWO_RESULT_SCHEMA_VERSION,
        "status": status,
        "total_lambda": total_lambda,
    }
    return MethodTwoResult(
        method=METHOD_TWO_NAME,
        method_version=METHOD_TWO_VERSION,
        configuration_schema_version=cast(
            Literal[1], METHOD_TWO_CONFIGURATION_SCHEMA_VERSION
        ),
        result_schema_version=cast(Literal[1], METHOD_TWO_RESULT_SCHEMA_VERSION),
        status=status,
        evidence=evidence,
        configuration_fingerprint=configuration_fingerprint,
        evidence_fingerprint=evidence_fingerprint,
        result_fingerprint=_sha256(result_payload),
        home_lambda=home_lambda,
        away_lambda=away_lambda,
        total_lambda=total_lambda,
        blocking_reasons=blocking_reasons,
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        _canonical(value), allow_nan=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _canonical(value: Any) -> Any:
    if isinstance(value, float):
        return {"$float": value.hex()}
    if isinstance(value, date):
        return value.isoformat()
    if is_dataclass(value):
        return {
            field.name: _canonical(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in value.items()}
    return value
