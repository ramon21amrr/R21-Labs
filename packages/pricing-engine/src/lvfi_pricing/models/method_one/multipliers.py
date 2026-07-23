"""Versioned, pure multiplier resolution and application for Method One."""

from __future__ import annotations

import math
from dataclasses import dataclass

from lvfi_pricing.core import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.models.samples import (
    MatchPeriodCode,
    SampleQuality,
    StatisticCode,
)

from .base_rates import MethodOneBaseRateResult
from .contracts import (
    METHOD_ONE_MULTIPLIER_CATALOG_VERSION,
    METHOD_ONE_VERSION,
    MethodOneMultiplierCandidate,
    MethodOneMultiplierResolution,
    MultiplierAppliesTo,
    MultiplierCategory,
    MultiplierScope,
    _code,
    _rank,
)

_ALLOWED_PERIODS = (MatchPeriodCode.FIRST_HALF, MatchPeriodCode.REGULATION_TIME)
_ALLOWED_SCOPES = (
    MultiplierScope.GLOBAL,
    MultiplierScope.COMPETITION,
    MultiplierScope.MATCH,
)
_ORDER = {
    MultiplierCategory.HOME_FIELD_ADVANTAGE: 10,
    MultiplierCategory.OPPONENT_STRENGTH: 20,
    MultiplierCategory.RECENT_FORM: 30,
    MultiplierCategory.SQUAD_AVAILABILITY: 40,
    MultiplierCategory.MATCH_PACE: 50,
    MultiplierCategory.MUST_WIN: 60,
}
_DESTINATIONS = {
    MultiplierCategory.HOME_FIELD_ADVANTAGE: (MultiplierAppliesTo.HOME,),
    MultiplierCategory.OPPONENT_STRENGTH: tuple(MultiplierAppliesTo),
    MultiplierCategory.RECENT_FORM: tuple(MultiplierAppliesTo),
    MultiplierCategory.SQUAD_AVAILABILITY: tuple(MultiplierAppliesTo),
    MultiplierCategory.MATCH_PACE: tuple(MultiplierAppliesTo),
    MultiplierCategory.MUST_WIN: tuple(MultiplierAppliesTo),
}


def _error(code: ErrorCode, message: str, field: str) -> CalculationError:
    return CalculationError(code, message, field)


@dataclass(frozen=True, slots=True)
class MethodOneMultiplierCatalogEntry:
    category: MultiplierCategory
    applies_to: MultiplierAppliesTo
    statistic: StatisticCode
    period: MatchPeriodCode
    order: int
    minimum: float = 0.9
    maximum: float = 1.1
    allowed_scopes: tuple[MultiplierScope, ...] = _ALLOWED_SCOPES
    entry_schema_version: int = 1

    @property
    def key(
        self,
    ) -> tuple[MultiplierCategory, MultiplierAppliesTo, StatisticCode, MatchPeriodCode]:
        return self.category, self.applies_to, self.statistic, self.period

    def __post_init__(self) -> None:
        if (
            not isinstance(self.category, MultiplierCategory)
            or not isinstance(self.applies_to, MultiplierAppliesTo)
            or self.applies_to not in _DESTINATIONS[self.category]
            or self.statistic is not StatisticCode.GOALS
            or self.period not in _ALLOWED_PERIODS
            or isinstance(self.order, bool)
            or self.order != _ORDER[self.category]
            or self.minimum != 0.9
            or self.maximum != 1.1
            or self.allowed_scopes != _ALLOWED_SCOPES
            or self.entry_schema_version != 1
        ):
            raise ValueError("invalid multiplier catalog entry")


@dataclass(frozen=True, slots=True)
class MethodOneMultiplierCatalog:
    catalog_version: str
    entries: tuple[MethodOneMultiplierCatalogEntry, ...]
    catalog_schema_version: int = 1

    def __post_init__(self) -> None:
        if (
            self.catalog_version != METHOD_ONE_MULTIPLIER_CATALOG_VERSION
            or not isinstance(self.entries, tuple)
            or any(
                not isinstance(item, MethodOneMultiplierCatalogEntry)
                for item in self.entries
            )
            or self.catalog_schema_version != 1
        ):
            raise ValueError("invalid multiplier catalog")
        keys = tuple(item.key for item in self.entries)
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate multiplier catalog entry")
        object.__setattr__(
            self,
            "entries",
            tuple(
                sorted(
                    self.entries,
                    key=lambda item: (
                        item.period.value,
                        item.order,
                        item.applies_to.value,
                    ),
                )
            ),
        )


def _approved_entries() -> tuple[MethodOneMultiplierCatalogEntry, ...]:
    return tuple(
        MethodOneMultiplierCatalogEntry(
            category, applies_to, StatisticCode.GOALS, period, _ORDER[category]
        )
        for period in _ALLOWED_PERIODS
        for category in MultiplierCategory
        for applies_to in _DESTINATIONS[category]
    )


METHOD_ONE_MULTIPLIER_CATALOG = MethodOneMultiplierCatalog(
    METHOD_ONE_MULTIPLIER_CATALOG_VERSION,
    _approved_entries(),
)


def _candidate_key(
    candidate: MethodOneMultiplierCandidate,
) -> tuple[MultiplierCategory, MultiplierAppliesTo, StatisticCode, MatchPeriodCode]:
    return (
        candidate.category,
        candidate.applies_to,
        candidate.statistic,
        candidate.period,
    )


def _validate_candidate_context(
    candidate: MethodOneMultiplierCandidate,
    match_id: str,
    competition_id: str,
) -> CalculationError | None:
    if candidate.scope is MultiplierScope.MATCH:
        if candidate.target_match_id != match_id or (
            candidate.competition_id is not None
            and candidate.competition_id != competition_id
        ):
            return _error(
                ErrorCode.INCONSISTENT_DATA,
                "match multiplier context does not match calculation",
                "candidates",
            )
    elif (
        candidate.scope is MultiplierScope.COMPETITION
        and candidate.competition_id != competition_id
    ):
        return _error(
            ErrorCode.INCONSISTENT_DATA,
            "competition multiplier context does not match calculation",
            "candidates",
        )
    return None


def resolve_method_one_multipliers(
    candidates: tuple[MethodOneMultiplierCandidate, ...],
    *,
    match_id: str,
    competition_id: str,
    statistic: StatisticCode,
    period: MatchPeriodCode,
    catalog: MethodOneMultiplierCatalog = METHOD_ONE_MULTIPLIER_CATALOG,
) -> tuple[MethodOneMultiplierResolution, ...] | CalculationError:
    """Resolve one effective candidate per catalog entry and preserve the trace."""
    try:
        match_id = _code(match_id, "match_id")
        competition_id = _code(competition_id, "competition_id")
    except ValueError:
        return _error(
            ErrorCode.INCONSISTENT_DATA, "invalid calculation context", "context"
        )
    if not isinstance(candidates, tuple) or any(
        not isinstance(item, MethodOneMultiplierCandidate) for item in candidates
    ):
        return _error(
            ErrorCode.INVALID_MULTIPLIER,
            "candidates must be an immutable tuple",
            "candidates",
        )
    if catalog != METHOD_ONE_MULTIPLIER_CATALOG:
        return _error(
            ErrorCode.SCHEMA_VERSION_UNSUPPORTED,
            "unsupported multiplier catalog",
            "catalog",
        )
    if statistic is not StatisticCode.GOALS or period not in _ALLOWED_PERIODS:
        return _error(
            ErrorCode.MODEL_NOT_APPLICABLE,
            "unsupported statistic or period",
            "candidates",
        )
    if len(set(candidates)) != len(candidates):
        return _error(
            ErrorCode.INVALID_MULTIPLIER, "duplicate multiplier candidate", "candidates"
        )
    active_keys = {
        entry.key
        for entry in catalog.entries
        if entry.statistic is statistic and entry.period is period
    }
    scope_keys: set[tuple[object, ...]] = set()
    for candidate in candidates:
        if (
            candidate.candidate_schema_version != 1
            or candidate.catalog_version != catalog.catalog_version
            or _candidate_key(candidate) not in active_keys
            or candidate.catalog_order != _ORDER[candidate.category]
        ):
            return _error(
                ErrorCode.INVALID_MULTIPLIER,
                "candidate does not match catalog",
                "candidates",
            )
        if error := _validate_candidate_context(candidate, match_id, competition_id):
            return error
        scope_key = (*_candidate_key(candidate), candidate.scope)
        if scope_key in scope_keys:
            return _error(
                ErrorCode.INVALID_MULTIPLIER,
                "ambiguous candidate precedence",
                "candidates",
            )
        scope_keys.add(scope_key)
    resolutions: list[MethodOneMultiplierResolution] = []
    entries = tuple(
        entry
        for entry in catalog.entries
        if entry.statistic is statistic and entry.period is period
    )
    for entry in entries:
        compatible = tuple(
            sorted(
                (item for item in candidates if _candidate_key(item) == entry.key),
                key=lambda item: (_rank(item.scope), item.source, item.value),
            )
        )
        if not compatible:
            resolutions.append(
                MethodOneMultiplierResolution(
                    entry.category,
                    entry.applies_to,
                    statistic,
                    period,
                    entry.order,
                    match_id,
                    competition_id,
                )
            )
            continue
        selected, discarded = compatible[0], compatible[1:]
        resolutions.append(
            MethodOneMultiplierResolution(
                entry.category,
                entry.applies_to,
                statistic,
                period,
                entry.order,
                match_id,
                competition_id,
                selected,
                discarded,
                tuple("lower_precedence" for _ in discarded),
                selected.value,
                selected.scope,
                selected.value == 1.0,
            )
        )
    return tuple(resolutions)


@dataclass(frozen=True, slots=True)
class MethodOneMultiplierApplicationStep:
    resolution: MethodOneMultiplierResolution
    rate_before: float
    rate_after: float


@dataclass(frozen=True, slots=True)
class MethodOneAdjustedRateExplanation:
    home_base_rate: float
    away_base_rate: float
    home_steps: tuple[MethodOneMultiplierApplicationStep, ...]
    away_steps: tuple[MethodOneMultiplierApplicationStep, ...]
    home_adjusted_rate: float
    away_adjusted_rate: float
    resolutions: tuple[MethodOneMultiplierResolution, ...]
    quality: SampleQuality
    warnings: tuple[CalculationWarning, ...]
    blockers: tuple[CalculationError, ...]
    catalog_version: str = METHOD_ONE_MULTIPLIER_CATALOG_VERSION
    formula: str = "refined_rate=base_rate*math.prod(multiplier_i)"
    explanation_schema_version: int = 1
    deterministic: bool = True


@dataclass(frozen=True, slots=True)
class MethodOneAdjustedRateResult:
    match_id: str
    competition_id: str
    home_team_id: str
    away_team_id: str
    statistic: StatisticCode
    period: MatchPeriodCode
    home_base_rate: float
    away_base_rate: float
    home_adjusted_rate: float
    away_adjusted_rate: float
    resolutions: tuple[MethodOneMultiplierResolution, ...]
    quality: SampleQuality
    warnings: tuple[CalculationWarning, ...]
    blockers: tuple[CalculationError, ...]
    explanation: MethodOneAdjustedRateExplanation
    method_version: str = METHOD_ONE_VERSION
    adjusted_rate_schema_version: int = 1
    deterministic: bool = True

    @property
    def effective_multipliers(self) -> tuple[float, ...]:
        return tuple(item.effective_value for item in self.resolutions)

    @property
    def selected_candidates(self) -> tuple[MethodOneMultiplierCandidate, ...]:
        return tuple(
            item.selected for item in self.resolutions if item.selected is not None
        )

    @property
    def discarded_candidates(self) -> tuple[MethodOneMultiplierCandidate, ...]:
        return tuple(
            item for resolution in self.resolutions for item in resolution.discarded
        )

    @property
    def application_order(self) -> tuple[int, ...]:
        return tuple(item.catalog_order for item in self.resolutions)


def _apply_side(
    base_rate: float,
    resolutions: tuple[MethodOneMultiplierResolution, ...],
) -> tuple[float, tuple[MethodOneMultiplierApplicationStep, ...]] | CalculationError:
    if (
        isinstance(base_rate, bool)
        or not isinstance(base_rate, (int, float))
        or not math.isfinite(base_rate)
        or base_rate < 0
    ):
        return _error(ErrorCode.INVALID_NUMBER, "invalid base rate", "base_rate")
    factors: list[float] = []
    steps: list[MethodOneMultiplierApplicationStep] = []
    normalized_base = 0.0 if base_rate == 0 else float(base_rate)
    before = normalized_base
    for resolution in resolutions:
        factors.append(resolution.effective_value)
        after = normalized_base * math.prod(factors)
        if not math.isfinite(after) or after < 0:
            return _error(
                ErrorCode.INVALID_NUMBER, "invalid adjusted rate", "adjusted_rate"
            )
        after = 0.0 if after == 0 else after
        steps.append(MethodOneMultiplierApplicationStep(resolution, before, after))
        before = after
    return before, tuple(steps)


def apply_method_one_multipliers(
    base_rates: MethodOneBaseRateResult,
    resolutions: tuple[MethodOneMultiplierResolution, ...],
) -> MethodOneAdjustedRateResult | CalculationError:
    """Apply resolved factors by destination and catalog order without I/O."""
    if not isinstance(base_rates, MethodOneBaseRateResult):
        return _error(
            ErrorCode.INCONSISTENT_DATA, "invalid base-rate result", "base_rates"
        )
    if (
        base_rates.method_version != METHOD_ONE_VERSION
        or base_rates.result_schema_version != 2
    ):
        return _error(
            ErrorCode.SCHEMA_VERSION_UNSUPPORTED,
            "unsupported base-rate result",
            "base_rates",
        )
    if not base_rates.quality.calculation_allowed:
        return _error(
            ErrorCode.MODEL_NOT_APPLICABLE, "base-rate result is blocked", "base_rates"
        )
    if not isinstance(resolutions, tuple) or any(
        not isinstance(item, MethodOneMultiplierResolution) for item in resolutions
    ):
        return _error(
            ErrorCode.INVALID_MULTIPLIER, "invalid resolutions", "resolutions"
        )
    expected = tuple(
        entry.key
        for entry in METHOD_ONE_MULTIPLIER_CATALOG.entries
        if entry.statistic is base_rates.statistic and entry.period is base_rates.period
    )
    actual = tuple(item.key for item in resolutions)
    if actual != expected or any(
        item.match_id != base_rates.match_id
        or item.competition_id != base_rates.competition_id
        or item.catalog_version != METHOD_ONE_MULTIPLIER_CATALOG_VERSION
        or item.resolution_schema_version != 1
        for item in resolutions
    ):
        return _error(
            ErrorCode.INVALID_MULTIPLIER,
            "resolutions do not match base-rate context",
            "resolutions",
        )
    home_resolutions = tuple(
        item for item in resolutions if item.applies_to is MultiplierAppliesTo.HOME
    )
    away_resolutions = tuple(
        item for item in resolutions if item.applies_to is MultiplierAppliesTo.AWAY
    )
    home = _apply_side(base_rates.home_base_rate, home_resolutions)
    if isinstance(home, CalculationError):
        return home
    away = _apply_side(base_rates.away_base_rate, away_resolutions)
    if isinstance(away, CalculationError):
        return away
    blockers = base_rates.quality.errors
    explanation = MethodOneAdjustedRateExplanation(
        base_rates.home_base_rate,
        base_rates.away_base_rate,
        home[1],
        away[1],
        home[0],
        away[0],
        resolutions,
        base_rates.quality,
        base_rates.warnings,
        blockers,
    )
    return MethodOneAdjustedRateResult(
        base_rates.match_id,
        base_rates.competition_id,
        base_rates.home_team_id,
        base_rates.away_team_id,
        base_rates.statistic,
        base_rates.period,
        base_rates.home_base_rate,
        base_rates.away_base_rate,
        home[0],
        away[0],
        resolutions,
        base_rates.quality,
        base_rates.warnings,
        blockers,
        explanation,
    )
