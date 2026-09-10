"""Versioned, auditable configuration contracts for the LVFI application."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from json import dumps
from typing import Literal

ConfigurationScope = Literal["global", "competition", "match"]

CATALOG_ID = "lvfi-mvp@1.0.0"
CATALOG_SCHEMA_VERSION = 1

# These are selectors already public in APP-013.  This catalog deliberately
# records no calculation coefficient, market price, or implicit default.
CATALOG_PARAMETERS: tuple[tuple[str, tuple[object, ...]], ...] = (
    ("sample_size", (5, 10, 15, 20)),
    ("venue", ("home", "away", "overall")),
    ("competition_scope", ("target_competition", "all_eligible")),
    ("season_scope", ("current", "current_and_previous")),
    (
        "metric",
        (
            "goals_scored",
            "goals_conceded",
            "result_win",
            "corners",
            "shots_on_target",
            "shots",
            "cards",
            "fouls",
        ),
    ),
    ("probability_band", ("lt_0_4", "from_0_4_to_0_6", "gt_0_6")),
)
HANDICAP_LINE_QUARTERS = tuple(range(-12, 13))
TOTAL_LINE_QUARTERS = tuple(range(1, 25))


def canonical_json(value: object) -> str:
    """Return the single stable representation used by all configuration hashes."""
    return dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def configuration_hash(value: object) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def catalog_payload() -> dict[str, object]:
    return {
        "catalog_id": CATALOG_ID,
        "schema_version": CATALOG_SCHEMA_VERSION,
        "statistical_parameters": [
            {"code": code, "allowed_values": list(values)}
            for code, values in CATALOG_PARAMETERS
        ],
        "statistical_lines": {
            "handicap_line_quarters": list(HANDICAP_LINE_QUARTERS),
            "total_line_quarters": list(TOTAL_LINE_QUARTERS),
        },
        "probability_bands": [
            {"code": "lt_0_4", "upper_exclusive": 0.4},
            {"code": "from_0_4_to_0_6", "lower_inclusive": 0.4, "upper_inclusive": 0.6},
            {"code": "gt_0_6", "lower_exclusive": 0.6},
        ],
    }


def allowed_parameter_value(parameter_code: str, value: object) -> bool:
    return any(
        code == parameter_code and value in values
        for code, values in CATALOG_PARAMETERS
    )


@dataclass(frozen=True, slots=True)
class ConfigurationCatalog:
    catalog_id: str
    schema_version: int
    payload: dict[str, object]
    content_hash: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ConfigurationRevisionDraft:
    catalog_id: str
    scope: ConfigurationScope
    parameter_code: str
    value: object
    competition_id: int | None
    match_id: int | None
    actor: str
    reason: str


@dataclass(frozen=True, slots=True)
class ConfigurationRevision:
    revision_id: int
    catalog_id: str
    catalog_hash: str
    scope: ConfigurationScope
    parameter_code: str
    value: object
    competition_id: int | None
    match_id: int | None
    actor: str
    reason: str
    replaces_revision_id: int | None
    revision_hash: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class EffectiveConfiguration:
    match_id: int
    competition_id: int
    catalog_id: str
    catalog_hash: str
    values: dict[str, object]
    selected_revisions: tuple[ConfigurationRevision, ...]
    discarded_revisions: tuple[ConfigurationRevision, ...]
    effective_hash: str


def valid_revision_draft(draft: ConfigurationRevisionDraft) -> bool:
    if (
        draft.catalog_id != CATALOG_ID
        or not allowed_parameter_value(draft.parameter_code, draft.value)
        or not draft.actor.strip()
        or not draft.reason.strip()
    ):
        return False
    if draft.scope == "global":
        return draft.competition_id is None and draft.match_id is None
    if draft.scope == "competition":
        return (
            draft.competition_id is not None
            and draft.competition_id > 0
            and draft.match_id is None
        )
    return (
        draft.scope == "match"
        and draft.match_id is not None
        and draft.match_id > 0
        and draft.competition_id is None
    )
