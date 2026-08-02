"""Coverage for filtered immutable execution history and stored-record comparisons."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from lvfi_api.application.pricing_execution_comparison import (
    PricingExecutionComparisonService,
)
from lvfi_api.application.pricing_execution_persistence import (
    PricingExecutionPersistenceService,
)
from lvfi_api.domain.errors import (
    InvalidQueryError,
    PersistenceUnavailableError,
    ResourceNotFoundError,
)
from lvfi_api.domain.historical_queries import Page
from lvfi_api.domain.pricing_executions import (
    PricingExecution,
    PricingExecutionHistoryFilters,
    PricingExecutionStatus,
)
from lvfi_api.main import create_app
from lvfi_api.persistence.pricing_executions import SqlAlchemyPricingExecutionRepository

from .conftest import FakeDatabase
from .test_method_one_execution import TARGET, Provider, sample
from .test_pricing_execution_persistence import Database, Session, _row

NOW = datetime(2026, 8, 2, tzinfo=UTC)


def execution(
    execution_id: str,
    *,
    match_id: int = TARGET.id,
    created_at: datetime = NOW,
    status: PricingExecutionStatus = PricingExecutionStatus.COMPLETED,
    sample_fingerprint: str = "a" * 64,
    pricing_engine_version: str = "1.0.1",
    method_one_version: str = "1.0.0",
    schema_version: int = 1,
    canonical_input: dict[str, Any] | None = None,
    canonical_result: dict[str, Any] | None = None,
) -> PricingExecution:
    completed = status is PricingExecutionStatus.COMPLETED
    return PricingExecution(
        execution_id=execution_id,
        match_id=match_id,
        status=status,
        created_at=created_at,
        finalized_at=created_at,
        correlation_id="public-correlation",
        sample_fingerprint=sample_fingerprint,
        input_fingerprint="b" * 64 if completed else None,
        result_fingerprint="c" * 64 if completed else None,
        pricing_engine_version=pricing_engine_version,
        distribution_version="1.1.1",
        method_one_version=method_one_version,
        schema_version=schema_version,
        public_parameters={"requested_count": 10},
        canonical_input=canonical_input if completed else None,
        canonical_result=canonical_result if completed else None,
        failure_code=None if completed else "method_one_execution_failed",
    )


class HistoryRepository:
    def __init__(self, records: list[PricingExecution], matches: set[int]) -> None:
        self.records = records
        self.matches = matches
        self.calls = 0

    async def list_by_match(
        self,
        match_id: int,
        page: int,
        page_size: int,
        filters: PricingExecutionHistoryFilters | None = None,
    ) -> Page[PricingExecution] | None:
        self.calls += 1
        if match_id not in self.matches:
            return None
        values = [item for item in self.records if item.match_id == match_id]
        if filters is not None:
            values = [
                item
                for item in values
                if (filters.status is None or item.status is filters.status)
                and (
                    filters.created_from is None
                    or item.created_at >= filters.created_from
                )
                and (
                    filters.created_to is None or item.created_at <= filters.created_to
                )
                and (
                    filters.pricing_engine_version is None
                    or item.pricing_engine_version == filters.pricing_engine_version
                )
                and (
                    filters.method_one_version is None
                    or item.method_one_version == filters.method_one_version
                )
                and (
                    filters.sample_fingerprint is None
                    or item.sample_fingerprint == filters.sample_fingerprint
                )
                and (
                    filters.correlation_id is None
                    or item.correlation_id == filters.correlation_id
                )
            ]
            reverse = filters.order == "created_at_desc"
        else:
            reverse = True
        values.sort(
            key=lambda item: (item.created_at, item.execution_id), reverse=reverse
        )
        start = (page - 1) * page_size
        return Page(
            tuple(values[start : start + page_size]), page, page_size, len(values)
        )


class ComparisonRepository:
    def __init__(self, records: list[PricingExecution]) -> None:
        self.records = {item.execution_id: item for item in records}
        self.calls = 0

    async def get_many(
        self, execution_ids: tuple[str, ...]
    ) -> tuple[PricingExecution, ...]:
        self.calls += 1
        return tuple(
            self.records[execution_id]
            for execution_id in execution_ids
            if execution_id in self.records
        )


@pytest.mark.asyncio
async def test_comparison_is_stable_and_uses_only_one_stored_lookup() -> None:
    left = execution(
        "00000000-0000-0000-0000-000000000001",
        canonical_input={"rate": 1, "flags": [True, False]},
        canonical_result={"probability": 0.4, "lines": [1, 2]},
    )
    right = replace(
        left,
        execution_id="00000000-0000-0000-0000-000000000002",
        canonical_input={"rate": 3, "flags": [True, False]},
        canonical_result={"probability": 0.6, "lines": [1, 5]},
    )
    repository = ComparisonRepository([left, right])

    result = await PricingExecutionComparisonService(repository).compare(
        left.execution_id, right.execution_id
    )

    fields = {field.path: field for field in result.fields}
    assert repository.calls == 1
    assert result.canonical_compatible is True
    assert result.incompatibilities == ()
    assert [field.path for field in result.fields] == sorted(
        field.path for field in result.fields
    )
    assert fields["canonical_input.rate"].delta == 2
    assert fields["canonical_result.probability"].delta == pytest.approx(0.2)
    assert fields["canonical_result.lines[1]"].delta == 3
    assert fields["canonical_input.flags[0]"].delta is None
    assert fields["status"].equal is True


@pytest.mark.asyncio
async def test_comparison_reports_versions_status_and_schema_without_converting() -> (
    None
):
    left = execution(
        "00000000-0000-0000-0000-000000000003",
        canonical_input={"rate": 1},
        canonical_result={"probability": 0.4},
    )
    right = replace(
        left,
        execution_id="00000000-0000-0000-0000-000000000004",
        status=PricingExecutionStatus.TECHNICAL_FAILURE,
        sample_fingerprint="d" * 64,
        pricing_engine_version="2.0.0",
        method_one_version="2.0.0",
        schema_version=2,
        canonical_input=None,
        canonical_result=None,
        input_fingerprint=None,
        result_fingerprint=None,
        failure_code="method_one_execution_failed",
    )

    result = await PricingExecutionComparisonService(
        ComparisonRepository([left, right])
    ).compare(left.execution_id, right.execution_id)

    fields = {field.path: field for field in result.fields}
    assert result.canonical_compatible is False
    assert result.incompatibilities == (
        "schema_version",
        "pricing_engine_version",
        "method_one_version",
    )
    assert fields["status"].equal is False
    assert fields["sample_fingerprint"].equal is False
    assert fields["canonical_input"].delta is None
    assert fields["canonical_result"].left == {"probability": 0.4}


@pytest.mark.asyncio
async def test_comparison_rejects_absent_same_and_cross_match_executions() -> None:
    left = execution("00000000-0000-0000-0000-000000000005")
    other_match = replace(
        left, execution_id="00000000-0000-0000-0000-000000000006", match_id=999
    )
    service = PricingExecutionComparisonService(
        ComparisonRepository([left, other_match])
    )

    with pytest.raises(InvalidQueryError):
        await service.compare(left.execution_id, left.execution_id)
    with pytest.raises(ResourceNotFoundError):
        await service.compare(left.execution_id, "00000000-0000-0000-0000-000000000099")
    with pytest.raises(InvalidQueryError):
        await service.compare(left.execution_id, other_match.execution_id)


def test_history_filters_pagination_order_contracts_and_comparison_http(
    settings: Any,
) -> None:
    records = [
        execution("00000000-0000-0000-0000-000000000010", created_at=NOW),
        execution(
            "00000000-0000-0000-0000-000000000011",
            created_at=NOW + timedelta(seconds=1),
            sample_fingerprint="e" * 64,
            pricing_engine_version="2.0.0",
            method_one_version="2.0.0",
        ),
        execution(
            "00000000-0000-0000-0000-000000000012",
            created_at=NOW + timedelta(seconds=2),
            status=PricingExecutionStatus.TECHNICAL_FAILURE,
        ),
    ]
    history = HistoryRepository(records, {TARGET.id, 200})
    comparison = ComparisonRepository(records[:2])
    app = create_app(settings, FakeDatabase())
    app.state.pricing_execution_service = PricingExecutionPersistenceService(
        Provider(sample()),
        history,  # type: ignore[arg-type]
    )
    app.state.pricing_execution_comparison_service = PricingExecutionComparisonService(
        comparison
    )

    with TestClient(app) as client:
        empty = client.get("/matches/200/method-one/pricing-executions")
        individual_totals = [
            client.get(
                f"/matches/{TARGET.id}/method-one/pricing-executions", params=params
            )
            for params in (
                {"status": "completed"},
                {"created_from": (NOW + timedelta(seconds=1)).isoformat()},
                {"created_to": (NOW + timedelta(seconds=1)).isoformat()},
                {"pricing_engine_version": "2.0.0"},
                {"method_one_version": "2.0.0"},
                {"sample_fingerprint": "e" * 64},
                {"correlation_id": "public-correlation"},
            )
        ]
        filtered = client.get(
            f"/matches/{TARGET.id}/method-one/pricing-executions",
            params={
                "status": "completed",
                "created_from": NOW.isoformat(),
                "created_to": (NOW + timedelta(seconds=1)).isoformat(),
                "pricing_engine_version": "2.0.0",
                "method_one_version": "2.0.0",
                "sample_fingerprint": "e" * 64,
                "correlation_id": "public-correlation",
                "order": "created_at_asc",
                "page_size": 1,
            },
            headers={"X-Request-ID": "history-comparison"},
        )
        compared = client.get(
            "/pricing-execution-comparisons",
            params={
                "left_execution_id": records[0].execution_id,
                "right_execution_id": records[1].execution_id,
            },
        )
        missing = client.get(
            "/pricing-execution-comparisons",
            params={
                "left_execution_id": records[0].execution_id,
                "right_execution_id": "00000000-0000-0000-0000-000000000099",
            },
        )
        cross_match = client.get(
            "/pricing-execution-comparisons",
            params={
                "left_execution_id": records[0].execution_id,
                "right_execution_id": records[0].execution_id,
            },
        )
        paths = client.get("/openapi.json").json()["paths"]

    assert empty.status_code == 200 and empty.json()["items"] == []
    assert [response.json()["total"] for response in individual_totals] == [
        2,
        2,
        2,
        1,
        1,
        1,
        3,
    ]
    assert filtered.status_code == 200
    assert filtered.headers["X-Request-ID"] == "history-comparison"
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["execution_id"] == records[1].execution_id
    assert compared.status_code == 200
    assert comparison.calls == 2
    assert missing.status_code == 404 and "SQL" not in missing.text
    assert cross_match.status_code == 422 and "stack" not in cross_match.text
    assert "/pricing-execution-comparisons" in paths
    assert "source_line" not in compared.text and "idempotency_key" not in compared.text


@pytest.mark.asyncio
async def test_postgresql_repository_history_filters_and_pair_lookup() -> None:
    row = _row()
    pair = await SqlAlchemyPricingExecutionRepository(
        Database(Session([row]))
    ).get_many(("x",))  # type: ignore[arg-type]
    assert len(pair) == 1

    filters = PricingExecutionHistoryFilters(
        status=PricingExecutionStatus.COMPLETED,
        created_from=NOW,
        created_to=NOW,
        pricing_engine_version="1.1.1",
        method_one_version="1.0.0",
        sample_fingerprint="1" * 64,
        correlation_id="test",
        order="created_at_asc",
    )
    page = await SqlAlchemyPricingExecutionRepository(
        Database(Session([row], [TARGET.id, 1]))
    ).list_by_match(TARGET.id, 1, 10, filters)  # type: ignore[arg-type]
    assert page is not None and page.items[0].execution_id == row["execution_id"]


@pytest.mark.asyncio
async def test_comparison_repository_empty_failure_and_route_composition() -> None:
    assert (
        await SqlAlchemyPricingExecutionRepository(Database(Session())).get_many(())
        == ()
    )  # type: ignore[arg-type]
    with pytest.raises(PersistenceUnavailableError):
        await SqlAlchemyPricingExecutionRepository(
            Database(Session(fail=True))
        ).get_many(("x",))  # type: ignore[arg-type]

    from types import SimpleNamespace

    from lvfi_api.presentation.pricing_execution_routes import (
        get_pricing_execution_comparison_service,
    )

    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(database=Database(Session())))
    )
    service = await get_pricing_execution_comparison_service(request)  # type: ignore[arg-type]
    assert isinstance(service, PricingExecutionComparisonService)
    unavailable = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(database=object()))
    )
    with pytest.raises(PersistenceUnavailableError):
        await get_pricing_execution_comparison_service(unavailable)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_postgresql_repository_keeps_filter_branches_and_errors_covered() -> None:
    row = _row()
    ascending = PricingExecutionHistoryFilters(order="created_at_asc")
    page = await SqlAlchemyPricingExecutionRepository(
        Database(Session([row], [TARGET.id, 1]))
    ).list_by_match(TARGET.id, 1, 10, ascending)  # type: ignore[arg-type]
    assert page is not None and page.total == 1
