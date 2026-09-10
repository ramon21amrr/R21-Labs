"""HTTP contract tests for the additive APP-014 configuration endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient

from lvfi_api.domain.configuration import (
    CATALOG_ID,
    ConfigurationCatalog,
    ConfigurationRevision,
    EffectiveConfiguration,
    catalog_payload,
    configuration_hash,
)
from lvfi_api.main import create_app


class _Service:
    def __init__(self) -> None:
        self.revision = ConfigurationRevision(
            revision_id=2,
            catalog_id=CATALOG_ID,
            catalog_hash=configuration_hash(catalog_payload()),
            scope="match",
            parameter_code="sample_size",
            value=15,
            competition_id=None,
            match_id=7,
            actor="local-admin",
            reason="verified local setting",
            replaces_revision_id=1,
            revision_hash="a" * 64,
            created_at=datetime(2026, 9, 10, tzinfo=UTC),
        )

    async def get_catalog(self) -> ConfigurationCatalog:
        payload = catalog_payload()
        return ConfigurationCatalog(
            catalog_id=CATALOG_ID,
            schema_version=1,
            payload=payload,
            content_hash=configuration_hash(payload),
            created_at=datetime(2026, 9, 10, tzinfo=UTC),
        )

    async def create_revision(self, draft: Any) -> ConfigurationRevision:
        assert draft.scope == "match" and draft.value == 15
        return self.revision

    async def get_history(self, *args: Any) -> tuple[ConfigurationRevision, ...]:
        return (self.revision,)

    async def effective(self, match_id: int) -> EffectiveConfiguration:
        assert match_id == 7
        return EffectiveConfiguration(
            match_id=7,
            competition_id=3,
            catalog_id=CATALOG_ID,
            catalog_hash="b" * 64,
            values={"sample_size": 15},
            selected_revisions=(self.revision,),
            discarded_revisions=(),
            effective_hash="c" * 64,
        )


def test_configuration_routes_expose_catalog_revision_and_effective_value(
    settings: Any, database: Any
) -> None:
    app = create_app(settings, database)
    app.state.configuration_service = _Service()
    with TestClient(app) as client:
        catalog = client.get("/configuration-catalogs/lvfi-mvp/1.0.0")
        created = client.post(
            "/administration/configuration-revisions",
            json={
                "catalog_id": CATALOG_ID,
                "scope": "match",
                "parameter_code": "sample_size",
                "value": 15,
                "match_id": 7,
                "reason": "verified local setting",
            },
        )
        history = client.get("/administration/configuration-revisions")
        effective = client.get("/matches/7/configuration/effective")

    assert catalog.status_code == 200
    assert catalog.json()["payload"]["statistical_lines"]["total_line_quarters"][0] == 1
    assert created.status_code == 201 and created.json()["replaces_revision_id"] == 1
    assert history.json()["revisions"][0]["scope"] == "match"
    assert effective.json()["values"] == {"sample_size": 15}
    assert effective.json()["effective_hash"] == "c" * 64


def test_configuration_routes_reject_unknown_and_invalid_request_fields(
    settings: Any, database: Any
) -> None:
    app = create_app(settings, database)
    app.state.configuration_service = _Service()
    with TestClient(app) as client:
        unknown_query = client.get(
            "/administration/configuration-revisions?unexpected=value"
        )
        invalid_payload = client.post(
            "/administration/configuration-revisions",
            json={
                "catalog_id": CATALOG_ID,
                "scope": "global",
                "parameter_code": "sample_size",
                "value": True,
                "reason": "must not coerce boolean",
            },
        )

    assert unknown_query.status_code == 422
    assert invalid_payload.status_code == 422
