"""Add manual-match support and append-only statistic revisions.

Revision ID: 20260906_07
Revises: 20260825_06
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from lvfi_api.persistence.historical_models import statistic_revisions

revision: str = "20260906_07"
down_revision: str | None = "20260825_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Allow future manual matches and preserve each subsequent correction."""

    op.alter_column(
        "matches",
        "source_record_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
    statistic_revisions.create(op.get_bind(), checkfirst=False)
    op.execute(
        "CREATE FUNCTION prohibit_statistic_revision_mutation() RETURNS trigger "
        "AS $$ BEGIN RAISE EXCEPTION 'statistic_revisions is append-only'; "
        "END; $$ LANGUAGE plpgsql;"
    )
    op.execute(
        "CREATE TRIGGER statistic_revisions_append_only BEFORE UPDATE OR DELETE "
        "ON statistic_revisions FOR EACH ROW EXECUTE FUNCTION "
        "prohibit_statistic_revision_mutation();"
    )


def downgrade() -> None:
    """Remove only APP-012 schema, refusing to discard manual matches."""

    op.execute("DROP TRIGGER statistic_revisions_append_only ON statistic_revisions")
    op.execute("DROP FUNCTION prohibit_statistic_revision_mutation()")
    statistic_revisions.drop(op.get_bind(), checkfirst=False)
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM matches WHERE source_record_id IS NULL) "
        "THEN RAISE EXCEPTION "
        "'cannot restore source_record_id requirement while manual matches exist'; "
        "END IF; END $$;"
    )
    op.alter_column(
        "matches",
        "source_record_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
