"""Create append-only PDF artifact metadata for approved snapshots.

Revision ID: 20260911_11
Revises: 20260911_10
"""

from collections.abc import Sequence

from alembic import op
from lvfi_api.persistence.historical_models import analysis_pdf_artifacts

revision: str = "20260911_11"
down_revision: str | None = "20260911_10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Install immutable report metadata without changing snapshots."""
    bind = op.get_bind()
    analysis_pdf_artifacts.create(bind, checkfirst=False)
    op.execute(
        "CREATE FUNCTION prohibit_analysis_pdf_artifact_mutation() RETURNS trigger AS $$ "
        "BEGIN RAISE EXCEPTION 'analysis PDF artifacts are append-only'; END; $$ LANGUAGE plpgsql"
    )
    op.execute(
        "CREATE TRIGGER analysis_pdf_artifacts_append_only BEFORE UPDATE OR DELETE ON "
        "analysis_pdf_artifacts FOR EACH ROW EXECUTE FUNCTION prohibit_analysis_pdf_artifact_mutation()"
    )


def downgrade() -> None:
    """Remove only the APP-018 additive metadata and its guard."""
    op.execute("DROP TRIGGER analysis_pdf_artifacts_append_only ON analysis_pdf_artifacts")
    op.execute("DROP FUNCTION prohibit_analysis_pdf_artifact_mutation()")
    analysis_pdf_artifacts.drop(op.get_bind(), checkfirst=False)
