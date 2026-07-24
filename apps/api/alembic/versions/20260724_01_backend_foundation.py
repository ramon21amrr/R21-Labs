"""Initialize the backend migration lineage without premature domain tables.

Revision ID: 20260724_01
Revises:
Create Date: 2026-07-24 00:00:00

Alembic creates and owns ``alembic_version`` as the technical migration-control
table. Football entities are intentionally absent until their approved task.
"""

from collections.abc import Sequence

revision: str = "20260724_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Establish the initial revision marker through Alembic's control table."""


def downgrade() -> None:
    """Return to the unversioned empty schema without domain data."""
