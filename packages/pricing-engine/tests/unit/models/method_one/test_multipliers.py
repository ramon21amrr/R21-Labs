from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from lvfi_pricing.core import CalculationError, ErrorCode
from lvfi_pricing.models.method_one import (
    METHOD_ONE_MULTIPLIER_CATALOG,
    METHOD_ONE_MULTIPLIER_CATALOG_VERSION,
    MethodOneAdjustedRateResult,
    MethodOneConfiguration,
    MethodOneMultiplierCandidate,
    MethodOneMultiplierCatalog,
    MethodOneMultiplierCatalogEntry,
    MethodOneMultiplierResolution,
    MultiplierAppliesTo,
    MultiplierCategory,
    MultiplierScope,
    apply_method_one_multipliers,
    resolve_method_one_multipliers,
)
from lvfi_pricing.models.method_one import multipliers as implementation
from lvfi_pricing.models.samples import MatchPeriodCode, StatisticCode
from tests.unit.models.method_one.test_base_rates import averages, result


def candidate(
    category: MultiplierCategory = MultiplierCategory.RECENT_FORM,
    value: object = 1.05,
    scope: MultiplierScope = MultiplierScope.GLOBAL,
    applies_to: MultiplierAppliesTo = MultiplierAppliesTo.HOME,
    *,
    statistic: StatisticCode = StatisticCode.GOALS,
    period: MatchPeriodCode = MatchPeriodCode.REGULATION_TIME,
    order: int | None = None,
    catalog_version: str = METHOD_ONE_MULTIPLIER_CATALOG_VERSION,
    source: str = "source",
    justification: str = "reason",
    target_match_id: str | None = None,
    competition_id: str | None = None,
) -> MethodOneMultiplierCandidate:
    if order is None:
        order = {
            MultiplierCategory.HOME_FIELD_ADVANTAGE: 10,
            MultiplierCategory.OPPONENT_STRENGTH: 20,
            MultiplierCategory.RECENT_FORM: 30,
            MultiplierCategory.SQUAD_AVAILABILITY: 40,
            MultiplierCategory.MATCH_PACE: 50,
            MultiplierCategory.MUST_WIN: 60,
        }[category]
    if scope is MultiplierScope.MATCH and target_match_id is None:
        target_match_id = "target"
    if scope is MultiplierScope.COMPETITION and competition_id is None:
        competition_id = "competition"
    return MethodOneMultiplierCandidate(
        category,
        cast(float, value),
        scope,
        applies_to,
        statistic,
        period,
        order,
        catalog_version,
        source,
        justification,
        target_match_id,
        competition_id,
    )


def resolved(
    *candidates: MethodOneMultiplierCandidate,
    statistic: StatisticCode = StatisticCode.GOALS,
    period: MatchPeriodCode = MatchPeriodCode.REGULATION_TIME,
) -> tuple[MethodOneMultiplierResolution, ...]:
    value = resolve_method_one_multipliers(
        candidates,
        match_id="target",
        competition_id="competition",
        statistic=statistic,
        period=period,
    )
    assert isinstance(value, tuple)
    return value


def failure(value: object) -> CalculationError:
    assert isinstance(value, CalculationError)
    return value


def test_catalog_is_complete_versioned_canonical_and_immutable() -> None:
    catalog = METHOD_ONE_MULTIPLIER_CATALOG
    assert catalog.catalog_version == "lvfi-method-one-adjustments@1.0.0"
    assert catalog.catalog_schema_version == 1
    assert len(catalog.entries) == 22
    assert len({entry.key for entry in catalog.entries}) == 22
    assert all(
        entry.minimum == 0.9 and entry.maximum == 1.1 for entry in catalog.entries
    )
    assert all(entry.statistic is StatisticCode.GOALS for entry in catalog.entries)
    hfa = [
        entry
        for entry in catalog.entries
        if entry.category is MultiplierCategory.HOME_FIELD_ADVANTAGE
    ]
    assert len(hfa) == 2
    assert {entry.applies_to for entry in hfa} == {MultiplierAppliesTo.HOME}
    assert tuple(entry.order for entry in catalog.entries) == tuple(
        entry.order
        for entry in sorted(
            catalog.entries,
            key=lambda item: (item.period.value, item.order, item.applies_to.value),
        )
    )
    with pytest.raises(FrozenInstanceError):
        catalog.catalog_version = "other"  # type: ignore[misc]


def test_catalog_rejects_invalid_entries_and_duplicates() -> None:
    entry = METHOD_ONE_MULTIPLIER_CATALOG.entries[0]
    with pytest.raises(ValueError):
        MethodOneMultiplierCatalog("bad", (entry,))
    with pytest.raises(ValueError):
        MethodOneMultiplierCatalog(
            METHOD_ONE_MULTIPLIER_CATALOG_VERSION, cast(Any, [entry])
        )
    with pytest.raises(ValueError):
        MethodOneMultiplierCatalog(
            METHOD_ONE_MULTIPLIER_CATALOG_VERSION, (entry, entry)
        )
    with pytest.raises(ValueError):
        MethodOneMultiplierCatalog(
            METHOD_ONE_MULTIPLIER_CATALOG_VERSION, (cast(Any, object()),)
        )
    for kwargs in (
        {"category": cast(Any, object())},
        {"applies_to": cast(Any, object())},
        {"applies_to": MultiplierAppliesTo.AWAY},
        {"statistic": StatisticCode.CORNERS},
        {"period": cast(Any, object())},
        {"order": True},
        {"order": 99},
        {"minimum": 0.8},
        {"maximum": 1.2},
        {"allowed_scopes": ()},
        {"entry_schema_version": 2},
    ):
        values: dict[str, object] = {
            "category": MultiplierCategory.HOME_FIELD_ADVANTAGE,
            "applies_to": MultiplierAppliesTo.HOME,
            "statistic": StatisticCode.GOALS,
            "period": MatchPeriodCode.FIRST_HALF,
            "order": 10,
        }
        values.update(kwargs)
        with pytest.raises((KeyError, TypeError, ValueError)):
            MethodOneMultiplierCatalogEntry(**cast(Any, values))


def test_candidate_contract_validates_catalog_and_context_shapes() -> None:
    assert candidate(value=0.9).value == 0.9
    assert candidate(value=1.1).value == 1.1
    assert candidate(value=1.0).value == 1.0
    assert candidate(scope=MultiplierScope.MATCH).target_match_id == "target"
    assert candidate(scope=MultiplierScope.COMPETITION).competition_id == "competition"
    assert (
        candidate(
            scope=MultiplierScope.MATCH, competition_id="competition"
        ).competition_id
        == "competition"
    )
    assert isinstance(
        MethodOneMultiplierCandidate.create(category=object()), CalculationError
    )
    with pytest.raises(FrozenInstanceError):
        candidate().value = 1.0  # type: ignore[misc]


@pytest.mark.parametrize(
    "value", [0.0, -1.0, True, float("nan"), float("inf"), 0.89, 1.11]
)
def test_candidate_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ValueError):
        candidate(value=value)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"category": cast(Any, object())},
        {"scope": cast(Any, object())},
        {"applies_to": cast(Any, object())},
        {"statistic": cast(Any, object())},
        {"period": cast(Any, object())},
        {
            "category": MultiplierCategory.HOME_FIELD_ADVANTAGE,
            "applies_to": MultiplierAppliesTo.AWAY,
        },
        {"order": True},
        {"order": 99},
        {"catalog_version": "bad"},
        {"source": ""},
        {"justification": ""},
    ],
)
def test_candidate_rejects_invalid_catalog_fields(kwargs: dict[str, object]) -> None:
    with pytest.raises((KeyError, TypeError, ValueError)):
        candidate(**cast(Any, kwargs))


def test_candidate_rejects_incoherent_scope_ids_and_schema() -> None:
    with pytest.raises(ValueError):
        candidate(target_match_id="target")
    with pytest.raises(ValueError):
        candidate(competition_id="competition")
    with pytest.raises(ValueError):
        candidate(scope=MultiplierScope.COMPETITION, target_match_id="target")
    with pytest.raises(ValueError):
        MethodOneMultiplierCandidate(
            MultiplierCategory.RECENT_FORM,
            1.0,
            MultiplierScope.COMPETITION,
            MultiplierAppliesTo.HOME,
            StatisticCode.GOALS,
            MatchPeriodCode.REGULATION_TIME,
            30,
            METHOD_ONE_MULTIPLIER_CATALOG_VERSION,
            "source",
            "reason",
        )
    with pytest.raises(ValueError):
        MethodOneMultiplierCandidate(
            MultiplierCategory.RECENT_FORM,
            1.0,
            MultiplierScope.MATCH,
            MultiplierAppliesTo.HOME,
            StatisticCode.GOALS,
            MatchPeriodCode.REGULATION_TIME,
            30,
            METHOD_ONE_MULTIPLIER_CATALOG_VERSION,
            "source",
            "reason",
        )
    with pytest.raises(ValueError):
        candidate(scope=MultiplierScope.MATCH, target_match_id="bad id")
    value = candidate()
    object.__setattr__(value, "candidate_schema_version", 2)
    assert (
        failure(
            resolve_method_one_multipliers(
                (value,),
                match_id="target",
                competition_id="competition",
                statistic=StatisticCode.GOALS,
                period=MatchPeriodCode.REGULATION_TIME,
            )
        ).code
        is ErrorCode.INVALID_MULTIPLIER
    )


def test_resolution_neutrality_precedence_and_discard_audit() -> None:
    neutral = resolved()
    assert len(neutral) == 11
    assert all(
        item.selected is None and item.neutral and item.effective_value == 1.0
        for item in neutral
    )
    global_ = candidate(value=0.95)
    competition = candidate(value=1.02, scope=MultiplierScope.COMPETITION)
    match = candidate(value=1.08, scope=MultiplierScope.MATCH)
    values = resolved(global_, competition, match)
    chosen = next(
        item
        for item in values
        if item.key == (match.category, match.applies_to, match.statistic, match.period)
    )
    assert chosen.selected is match
    assert chosen.effective_scope is MultiplierScope.MATCH
    assert chosen.discarded == (competition, global_)
    assert chosen.discard_reasons == ("lower_precedence", "lower_precedence")


def test_resolution_is_independent_of_input_order_and_side() -> None:
    home = candidate(value=1.1)
    away = candidate(value=0.9, applies_to=MultiplierAppliesTo.AWAY)
    first = resolved(home, away)
    second = resolved(away, home)
    assert first == second
    assert [item.selected for item in first if item.selected is not None] == [
        away,
        home,
    ]


def test_resolution_rejects_collection_duplicates_ambiguity_and_context() -> None:
    value = candidate()
    assert (
        failure(
            resolve_method_one_multipliers(
                cast(Any, [value]),
                match_id="target",
                competition_id="competition",
                statistic=StatisticCode.GOALS,
                period=MatchPeriodCode.REGULATION_TIME,
            )
        ).code
        is ErrorCode.INVALID_MULTIPLIER
    )
    assert (
        failure(
            resolve_method_one_multipliers(
                (cast(Any, object()),),
                match_id="target",
                competition_id="competition",
                statistic=StatisticCode.GOALS,
                period=MatchPeriodCode.REGULATION_TIME,
            )
        ).code
        is ErrorCode.INVALID_MULTIPLIER
    )
    assert (
        failure(
            resolve_method_one_multipliers(
                (value, value),
                match_id="target",
                competition_id="competition",
                statistic=StatisticCode.GOALS,
                period=MatchPeriodCode.REGULATION_TIME,
            )
        ).code
        is ErrorCode.INVALID_MULTIPLIER
    )
    other = candidate(value=1.06, source="other")
    assert (
        failure(
            resolve_method_one_multipliers(
                (value, other),
                match_id="target",
                competition_id="competition",
                statistic=StatisticCode.GOALS,
                period=MatchPeriodCode.REGULATION_TIME,
            )
        ).code
        is ErrorCode.INVALID_MULTIPLIER
    )
    wrong_match = candidate(scope=MultiplierScope.MATCH, target_match_id="other")
    assert (
        failure(
            resolve_method_one_multipliers(
                (wrong_match,),
                match_id="target",
                competition_id="competition",
                statistic=StatisticCode.GOALS,
                period=MatchPeriodCode.REGULATION_TIME,
            )
        ).code
        is ErrorCode.INCONSISTENT_DATA
    )
    wrong_match_competition = candidate(
        scope=MultiplierScope.MATCH, competition_id="other"
    )
    assert (
        failure(
            resolve_method_one_multipliers(
                (wrong_match_competition,),
                match_id="target",
                competition_id="competition",
                statistic=StatisticCode.GOALS,
                period=MatchPeriodCode.REGULATION_TIME,
            )
        ).code
        is ErrorCode.INCONSISTENT_DATA
    )
    wrong_competition = candidate(
        scope=MultiplierScope.COMPETITION, competition_id="other"
    )
    assert (
        failure(
            resolve_method_one_multipliers(
                (wrong_competition,),
                match_id="target",
                competition_id="competition",
                statistic=StatisticCode.GOALS,
                period=MatchPeriodCode.REGULATION_TIME,
            )
        ).code
        is ErrorCode.INCONSISTENT_DATA
    )


def test_resolution_rejects_unsupported_context_catalog_and_mutation() -> None:
    assert (
        failure(
            resolve_method_one_multipliers(
                (),
                match_id="bad id",
                competition_id="competition",
                statistic=StatisticCode.GOALS,
                period=MatchPeriodCode.REGULATION_TIME,
            )
        ).code
        is ErrorCode.INCONSISTENT_DATA
    )
    assert (
        failure(
            resolve_method_one_multipliers(
                (),
                match_id="target",
                competition_id="competition",
                statistic=StatisticCode.CORNERS,
                period=MatchPeriodCode.REGULATION_TIME,
            )
        ).code
        is ErrorCode.MODEL_NOT_APPLICABLE
    )
    partial = MethodOneMultiplierCatalog(
        METHOD_ONE_MULTIPLIER_CATALOG_VERSION, METHOD_ONE_MULTIPLIER_CATALOG.entries[:1]
    )
    assert (
        failure(
            resolve_method_one_multipliers(
                (),
                match_id="target",
                competition_id="competition",
                statistic=StatisticCode.GOALS,
                period=MatchPeriodCode.REGULATION_TIME,
                catalog=partial,
            )
        ).code
        is ErrorCode.SCHEMA_VERSION_UNSUPPORTED
    )
    value = candidate()
    object.__setattr__(value, "catalog_order", 99)
    assert (
        failure(
            resolve_method_one_multipliers(
                (value,),
                match_id="target",
                competition_id="competition",
                statistic=StatisticCode.GOALS,
                period=MatchPeriodCode.REGULATION_TIME,
            )
        ).code
        is ErrorCode.INVALID_MULTIPLIER
    )


def test_resolution_contract_rejects_incoherent_manual_values() -> None:
    value = candidate()
    base = resolved(value)[5]
    assert isinstance(MethodOneMultiplierResolution.create(), CalculationError)
    with pytest.raises(ValueError):
        MethodOneMultiplierResolution(
            cast(Any, object()),
            base.applies_to,
            base.statistic,
            base.period,
            base.catalog_order,
            "target",
            "competition",
        )
    with pytest.raises(ValueError):
        MethodOneMultiplierResolution(
            base.category,
            cast(Any, object()),
            base.statistic,
            base.period,
            base.catalog_order,
            "target",
            "competition",
        )
    with pytest.raises(ValueError):
        MethodOneMultiplierResolution(
            base.category,
            base.applies_to,
            base.statistic,
            base.period,
            99,
            "target",
            "competition",
        )
    with pytest.raises(ValueError):
        MethodOneMultiplierResolution(
            base.category,
            base.applies_to,
            base.statistic,
            base.period,
            base.catalog_order,
            "bad id",
            "competition",
        )
    with pytest.raises(ValueError):
        MethodOneMultiplierResolution(
            base.category,
            base.applies_to,
            base.statistic,
            base.period,
            base.catalog_order,
            "target",
            "competition",
            None,
            (value,),
            ("reason",),
        )
    with pytest.raises(ValueError):
        MethodOneMultiplierResolution(
            base.category,
            base.applies_to,
            base.statistic,
            base.period,
            base.catalog_order,
            "target",
            "competition",
            value,
            (),
            (),
            1.0,
            MultiplierScope.GLOBAL,
            True,
        )
    with pytest.raises(ValueError):
        MethodOneMultiplierResolution(
            base.category,
            base.applies_to,
            base.statistic,
            base.period,
            base.catalog_order,
            "target",
            "competition",
            effective_value=1.1,
        )
    selected = next(item for item in resolved(value) if item.selected is not None)
    with pytest.raises(ValueError):
        MethodOneMultiplierResolution(
            selected.category,
            selected.applies_to,
            selected.statistic,
            selected.period,
            selected.catalog_order,
            "target",
            "competition",
            selected.selected,
            effective_value=1.0,
            effective_scope=selected.effective_scope,
            neutral=False,
        )
    assert isinstance(
        MethodOneConfiguration.create(
            configuration_id="duplicate",
            multiplier_resolutions=(selected, selected),
        ),
        CalculationError,
    )
    assert isinstance(MethodOneConfiguration.create(), CalculationError)


def test_application_applies_each_side_in_catalog_order_and_audits_steps() -> None:
    base = result()
    home_hfa = candidate(
        MultiplierCategory.HOME_FIELD_ADVANTAGE,
        1.1,
        applies_to=MultiplierAppliesTo.HOME,
    )
    home_form = candidate(
        MultiplierCategory.RECENT_FORM, 0.9, applies_to=MultiplierAppliesTo.HOME
    )
    away_form = candidate(
        MultiplierCategory.RECENT_FORM, 1.05, applies_to=MultiplierAppliesTo.AWAY
    )
    resolutions = resolved(home_hfa, home_form, away_form)
    adjusted = apply_method_one_multipliers(base, resolutions)
    assert isinstance(adjusted, MethodOneAdjustedRateResult)
    assert adjusted.home_adjusted_rate == base.home_base_rate * 1.1 * 0.9
    assert adjusted.away_adjusted_rate == base.away_base_rate * 1.05
    assert adjusted.selected_candidates == (home_hfa, away_form, home_form)
    assert adjusted.effective_multipliers == tuple(
        item.effective_value for item in resolutions
    )
    assert adjusted.discarded_candidates == ()
    assert adjusted.application_order == tuple(
        item.catalog_order for item in resolutions
    )
    assert adjusted.explanation.home_steps[0].rate_before == base.home_base_rate
    assert adjusted.explanation.home_steps[-1].rate_after == adjusted.home_adjusted_rate
    assert adjusted.explanation.away_steps[-1].rate_after == adjusted.away_adjusted_rate
    assert (
        adjusted.explanation.formula == "refined_rate=base_rate*math.prod(multiplier_i)"
    )
    assert adjusted.method_version == "1.0.0a5"
    assert adjusted.adjusted_rate_schema_version == 1
    with pytest.raises(FrozenInstanceError):
        adjusted.home_adjusted_rate = 0.0  # type: ignore[misc]


def test_application_neutral_zero_and_quality_are_inherited() -> None:
    base = result(averages((0.0, 0.0, 0.0, 0.0), counts=(5, 10, 10, 10)))
    adjusted = apply_method_one_multipliers(base, resolved())
    assert isinstance(adjusted, MethodOneAdjustedRateResult)
    assert (adjusted.home_adjusted_rate, adjusted.away_adjusted_rate) == (0.0, 0.0)
    assert adjusted.quality is base.quality
    assert adjusted.warnings is base.warnings
    assert adjusted.blockers == base.quality.errors
    assert adjusted.explanation.quality is base.quality


def test_application_rejects_invalid_shapes_versions_context_and_blocking() -> None:
    base = result()
    values = resolved()
    assert (
        failure(apply_method_one_multipliers(cast(Any, object()), values)).code
        is ErrorCode.INCONSISTENT_DATA
    )
    altered = result()
    object.__setattr__(altered, "result_schema_version", 1)
    assert (
        failure(apply_method_one_multipliers(altered, values)).code
        is ErrorCode.SCHEMA_VERSION_UNSUPPORTED
    )
    blocked = result()
    object.__setattr__(blocked.quality, "calculation_allowed", False)
    assert (
        failure(apply_method_one_multipliers(blocked, values)).code
        is ErrorCode.MODEL_NOT_APPLICABLE
    )
    assert (
        failure(apply_method_one_multipliers(base, cast(Any, list(values)))).code
        is ErrorCode.INVALID_MULTIPLIER
    )
    assert (
        failure(apply_method_one_multipliers(base, (cast(Any, object()),))).code
        is ErrorCode.INVALID_MULTIPLIER
    )
    assert (
        failure(apply_method_one_multipliers(base, values[:-1])).code
        is ErrorCode.INVALID_MULTIPLIER
    )
    incoherent = list(values)
    object.__setattr__(incoherent[0], "match_id", "other")
    assert (
        failure(apply_method_one_multipliers(base, tuple(incoherent))).code
        is ErrorCode.INVALID_MULTIPLIER
    )


def test_numeric_failures_are_typed_and_no_forbidden_runtime_imports_exist() -> None:
    assert (
        failure(implementation._apply_side(cast(Any, True), ())).code
        is ErrorCode.INVALID_NUMBER
    )
    base = result()
    object.__setattr__(base, "home_base_rate", float("inf"))
    assert (
        failure(apply_method_one_multipliers(base, resolved())).code
        is ErrorCode.INVALID_NUMBER
    )
    away_invalid = result()
    object.__setattr__(away_invalid, "away_base_rate", float("inf"))
    assert (
        failure(apply_method_one_multipliers(away_invalid, resolved())).code
        is ErrorCode.INVALID_NUMBER
    )
    huge = result()
    object.__setattr__(huge, "home_base_rate", 1.7e308)
    factors = tuple(candidate(category, 1.1) for category in MultiplierCategory)
    assert (
        failure(apply_method_one_multipliers(huge, resolved(*factors))).code
        is ErrorCode.INVALID_NUMBER
    )
    source = implementation.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read()
    for forbidden in (
        "PoissonRate",
        "run_pricing_engine",
        "lvfi_pricing.engine",
        "lvfi_pricing.markets",
        "lvfi_pricing.distributions",
    ):
        assert forbidden not in text

