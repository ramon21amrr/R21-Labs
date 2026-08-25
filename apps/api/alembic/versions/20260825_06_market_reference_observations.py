"""Create the append-only manual market-reference observation ledger.

Revision ID: 20260825_06
Revises: 20260825_05
"""

from collections.abc import Sequence

from alembic import op
from lvfi_api.persistence.historical_models import market_reference_observations

revision: str = "20260825_06"
down_revision: str | None = "20260825_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    market_reference_observations.create(op.get_bind(), checkfirst=False)
    op.execute(
        "CREATE FUNCTION prohibit_market_reference_mutation() RETURNS trigger "
        "AS $$ BEGIN RAISE EXCEPTION 'market_reference_observations is append-only'; "
        "END; $$ LANGUAGE plpgsql;"
    )
    op.execute(
        "CREATE TRIGGER market_reference_observations_append_only BEFORE UPDATE OR "
        "DELETE ON market_reference_observations FOR EACH ROW EXECUTE FUNCTION "
        "prohibit_market_reference_mutation();"
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER market_reference_observations_append_only "
        "ON market_reference_observations"
    )
    op.execute("DROP FUNCTION prohibit_market_reference_mutation()")
    market_reference_observations.drop(op.get_bind(), checkfirst=False)
