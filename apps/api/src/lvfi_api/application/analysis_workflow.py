"""Application boundary for immutable APP-015 workflow transitions."""

from __future__ import annotations

from typing import Protocol
from uuid import uuid4

from lvfi_api.domain.analysis_workflow import Analysis, AnalysisSnapshot
from lvfi_api.domain.errors import InvalidQueryError, ResourceNotFoundError


class AnalysisWorkflowRepository(Protocol):
    async def create_draft(
        self, analysis_id: str, match_id: int
    ) -> Analysis | None: ...

    async def calculate(
        self, analysis_id: str, execution_id: str
    ) -> Analysis | None: ...

    async def review(
        self, analysis_id: str, actor: str, reason: str
    ) -> Analysis | None: ...

    async def approve(
        self, analysis_id: str, snapshot_id: str, actor: str, reason: str
    ) -> tuple[Analysis, AnalysisSnapshot] | None: ...

    async def get(self, analysis_id: str) -> Analysis | None: ...

    async def list_by_match(self, match_id: int) -> tuple[Analysis, ...] | None: ...

    async def get_snapshot_by_analysis(
        self, analysis_id: str
    ) -> AnalysisSnapshot | None: ...

    async def get_snapshot(self, snapshot_id: str) -> AnalysisSnapshot | None: ...


class AnalysisWorkflowService:
    def __init__(self, repository: AnalysisWorkflowRepository) -> None:
        self._repository = repository

    async def create_draft(self, match_id: int) -> Analysis:
        value = await self._repository.create_draft(str(uuid4()), match_id)
        if value is None:
            raise ResourceNotFoundError("match")
        return value

    async def calculate(self, analysis_id: str, execution_id: str) -> Analysis:
        value = await self._repository.calculate(analysis_id, execution_id)
        if value is None:
            raise ResourceNotFoundError("analysis or pricing execution")
        return value

    async def review(self, analysis_id: str, actor: str, reason: str) -> Analysis:
        if not actor.strip() or not reason.strip():
            raise InvalidQueryError("review requires actor and reason")
        value = await self._repository.review(
            analysis_id, actor.strip(), reason.strip()
        )
        if value is None:
            raise ResourceNotFoundError("analysis")
        return value

    async def approve(
        self, analysis_id: str, actor: str, reason: str
    ) -> tuple[Analysis, AnalysisSnapshot]:
        if not actor.strip() or not reason.strip():
            raise InvalidQueryError("approval requires actor and reason")
        value = await self._repository.approve(
            analysis_id, str(uuid4()), actor.strip(), reason.strip()
        )
        if value is None:
            raise ResourceNotFoundError("analysis")
        return value

    async def get(self, analysis_id: str) -> Analysis:
        value = await self._repository.get(analysis_id)
        if value is None:
            raise ResourceNotFoundError("analysis")
        return value

    async def list_by_match(self, match_id: int) -> tuple[Analysis, ...]:
        value = await self._repository.list_by_match(match_id)
        if value is None:
            raise ResourceNotFoundError("match")
        return value

    async def snapshot_for_analysis(self, analysis_id: str) -> AnalysisSnapshot:
        value = await self._repository.get_snapshot_by_analysis(analysis_id)
        if value is None:
            raise ResourceNotFoundError("analysis snapshot")
        return value

    async def snapshot(self, snapshot_id: str) -> AnalysisSnapshot:
        value = await self._repository.get_snapshot(snapshot_id)
        if value is None:
            raise ResourceNotFoundError("analysis snapshot")
        return value
