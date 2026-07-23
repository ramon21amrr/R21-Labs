"""Pure structural Method One contracts. No rate calculation lives here."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum, auto
from typing import Any, Self, cast

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy, is_close
from lvfi_pricing.models.samples import (
    MatchPeriodCode,
    ObservationRole,
    SampleExclusion,
    SampleQuality,
    SampleSnapshot,
    StatisticCode,
    VenueCondition,
)
from lvfi_pricing.models.samples.contracts import COMMON_CONTRACT_VERSION

METHOD_ONE_VERSION = "1.0.0a4"
METHOD_ONE_MULTIPLIER_CATALOG_VERSION = "lvfi-method-one-adjustments@1.0.0"
_SCHEMA_VERSION = 1
_SAFE_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class MethodOneStatisticPeriod(StrEnum):
    GOALS_FIRST_HALF = "goals/first_half"
    GOALS_REGULATION_TIME = "goals/regulation_time"


class MethodOneSeriesRole(StrEnum):
    HOME_PRODUCTION = auto()
    HOME_CONCESSION = auto()
    AWAY_PRODUCTION = auto()
    AWAY_CONCESSION = auto()


class RecencyPolicyCode(StrEnum):
    UNIFORM_V1 = "uniform/v1"


class MultiplierScope(StrEnum):
    MATCH = "MATCH"
    COMPETITION = "COMPETITION"
    GLOBAL = "GLOBAL"


class MultiplierCategory(StrEnum):
    HOME_FIELD_ADVANTAGE = "HOME_FIELD_ADVANTAGE"
    OPPONENT_STRENGTH = "OPPONENT_STRENGTH"
    RECENT_FORM = "RECENT_FORM"
    SQUAD_AVAILABILITY = "SQUAD_AVAILABILITY"
    MATCH_PACE = "MATCH_PACE"
    MUST_WIN = "MUST_WIN"


class MultiplierAppliesTo(StrEnum):
    HOME = "HOME"
    AWAY = "AWAY"


_MULTIPLIER_ORDER = {
    MultiplierCategory.HOME_FIELD_ADVANTAGE: 10,
    MultiplierCategory.OPPONENT_STRENGTH: 20,
    MultiplierCategory.RECENT_FORM: 30,
    MultiplierCategory.SQUAD_AVAILABILITY: 40,
    MultiplierCategory.MATCH_PACE: 50,
    MultiplierCategory.MUST_WIN: 60,
}


def _code(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 128
        or not _SAFE_CODE.fullmatch(value)
    ):
        raise ValueError(f"invalid {field}")
    return value


def _number(value: object, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"invalid {field}")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError(f"invalid {field}")
    return 0.0 if result == 0 else result


def _schema(value: object, field: str, expected: int = _SCHEMA_VERSION) -> int:
    if isinstance(value, bool) or value != expected:
        raise ValueError(f"unsupported {field}")
    return expected


def _items(value: object, field: str, type_: type[object]) -> tuple[object, ...]:
    if not isinstance(value, tuple) or any(
        not isinstance(item, type_) for item in value
    ):
        raise ValueError(f"invalid {field}")
    return value


def _factory[T](
    cls: type[T], code: ErrorCode, field: str, kwargs: dict[str, object]
) -> T | CalculationError:
    try:
        return cls(**cast(Any, kwargs))
    except (TypeError, ValueError):
        return CalculationError(code, f"invalid {field}", field)


def _period(
    statistic: StatisticCode, period: MatchPeriodCode
) -> MethodOneStatisticPeriod:
    if statistic is StatisticCode.GOALS and period is MatchPeriodCode.FIRST_HALF:
        return MethodOneStatisticPeriod.GOALS_FIRST_HALF
    if statistic is StatisticCode.GOALS and period is MatchPeriodCode.REGULATION_TIME:
        return MethodOneStatisticPeriod.GOALS_REGULATION_TIME
    raise ValueError("unsupported statistic period")


def _rank(scope: MultiplierScope) -> int:
    return (
        MultiplierScope.MATCH,
        MultiplierScope.COMPETITION,
        MultiplierScope.GLOBAL,
    ).index(scope)


@dataclass(frozen=True, slots=True)
class MethodOneWeightConfiguration:
    weight_own: float = 0.5
    weight_opponent: float = 0.5
    configuration_version: str = METHOD_ONE_VERSION
    source_scope: MultiplierScope = MultiplierScope.GLOBAL
    configuration_schema_version: int = 1

    def __post_init__(self) -> None:
        own, opponent = (
            _number(self.weight_own, "weight_own"),
            _number(self.weight_opponent, "weight_opponent"),
        )
        if (
            not 0 <= own <= 1
            or not 0 <= opponent <= 1
            or is_close(own + opponent, 1.0, NumericPolicy()) is not True
        ):
            raise ValueError("invalid weights")
        if not isinstance(self.source_scope, MultiplierScope):
            raise ValueError("invalid source scope")
        object.__setattr__(self, "weight_own", own)
        object.__setattr__(self, "weight_opponent", opponent)
        object.__setattr__(
            self,
            "configuration_version",
            _code(self.configuration_version, "configuration_version"),
        )
        _schema(self.configuration_schema_version, "configuration schema")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        return _factory(cls, ErrorCode.INVALID_WEIGHT, "weights", kwargs)


@dataclass(frozen=True, slots=True)
class MethodOneRecencyConfiguration:
    code: RecencyPolicyCode = RecencyPolicyCode.UNIFORM_V1
    policy_version: str = "1"
    normalization_rule: str = "real_denominator"
    tie_break_rule: str = "occurred_at_desc_match_id_asc"
    recency_schema_version: int = 1

    def __post_init__(self) -> None:
        if self.code is not RecencyPolicyCode.UNIFORM_V1:
            raise ValueError("unsupported recency policy")
        for field in ("policy_version", "normalization_rule", "tie_break_rule"):
            object.__setattr__(self, field, _code(getattr(self, field), field))
        _schema(self.recency_schema_version, "recency schema")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        return _factory(cls, ErrorCode.CONFIGURATION_ERROR, "recency", kwargs)


@dataclass(frozen=True, slots=True)
class MethodOneMultiplierCandidate:
    category: MultiplierCategory
    value: float
    scope: MultiplierScope
    applies_to: MultiplierAppliesTo
    statistic: StatisticCode
    period: MatchPeriodCode
    catalog_order: int
    catalog_version: str
    source: str
    justification: str
    target_match_id: str | None = None
    competition_id: str | None = None
    candidate_schema_version: int = 1

    def __post_init__(self) -> None:
        if (
            not isinstance(self.category, MultiplierCategory)
            or not isinstance(self.scope, MultiplierScope)
            or not isinstance(self.applies_to, MultiplierAppliesTo)
            or not isinstance(self.statistic, StatisticCode)
            or not isinstance(self.period, MatchPeriodCode)
        ):
            raise ValueError("invalid multiplier")
        _period(self.statistic, self.period)
        if (
            self.category is MultiplierCategory.HOME_FIELD_ADVANTAGE
            and self.applies_to is not MultiplierAppliesTo.HOME
        ):
            raise ValueError("invalid multiplier destination")
        if (
            isinstance(self.catalog_order, bool)
            or self.catalog_order != _MULTIPLIER_ORDER[self.category]
        ):
            raise ValueError("invalid multiplier order")
        if self.catalog_version != METHOD_ONE_MULTIPLIER_CATALOG_VERSION:
            raise ValueError("unsupported multiplier catalog")
        value = _number(self.value, "value", positive=True)
        if not 0.9 <= value <= 1.1:
            raise ValueError("multiplier outside initial range")
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "source", _code(self.source, "source"))
        object.__setattr__(
            self, "justification", _code(self.justification, "justification")
        )
        if self.scope is MultiplierScope.GLOBAL:
            if self.target_match_id is not None or self.competition_id is not None:
                raise ValueError("global multiplier cannot carry context ids")
        elif self.scope is MultiplierScope.COMPETITION:
            if self.target_match_id is not None or self.competition_id is None:
                raise ValueError("competition multiplier requires competition id")
        elif self.target_match_id is None:
            raise ValueError("match multiplier requires target match id")
        if self.target_match_id is not None:
            object.__setattr__(
                self,
                "target_match_id",
                _code(self.target_match_id, "target_match_id"),
            )
        if self.competition_id is not None:
            object.__setattr__(
                self, "competition_id", _code(self.competition_id, "competition_id")
            )
        _schema(self.candidate_schema_version, "candidate schema")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        return _factory(cls, ErrorCode.INVALID_MULTIPLIER, "multiplier", kwargs)


@dataclass(frozen=True, slots=True)
class MethodOneMultiplierResolution:
    category: MultiplierCategory
    applies_to: MultiplierAppliesTo
    statistic: StatisticCode
    period: MatchPeriodCode
    catalog_order: int
    match_id: str
    competition_id: str
    selected: MethodOneMultiplierCandidate | None = None
    discarded: tuple[MethodOneMultiplierCandidate, ...] = ()
    discard_reasons: tuple[str, ...] = ()
    effective_value: float = 1.0
    effective_scope: MultiplierScope | None = None
    neutral: bool = True
    catalog_version: str = METHOD_ONE_MULTIPLIER_CATALOG_VERSION
    resolution_schema_version: int = 1

    @property
    def key(
        self,
    ) -> tuple[MultiplierCategory, MultiplierAppliesTo, StatisticCode, MatchPeriodCode]:
        return self.category, self.applies_to, self.statistic, self.period

    def __post_init__(self) -> None:
        if (
            not isinstance(self.category, MultiplierCategory)
            or not isinstance(self.applies_to, MultiplierAppliesTo)
            or not isinstance(self.statistic, StatisticCode)
            or not isinstance(self.period, MatchPeriodCode)
            or (
                self.selected is not None
                and not isinstance(self.selected, MethodOneMultiplierCandidate)
            )
        ):
            raise ValueError("invalid resolution")
        _period(self.statistic, self.period)
        if (
            self.catalog_order != _MULTIPLIER_ORDER[self.category]
            or self.catalog_version != METHOD_ONE_MULTIPLIER_CATALOG_VERSION
            or (
                self.category is MultiplierCategory.HOME_FIELD_ADVANTAGE
                and self.applies_to is not MultiplierAppliesTo.HOME
            )
        ):
            raise ValueError("invalid resolution entry")
        object.__setattr__(self, "match_id", _code(self.match_id, "match_id"))
        object.__setattr__(
            self, "competition_id", _code(self.competition_id, "competition_id")
        )
        discarded = cast(
            tuple[MethodOneMultiplierCandidate, ...],
            _items(self.discarded, "discarded", MethodOneMultiplierCandidate),
        )
        reasons = cast(
            tuple[str, ...], _items(self.discard_reasons, "discard_reasons", str)
        )
        candidates = (() if self.selected is None else (self.selected,)) + discarded
        if (
            any(
                (item.category, item.applies_to, item.statistic, item.period)
                != self.key
                for item in candidates
            )
            or len(set(candidates)) != len(candidates)
            or len(reasons) != len(discarded)
            or any(_code(reason, "discard_reason") != reason for reason in reasons)
        ):
            raise ValueError("unresolved multiplier precedence")
        if self.selected is None:
            if (
                discarded
                or self.effective_value != 1.0
                or self.effective_scope is not None
                or self.neutral is not True
            ):
                raise ValueError("invalid neutral resolution")
        elif (
            self.selected.scope
            is not min(candidates, key=lambda item: _rank(item.scope)).scope
            or self.effective_value != self.selected.value
            or self.effective_scope is not self.selected.scope
            or self.neutral is not (self.selected.value == 1.0)
        ):
            raise ValueError("invalid effective multiplier")
        pairs = sorted(
            zip(discarded, reasons, strict=True),
            key=lambda pair: (
                _rank(pair[0].scope),
                pair[0].source,
                pair[0].value,
            ),
        )
        object.__setattr__(self, "discarded", tuple(pair[0] for pair in pairs))
        object.__setattr__(self, "discard_reasons", tuple(pair[1] for pair in pairs))
        _schema(self.resolution_schema_version, "resolution schema")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        return _factory(cls, ErrorCode.INVALID_MULTIPLIER, "resolution", kwargs)


@dataclass(frozen=True, slots=True)
class MethodOneConfiguration:
    configuration_id: str
    home_weights: MethodOneWeightConfiguration = MethodOneWeightConfiguration()
    away_weights: MethodOneWeightConfiguration = MethodOneWeightConfiguration()
    recency: MethodOneRecencyConfiguration = MethodOneRecencyConfiguration()
    multiplier_resolutions: tuple[MethodOneMultiplierResolution, ...] = ()
    formula_version: str = METHOD_ONE_VERSION
    numeric_policy: NumericPolicy = NumericPolicy()
    configuration_version: str = METHOD_ONE_VERSION
    configuration_schema_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "configuration_id", _code(self.configuration_id, "configuration_id")
        )
        if (
            not isinstance(self.home_weights, MethodOneWeightConfiguration)
            or not isinstance(self.away_weights, MethodOneWeightConfiguration)
            or not isinstance(self.recency, MethodOneRecencyConfiguration)
            or not isinstance(self.numeric_policy, NumericPolicy)
        ):
            raise ValueError("invalid configuration")
        resolutions = cast(
            tuple[MethodOneMultiplierResolution, ...],
            _items(
                self.multiplier_resolutions,
                "multiplier_resolutions",
                MethodOneMultiplierResolution,
            ),
        )
        keys = {
            (item.category, item.applies_to, item.statistic, item.period)
            for item in resolutions
        }
        if len(keys) != len(resolutions):
            raise ValueError("duplicate multiplier entry")
        object.__setattr__(
            self,
            "multiplier_resolutions",
            tuple(
                sorted(
                    resolutions,
                    key=lambda item: (
                        item.catalog_order,
                        item.applies_to.value,
                        item.period.value,
                    ),
                )
            ),
        )
        object.__setattr__(
            self, "formula_version", _code(self.formula_version, "formula_version")
        )
        object.__setattr__(
            self,
            "configuration_version",
            _code(self.configuration_version, "configuration_version"),
        )
        _schema(self.configuration_schema_version, "configuration schema")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        return _factory(cls, ErrorCode.CONFIGURATION_ERROR, "configuration", kwargs)


@dataclass(frozen=True, slots=True)
class MethodOneSeriesReference:
    role: MethodOneSeriesRole
    snapshot: SampleSnapshot

    def __post_init__(self) -> None:
        if (
            not isinstance(self.role, MethodOneSeriesRole)
            or not isinstance(self.snapshot, SampleSnapshot)
            or self.snapshot.common_contract_version != COMMON_CONTRACT_VERSION
            or self.snapshot.sample_schema_version != 1
        ):
            raise ValueError("invalid series reference")

    def __hash__(self) -> int:
        raise TypeError("MethodOneSeriesReference is not hashable")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        return _factory(cls, ErrorCode.INCONSISTENT_DATA, "series", kwargs)


_ROLES = tuple(MethodOneSeriesRole)
_CONTEXT = {
    MethodOneSeriesRole.HOME_PRODUCTION: (
        ObservationRole.PRODUCTION,
        VenueCondition.HOME,
        "home_team_id",
    ),
    MethodOneSeriesRole.HOME_CONCESSION: (
        ObservationRole.CONCESSION,
        VenueCondition.HOME,
        "home_team_id",
    ),
    MethodOneSeriesRole.AWAY_PRODUCTION: (
        ObservationRole.PRODUCTION,
        VenueCondition.AWAY,
        "away_team_id",
    ),
    MethodOneSeriesRole.AWAY_CONCESSION: (
        ObservationRole.CONCESSION,
        VenueCondition.AWAY,
        "away_team_id",
    ),
}


@dataclass(frozen=True, slots=True)
class MethodOneRequest:
    match_id: str
    home_team_id: str
    away_team_id: str
    statistic: StatisticCode
    period: MatchPeriodCode
    series_references: tuple[MethodOneSeriesReference, ...]
    configuration: MethodOneConfiguration
    competition_id: str
    data_cutoff_at: datetime | None = None
    method_version: str = METHOD_ONE_VERSION
    request_schema_version: int = 2

    def __post_init__(self) -> None:
        for field in ("match_id", "competition_id", "home_team_id", "away_team_id"):
            object.__setattr__(self, field, _code(getattr(self, field), field))
        if (
            self.home_team_id == self.away_team_id
            or not isinstance(self.statistic, StatisticCode)
            or not isinstance(self.period, MatchPeriodCode)
            or not isinstance(self.configuration, MethodOneConfiguration)
        ):
            raise ValueError("invalid request identity")
        _period(self.statistic, self.period)
        references = cast(
            tuple[MethodOneSeriesReference, ...],
            _items(
                self.series_references, "series_references", MethodOneSeriesReference
            ),
        )
        if len(references) != 4 or {item.role for item in references} != set(_ROLES):
            raise ValueError("four distinct series are required")
        canonical = tuple(sorted(references, key=lambda item: _ROLES.index(item.role)))
        for reference in canonical:
            role, venue, team_field = _CONTEXT[reference.role]
            definition = reference.snapshot.definition
            if (
                definition.observation_role is not role
                or definition.sample_filter.venue_condition is not venue
                or definition.statistic is not self.statistic
                or definition.period is not self.period
                or definition.subject_id != getattr(self, team_field)
            ):
                raise ValueError("inconsistent series context")
        if self.data_cutoff_at is not None:
            if (
                not isinstance(self.data_cutoff_at, datetime)
                or self.data_cutoff_at.tzinfo is None
                or self.data_cutoff_at.utcoffset() is None
            ):
                raise ValueError("invalid data cutoff")
            cutoff = self.data_cutoff_at.astimezone(UTC)
            if any(
                reference.snapshot.definition.cutoff_at > cutoff
                for reference in canonical
            ):
                raise ValueError("snapshot after cutoff")
            object.__setattr__(self, "data_cutoff_at", cutoff)
        object.__setattr__(self, "series_references", canonical)
        object.__setattr__(
            self, "method_version", _code(self.method_version, "method_version")
        )
        if self.method_version != METHOD_ONE_VERSION:
            raise ValueError("unsupported method version")
        _schema(self.request_schema_version, "request schema", 2)

    def __hash__(self) -> int:
        raise TypeError("MethodOneRequest is not hashable")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        return _factory(cls, ErrorCode.INCONSISTENT_DATA, "request", kwargs)


@dataclass(frozen=True, slots=True)
class ContextualAverage:
    sample_id: str
    role: MethodOneSeriesRole
    value: float
    numerator: float
    denominator: float
    valid_count: int
    used_match_ids: tuple[str, ...]
    effective_weights: tuple[float, ...]
    evidence: ContextualAverageEvidence | None = None
    average_schema_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "sample_id", _code(self.sample_id, "sample_id"))
        if (
            not isinstance(self.role, MethodOneSeriesRole)
            or isinstance(self.valid_count, bool)
            or not isinstance(self.valid_count, int)
            or self.valid_count < 1
        ):
            raise ValueError("invalid contextual average")
        for field in ("value", "numerator", "denominator"):
            object.__setattr__(self, field, _number(getattr(self, field), field))
        if self.denominator <= 0:
            raise ValueError("invalid denominator")
        ids = cast(tuple[str, ...], _items(self.used_match_ids, "used_match_ids", str))
        weights = cast(
            tuple[float, ...],
            _items(self.effective_weights, "effective_weights", float),
        )
        if (
            len(ids) != self.valid_count
            or len(weights) != self.valid_count
            or len(set(ids)) != len(ids)
        ):
            raise ValueError("average evidence does not reconcile")
        object.__setattr__(
            self, "used_match_ids", tuple(_code(item, "used_match_ids") for item in ids)
        )
        object.__setattr__(
            self,
            "effective_weights",
            tuple(
                _number(item, "effective_weights", positive=True) for item in weights
            ),
        )
        if self.evidence is not None and not isinstance(
            self.evidence, ContextualAverageEvidence
        ):
            raise ValueError("invalid average evidence")
        _schema(self.average_schema_version, "average schema")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        return _factory(cls, ErrorCode.INVALID_NUMBER, "average", kwargs)


@dataclass(frozen=True, slots=True)
class MethodOneRateExplanation:
    averages: tuple[ContextualAverage, ...]
    home_base_rate: float
    away_base_rate: float
    home_final_rate: float
    away_final_rate: float
    considered_multipliers: tuple[MethodOneMultiplierCandidate, ...] = ()
    discarded_multipliers: tuple[MethodOneMultiplierCandidate, ...] = ()
    warnings: tuple[CalculationWarning, ...] = ()
    formula_version: str = METHOD_ONE_VERSION
    explanation_schema_version: int = 1

    def __post_init__(self) -> None:
        averages = cast(
            tuple[ContextualAverage, ...],
            _items(self.averages, "averages", ContextualAverage),
        )
        if len(averages) != 4 or {item.role for item in averages} != set(_ROLES):
            raise ValueError("four averages are required")
        object.__setattr__(
            self,
            "averages",
            tuple(sorted(averages, key=lambda item: _ROLES.index(item.role))),
        )
        for field in (
            "home_base_rate",
            "away_base_rate",
            "home_final_rate",
            "away_final_rate",
        ):
            object.__setattr__(self, field, _number(getattr(self, field), field))
        for field, type_ in (
            ("considered_multipliers", MethodOneMultiplierCandidate),
            ("discarded_multipliers", MethodOneMultiplierCandidate),
            ("warnings", CalculationWarning),
        ):
            object.__setattr__(self, field, _items(getattr(self, field), field, type_))
        object.__setattr__(
            self, "formula_version", _code(self.formula_version, "formula_version")
        )
        _schema(self.explanation_schema_version, "explanation schema")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        return _factory(cls, ErrorCode.INCONSISTENT_DATA, "explanation", kwargs)


@dataclass(frozen=True, slots=True)
class MethodOneMetadata:
    package_version: str = "1.1.0a9"
    method_version: str = METHOD_ONE_VERSION
    configuration_version: str = METHOD_ONE_VERSION
    data_version: str = "synthetic"
    sample_ids: tuple[str, ...] = ()
    sample_hashes: tuple[str, ...] = ()
    deterministic: bool = True
    warnings_count: int = 0
    metadata_schema_version: int = 1

    def __post_init__(self) -> None:
        for field in (
            "package_version",
            "method_version",
            "configuration_version",
            "data_version",
        ):
            object.__setattr__(self, field, _code(getattr(self, field), field))
        ids, hashes = (
            cast(tuple[str, ...], _items(self.sample_ids, "sample_ids", str)),
            cast(tuple[str, ...], _items(self.sample_hashes, "sample_hashes", str)),
        )
        if (
            len(ids) not in (0, 4)
            or len(ids) != len(hashes)
            or not isinstance(self.deterministic, bool)
            or isinstance(self.warnings_count, bool)
            or not isinstance(self.warnings_count, int)
            or self.warnings_count < 0
        ):
            raise ValueError("invalid metadata")
        object.__setattr__(
            self, "sample_ids", tuple(_code(item, "sample_ids") for item in ids)
        )
        object.__setattr__(
            self,
            "sample_hashes",
            tuple(_code(item, "sample_hashes") for item in hashes),
        )
        _schema(self.metadata_schema_version, "metadata schema")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        return _factory(cls, ErrorCode.INCONSISTENT_DATA, "metadata", kwargs)


@dataclass(frozen=True, slots=True)
class MethodOneResult:
    request: MethodOneRequest
    explanation: MethodOneRateExplanation
    metadata: MethodOneMetadata
    warnings: tuple[CalculationWarning, ...] = ()
    errors: tuple[CalculationError, ...] = ()
    result_schema_version: int = 1

    def __post_init__(self) -> None:
        if (
            not isinstance(self.request, MethodOneRequest)
            or not isinstance(self.explanation, MethodOneRateExplanation)
            or not isinstance(self.metadata, MethodOneMetadata)
        ):
            raise ValueError("invalid result")
        warnings = _items(self.warnings, "warnings", CalculationWarning)
        errors = _items(self.errors, "errors", CalculationError)
        if errors or self.metadata.warnings_count != len(warnings):
            raise ValueError("result evidence does not reconcile")
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(self, "errors", errors)
        _schema(self.result_schema_version, "result schema")

    def __hash__(self) -> int:
        raise TypeError("MethodOneResult is not hashable")

    @classmethod
    def create(cls, **kwargs: object) -> Self | CalculationError:
        return _factory(cls, ErrorCode.INCONSISTENT_DATA, "result", kwargs)


@dataclass(frozen=True, slots=True)
class ContextualAverageEvidence:
    """Immutable audit trail for one contextual average."""

    considered_match_ids: tuple[str, ...]
    exclusions: tuple[SampleExclusion, ...]
    quality: SampleQuality
    statistic: StatisticCode
    period: MatchPeriodCode
    subject_id: str
    opponent_ids: tuple[str, ...]
    venue_condition: VenueCondition
    common_contract_version: str
    recency_policy: RecencyPolicyCode
    calculation_method: str
    deterministic: bool
    used_values: tuple[float, ...]
    warnings: tuple[CalculationWarning, ...]
    errors: tuple[CalculationError, ...]
