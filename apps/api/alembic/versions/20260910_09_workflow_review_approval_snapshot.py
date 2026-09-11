# ruff: noqa: E501
"""Create immutable APP-015 analysis workflow, event ledger and snapshots.

Revision ID: 20260910_09
Revises: 20260910_08
"""

from collections.abc import Sequence

from alembic import op
from lvfi_api.persistence.historical_models import (
    analysis_workflow_analyses,
    analysis_workflow_events,
    analysis_workflow_snapshots,
)

revision: str = "20260910_09"
down_revision: str | None = "20260910_08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Install an append-only state machine without changing prior ledgers."""
    bind = op.get_bind()
    analysis_workflow_analyses.create(bind, checkfirst=False)
    analysis_workflow_events.create(bind, checkfirst=False)
    analysis_workflow_snapshots.create(bind, checkfirst=False)
    op.execute(
        "CREATE UNIQUE INDEX ux_analysis_workflow_calculated ON "
        "analysis_workflow_events (analysis_id) WHERE event_type = 'calculated'"
    )
    op.execute(
        "CREATE UNIQUE INDEX ux_analysis_workflow_approved ON "
        "analysis_workflow_events (analysis_id) WHERE event_type = 'approved'"
    )
    op.execute(
        "CREATE FUNCTION validate_analysis_workflow_event() RETURNS trigger AS $$ "
        "DECLARE analysis_match bigint; execution_match bigint; execution_status text; "
        "BEGIN "
        "SELECT match_id INTO analysis_match FROM analysis_workflow_analyses "
        "WHERE analysis_id = NEW.analysis_id; "
        "IF NEW.event_type = 'calculated' THEN "
        "SELECT match_id, status INTO execution_match, execution_status FROM pricing_executions "
        "WHERE execution_id = NEW.execution_id; "
        "IF execution_match IS NULL OR execution_match <> analysis_match OR execution_status <> 'completed' THEN "
        "RAISE EXCEPTION 'calculation requires a completed execution for the analysis match'; END IF; "
        "ELSIF NEW.event_type = 'reviewed' THEN "
        "IF NOT EXISTS (SELECT 1 FROM analysis_workflow_events WHERE analysis_id = NEW.analysis_id "
        "AND event_type = 'calculated') OR EXISTS (SELECT 1 FROM analysis_workflow_events "
        "WHERE analysis_id = NEW.analysis_id AND event_type = 'approved') THEN "
        "RAISE EXCEPTION 'review requires calculated analysis before approval'; END IF; "
        "ELSIF NEW.event_type = 'approved' THEN "
        "IF NOT EXISTS (SELECT 1 FROM analysis_workflow_events WHERE analysis_id = NEW.analysis_id "
        "AND event_type = 'calculated') OR NOT EXISTS (SELECT 1 FROM analysis_workflow_events "
        "WHERE analysis_id = NEW.analysis_id AND event_type = 'reviewed') OR EXISTS "
        "(SELECT 1 FROM analysis_workflow_events WHERE analysis_id = NEW.analysis_id "
        "AND event_type = 'approved') THEN RAISE EXCEPTION 'approval requires one review'; END IF; "
        "END IF; RETURN NEW; END; $$ LANGUAGE plpgsql"
    )
    op.execute(
        "CREATE TRIGGER analysis_workflow_event_state_machine BEFORE INSERT ON "
        "analysis_workflow_events FOR EACH ROW EXECUTE FUNCTION validate_analysis_workflow_event()"
    )
    op.execute(
        "CREATE FUNCTION validate_analysis_workflow_snapshot() RETURNS trigger AS $$ "
        "BEGIN IF NOT EXISTS (SELECT 1 FROM analysis_workflow_events WHERE "
        "analysis_id = NEW.analysis_id AND event_type = 'approved') THEN "
        "RAISE EXCEPTION 'snapshot requires approved analysis'; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql"
    )
    op.execute(
        "CREATE TRIGGER analysis_workflow_snapshot_approved BEFORE INSERT ON "
        "analysis_workflow_snapshots FOR EACH ROW EXECUTE FUNCTION validate_analysis_workflow_snapshot()"
    )
    op.execute(
        "CREATE FUNCTION prohibit_analysis_workflow_mutation() RETURNS trigger AS $$ "
        "BEGIN RAISE EXCEPTION 'analysis workflow is append-only'; END; $$ LANGUAGE plpgsql"
    )
    for table, trigger in (
        ("analysis_workflow_analyses", "analysis_workflow_analyses_append_only"),
        ("analysis_workflow_events", "analysis_workflow_events_append_only"),
        ("analysis_workflow_snapshots", "analysis_workflow_snapshots_append_only"),
    ):
        op.execute(
            f"CREATE TRIGGER {trigger} BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION prohibit_analysis_workflow_mutation()"
        )


def downgrade() -> None:
    """Remove only the additive APP-015 objects in dependency-safe order."""
    for table, trigger in (
        ("analysis_workflow_snapshots", "analysis_workflow_snapshots_append_only"),
        ("analysis_workflow_events", "analysis_workflow_events_append_only"),
        ("analysis_workflow_analyses", "analysis_workflow_analyses_append_only"),
    ):
        op.execute(f"DROP TRIGGER {trigger} ON {table}")
    op.execute("DROP FUNCTION prohibit_analysis_workflow_mutation()")
    op.execute(
        "DROP TRIGGER analysis_workflow_snapshot_approved ON analysis_workflow_snapshots"
    )
    op.execute("DROP FUNCTION validate_analysis_workflow_snapshot()")
    op.execute(
        "DROP TRIGGER analysis_workflow_event_state_machine ON analysis_workflow_events"
    )
    op.execute("DROP FUNCTION validate_analysis_workflow_event()")
    op.execute("DROP INDEX ux_analysis_workflow_approved")
    op.execute("DROP INDEX ux_analysis_workflow_calculated")
    analysis_workflow_snapshots.drop(op.get_bind(), checkfirst=False)
    analysis_workflow_events.drop(op.get_bind(), checkfirst=False)
    analysis_workflow_analyses.drop(op.get_bind(), checkfirst=False)
