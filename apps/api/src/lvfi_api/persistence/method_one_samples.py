"""Async PostgreSQL queries for Method 1 historical sample construction."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from sqlalchemy import and_, or_
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError

from lvfi_api.application.method_one_samples import MethodOneSampleRepository
from lvfi_api.domain.errors import PersistenceUnavailableError
from lvfi_api.domain.historical_queries import (
    Match,
    MatchStatistics,
    MethodOneSampleMatch,
)
from lvfi_api.persistence.historical_models import match_statistics, matches
from lvfi_api.persistence.historical_queries import (
    SessionProvider,
    _match,
    _match_select,
    _team_statistics,
)


class SqlAlchemyMethodOneSampleRepository(MethodOneSampleRepository):
    """Issue two bounded joined queries, one for each venue-conditioned series."""

    def __init__(self, database: SessionProvider) -> None:
        self._database = database

    async def get_samples(
        self, target_match: Match
    ) -> tuple[tuple[MethodOneSampleMatch, ...], tuple[MethodOneSampleMatch, ...]]:
        cutoff = or_(
            matches.c.played_on < target_match.played_on,
            and_(
                matches.c.played_on == target_match.played_on,
                matches.c.id < target_match.id,
            ),
        )
        statistics_columns = tuple(
            column for column in match_statistics.c if column.name != "match_id"
        )
        statement = (
            _match_select()
            .add_columns(*statistics_columns)
            .where(matches.c.season_id == target_match.season.id, cutoff)
            .where(match_statistics.c.match_id.is_not(None))
            .order_by(matches.c.played_on.desc(), matches.c.id.asc())
            .limit(10)
        )
        home_statement = statement.where(
            matches.c.home_team_id == target_match.home_team.id
        )
        away_statement = statement.where(
            matches.c.away_team_id == target_match.away_team.id
        )
        try:
            async with self._database.session() as session:
                home_rows = (await session.execute(home_statement)).mappings().all()
                away_rows = (await session.execute(away_statement)).mappings().all()
        except SQLAlchemyError as exc:
            raise PersistenceUnavailableError("historical sample query failed") from exc
        return self._map_rows(home_rows), self._map_rows(away_rows)

    @staticmethod
    def _map_rows(rows: Sequence[RowMapping]) -> tuple[MethodOneSampleMatch, ...]:
        return tuple(
            MethodOneSampleMatch(
                match=_match(row),
                statistics=_statistics(row),
            )
            for row in rows
        )


def _statistics(row: RowMapping) -> MatchStatistics:
    return MatchStatistics(
        match_id=cast(int, row["match_id"]),
        home=_team_statistics(row, "home"),
        away=_team_statistics(row, "away"),
    )
