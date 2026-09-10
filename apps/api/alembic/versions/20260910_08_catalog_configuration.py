"""Add the immutable APP-014 catalog and configuration revision ledger.

Revision ID: 20260910_08
Revises: 20260906_07
"""

from collections.abc import Sequence

from sqlalchemy import text

from alembic import op
from lvfi_api.domain.configuration import (
    CATALOG_ID,
    CATALOG_SCHEMA_VERSION,
    canonical_json,
    catalog_payload,
    configuration_hash,
)
from lvfi_api.persistence.historical_models import (
    configuration_catalogs,
    configuration_revisions,
)

revision: str = "20260910_08"
down_revision: str | None = "20260906_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Install the authorized catalog before accepting append-only revisions."""
    bind = op.get_bind()
    configuration_catalogs.create(bind, checkfirst=False)
    configuration_revisions.create(bind, checkfirst=False)
    payload = catalog_payload()
    bind.execute(
        text(
            "INSERT INTO configuration_catalogs "
            "(catalog_id, schema_version, payload, content_hash) VALUES "
            "(:catalog_id, :schema_version, CAST(:payload AS json), :content_hash)"
        ),
        {
            "catalog_id": CATALOG_ID,
            "schema_version": CATALOG_SCHEMA_VERSION,
            "payload": canonical_json(payload),
            "content_hash": configuration_hash(payload),
        },
    )
    op.execute(
        "CREATE FUNCTION prohibit_configuration_mutation() RETURNS trigger "
        "AS $$ BEGIN RAISE EXCEPTION 'configuration ledger is append-only'; "
        "END; $$ LANGUAGE plpgsql;"
    )
    op.execute(
        "CREATE TRIGGER configuration_catalogs_append_only BEFORE UPDATE OR DELETE "
        "ON configuration_catalogs FOR EACH ROW EXECUTE FUNCTION "
        "prohibit_configuration_mutation();"
    )
    op.execute(
        "CREATE TRIGGER configuration_revisions_append_only BEFORE UPDATE OR DELETE "
        "ON configuration_revisions FOR EACH ROW EXECUTE FUNCTION "
        "prohibit_configuration_mutation();"
    )


def downgrade() -> None:
    """Remove only the additive APP-014 tables and their local trigger."""
    op.execute(
        "DROP TRIGGER configuration_revisions_append_only ON configuration_revisions"
    )
    op.execute(
        "DROP TRIGGER configuration_catalogs_append_only ON configuration_catalogs"
    )
    op.execute("DROP FUNCTION prohibit_configuration_mutation()")
    configuration_revisions.drop(op.get_bind(), checkfirst=False)
    configuration_catalogs.drop(op.get_bind(), checkfirst=False)
