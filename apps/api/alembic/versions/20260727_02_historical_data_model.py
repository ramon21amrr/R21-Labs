"""Create controlled historical-import and canonical-football tables.

Revision ID: 20260727_02
Revises: 20260724_01
Create Date: 2026-07-27 00:00:00
"""

from collections.abc import Sequence

from alembic import op
from lvfi_api.persistence.historical_models import (
    competitions,
    import_batches,
    import_issues,
    match_statistics,
    matches,
    seasons,
    source_records,
    teams,
)

revision: str = "20260727_02"
down_revision: str | None = "20260724_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    import_batches,
    source_records,
    import_issues,
    competitions,
    seasons,
    teams,
    matches,
    match_statistics,
)


def upgrade() -> None:
    """Create the reversible APP-003 schema with PostgreSQL constraints and indexes."""

    bind = op.get_bind()
    for table in TABLES:
        table.create(bind, checkfirst=False)


def downgrade() -> None:
    """Drop only APP-003 domain tables in dependency-safe reverse order."""

    bind = op.get_bind()
    for table in reversed(TABLES):
        table.drop(bind, checkfirst=False)
