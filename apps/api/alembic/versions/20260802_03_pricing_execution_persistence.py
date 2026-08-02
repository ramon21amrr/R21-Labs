"""Create append-only auditable Method One pricing executions.

Revision ID: 20260802_03
Revises: 20260727_02
Create Date: 2026-08-02 00:00:00
"""

from collections.abc import Sequence

from alembic import op
from lvfi_api.persistence.historical_models import pricing_executions

revision: str = "20260802_03"
down_revision: str | None = "20260727_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the execution ledger and enforce PostgreSQL append-only writes."""
    bind = op.get_bind()
    pricing_executions.create(bind, checkfirst=False)
    op.execute(
        """
        CREATE FUNCTION prohibit_pricing_execution_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'pricing_executions is append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER pricing_executions_append_only
        BEFORE UPDATE OR DELETE ON pricing_executions
        FOR EACH ROW EXECUTE FUNCTION prohibit_pricing_execution_mutation();
        """
    )


def downgrade() -> None:
    """Remove only this task's trigger, function, and table in reverse order."""
    op.execute("DROP TRIGGER pricing_executions_append_only ON pricing_executions")
    op.execute("DROP FUNCTION prohibit_pricing_execution_mutation()")
    pricing_executions.drop(op.get_bind(), checkfirst=False)
