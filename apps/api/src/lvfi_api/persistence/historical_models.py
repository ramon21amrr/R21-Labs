# ruff: noqa: E501
"""Relational schema for controlled historical-football imports."""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)

from lvfi_api.persistence.metadata import metadata

import_batches = Table(
    "import_batches",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("source_filename", String(255), nullable=False),
    Column("source_sha256", String(64), nullable=False),
    Column("sheet_name", String(128), nullable=False),
    Column("status", String(24), nullable=False),
    Column("total_records", Integer, nullable=False, server_default="0"),
    Column("accepted_records", Integer, nullable=False, server_default="0"),
    Column("rejected_records", Integer, nullable=False, server_default="0"),
    Column("warning_records", Integer, nullable=False, server_default="0"),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    Column("completed_at", DateTime(timezone=True)),
    UniqueConstraint("source_sha256", "sheet_name", name="source_hash_sheet"),
    CheckConstraint(
        "status IN ('running', 'completed', 'completed_with_rejections', 'failed')",
        name="import_batch_status",
    ),
)

source_records = Table(
    "source_records",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column(
        "batch_id",
        BigInteger,
        ForeignKey("import_batches.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("source_line", Integer, nullable=False),
    Column("row_sha256", String(64), nullable=False),
    Column("raw_values", JSON, nullable=False),
    Column("status", String(24), nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    UniqueConstraint("batch_id", "source_line", name="source_record_line"),
    CheckConstraint(
        "status IN ('accepted', 'rejected', 'warning', 'conflict')",
        name="source_record_status",
    ),
)

import_issues = Table(
    "import_issues",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column(
        "source_record_id",
        BigInteger,
        ForeignKey("source_records.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("severity", String(16), nullable=False),
    Column("code", String(80), nullable=False),
    Column("field_name", String(80)),
    Column("message", Text, nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    CheckConstraint("severity IN ('error', 'warning')", name="import_issue_severity"),
)

competitions = Table(
    "competitions",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("display_name", String(255), nullable=False),
    Column("normalized_name", String(255), nullable=False, unique=True),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)

seasons = Table(
    "seasons",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column(
        "competition_id",
        BigInteger,
        ForeignKey("competitions.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("label", String(32), nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    UniqueConstraint("competition_id", "label", name="season_competition_label"),
)

teams = Table(
    "teams",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("display_name", String(255), nullable=False),
    Column("normalized_name", String(255), nullable=False, unique=True),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
)

matches = Table(
    "matches",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column(
        "season_id",
        BigInteger,
        ForeignKey("seasons.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("played_on", Date, nullable=False),
    Column(
        "home_team_id",
        BigInteger,
        ForeignKey("teams.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "away_team_id",
        BigInteger,
        ForeignKey("teams.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "source_record_id",
        BigInteger,
        ForeignKey("source_records.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    ),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    UniqueConstraint(
        "season_id",
        "played_on",
        "home_team_id",
        "away_team_id",
        name="match_natural_key",
    ),
    CheckConstraint("home_team_id <> away_team_id", name="match_distinct_teams"),
)

match_statistics = Table(
    "match_statistics",
    metadata,
    Column(
        "match_id",
        BigInteger,
        ForeignKey("matches.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("home_goals_first_half", Integer, nullable=False),
    Column("away_goals_first_half", Integer, nullable=False),
    Column("home_goals_full_match", Integer, nullable=False),
    Column("away_goals_full_match", Integer, nullable=False),
    Column("home_shots_first_half", Integer, nullable=False),
    Column("away_shots_first_half", Integer, nullable=False),
    Column("home_shots_full_match", Integer, nullable=False),
    Column("away_shots_full_match", Integer, nullable=False),
    Column("home_shots_on_target_first_half", Integer, nullable=False),
    Column("away_shots_on_target_first_half", Integer, nullable=False),
    Column("home_shots_on_target_full_match", Integer, nullable=False),
    Column("away_shots_on_target_full_match", Integer, nullable=False),
    Column("home_corners_first_half", Integer, nullable=False),
    Column("away_corners_first_half", Integer, nullable=False),
    Column("home_corners_full_match", Integer, nullable=False),
    Column("away_corners_full_match", Integer, nullable=False),
    Column("home_fouls_full_match", Integer, nullable=False),
    Column("away_fouls_full_match", Integer, nullable=False),
    Column("home_cards_full_match", Integer, nullable=False),
    Column("away_cards_full_match", Integer, nullable=False),
    CheckConstraint(
        "home_goals_first_half <= home_goals_full_match", name="stats_home_goals_half"
    ),
    CheckConstraint(
        "away_goals_first_half <= away_goals_full_match", name="stats_away_goals_half"
    ),
    CheckConstraint(
        "home_shots_first_half <= home_shots_full_match", name="stats_home_shots_half"
    ),
    CheckConstraint(
        "away_shots_first_half <= away_shots_full_match", name="stats_away_shots_half"
    ),
    CheckConstraint(
        "home_shots_on_target_first_half <= home_shots_on_target_full_match",
        name="stats_home_targets_half",
    ),
    CheckConstraint(
        "away_shots_on_target_first_half <= away_shots_on_target_full_match",
        name="stats_away_targets_half",
    ),
    CheckConstraint(
        "home_corners_first_half <= home_corners_full_match",
        name="stats_home_corners_half",
    ),
    CheckConstraint(
        "away_corners_first_half <= away_corners_full_match",
        name="stats_away_corners_half",
    ),
    CheckConstraint(
        "home_shots_on_target_full_match <= home_shots_full_match",
        name="stats_home_targets_shots",
    ),
    CheckConstraint(
        "away_shots_on_target_full_match <= away_shots_full_match",
        name="stats_away_targets_shots",
    ),
    *[
        CheckConstraint(f"{column} >= 0", name=f"stats_{column}_nonnegative")
        for column in (
            "home_goals_first_half",
            "away_goals_first_half",
            "home_goals_full_match",
            "away_goals_full_match",
            "home_shots_first_half",
            "away_shots_first_half",
            "home_shots_full_match",
            "away_shots_full_match",
            "home_shots_on_target_first_half",
            "away_shots_on_target_first_half",
            "home_shots_on_target_full_match",
            "away_shots_on_target_full_match",
            "home_corners_first_half",
            "away_corners_first_half",
            "home_corners_full_match",
            "away_corners_full_match",
            "home_fouls_full_match",
            "away_fouls_full_match",
            "home_cards_full_match",
            "away_cards_full_match",
        )
    ],
)

Index(
    "ix_source_records_batch_status", source_records.c.batch_id, source_records.c.status
)
Index(
    "ix_import_issues_source_severity",
    import_issues.c.source_record_id,
    import_issues.c.severity,
)
Index("ix_matches_played_on", matches.c.played_on)
