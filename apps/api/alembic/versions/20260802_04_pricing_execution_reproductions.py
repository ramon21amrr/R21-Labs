"""Create append-only controlled pricing-execution reproductions.

Revision ID: 20260802_04
Revises: 20260802_03
"""

from collections.abc import Sequence

from alembic import op

from lvfi_api.persistence.historical_models import pricing_execution_reproductions

revision: str = "20260802_04"
down_revision: str | None = "20260802_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the separate immutable reproduction ledger."""
    pricing_execution_reproductions.create(op.get_bind(), checkfirst=False)
    op.execute(
        "CREATE FUNCTION prohibit_pricing_reproduction_mutation() RETURNS trigger "
        "AS $$ BEGIN RAISE EXCEPTION 'pricing_execution_reproductions is append-only'; "
        "END; $$ LANGUAGE plpgsql;"
    )
    op.execute(
        "CREATE TRIGGER pricing_reproductions_append_only BEFORE UPDATE OR DELETE "
        "ON pricing_execution_reproductions FOR EACH ROW EXECUTE FUNCTION "
        "prohibit_pricing_reproduction_mutation();"
    )


def downgrade() -> None:
    """Remove only APP-009 objects in reverse order."""
    op.execute(
        "DROP TRIGGER pricing_reproductions_append_only ON pricing_execution_reproductions"
    )
    op.execute("DROP FUNCTION prohibit_pricing_reproduction_mutation()")
    pricing_execution_reproductions.drop(op.get_bind(), checkfirst=False)
