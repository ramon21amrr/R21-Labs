"""Create the append-only versioned market-pricing ledger.

Revision ID: 20260825_05
Revises: 20260802_04
"""

from collections.abc import Sequence

from alembic import op
from lvfi_api.persistence.historical_models import market_pricings

revision: str = "20260825_05"
down_revision: str | None = "20260802_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create a separate append-only ledger for Engine-produced market snapshots."""
    market_pricings.create(op.get_bind(), checkfirst=False)
    op.execute(
        "CREATE FUNCTION prohibit_market_pricing_mutation() RETURNS trigger "
        "AS $$ BEGIN RAISE EXCEPTION 'market_pricings is append-only'; END; $$ LANGUAGE plpgsql;"
    )
    op.execute(
        "CREATE TRIGGER market_pricings_append_only BEFORE UPDATE OR DELETE "
        "ON market_pricings FOR EACH ROW EXECUTE FUNCTION prohibit_market_pricing_mutation();"
    )


def downgrade() -> None:
    """Remove only this task's database objects in reverse dependency order."""
    op.execute("DROP TRIGGER market_pricings_append_only ON market_pricings")
    op.execute("DROP FUNCTION prohibit_market_pricing_mutation()")
    market_pricings.drop(op.get_bind(), checkfirst=False)
