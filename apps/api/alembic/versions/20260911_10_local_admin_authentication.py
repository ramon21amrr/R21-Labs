"""Create APP-017 local-admin credential, session and audit storage.

Revision ID: 20260911_10
Revises: 20260910_09
"""

from collections.abc import Sequence

from alembic import op
from lvfi_api.persistence.historical_models import (
    local_admin_auth_events,
    local_admin_credentials,
    local_admin_sessions,
)

revision: str = "20260911_10"
down_revision: str | None = "20260910_09"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Install additive identity tables and an append-only auth audit ledger."""
    bind = op.get_bind()
    local_admin_credentials.create(bind, checkfirst=False)
    local_admin_sessions.create(bind, checkfirst=False)
    local_admin_auth_events.create(bind, checkfirst=False)
    op.execute(
        "CREATE FUNCTION prohibit_local_admin_auth_event_mutation() "
        "RETURNS trigger AS $$ BEGIN RAISE EXCEPTION "
        "'local admin auth audit is append-only'; END; $$ LANGUAGE plpgsql"
    )
    op.execute(
        "CREATE TRIGGER local_admin_auth_events_append_only BEFORE UPDATE OR "
        "DELETE ON local_admin_auth_events FOR EACH ROW EXECUTE FUNCTION "
        "prohibit_local_admin_auth_event_mutation()"
    )


def downgrade() -> None:
    """Remove only APP-017 identity storage in dependency-safe order."""
    op.execute(
        "DROP TRIGGER local_admin_auth_events_append_only ON local_admin_auth_events"
    )
    op.execute("DROP FUNCTION prohibit_local_admin_auth_event_mutation()")
    local_admin_auth_events.drop(op.get_bind(), checkfirst=False)
    local_admin_sessions.drop(op.get_bind(), checkfirst=False)
    local_admin_credentials.drop(op.get_bind(), checkfirst=False)
