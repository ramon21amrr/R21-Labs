from datetime import UTC, datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from lvfi_pricing.models.samples import (
    MatchIdentity,
    MatchState,
    SampleFilter,
    SampleWindowKind,
    VenueCondition,
)


@settings(max_examples=20, derandomize=True)
@given(st.permutations(("league-c", "league-a", "league-b")))
def test_collection_canonicalization_is_permutation_invariant(
    values: tuple[str, ...] | list[str],
) -> None:
    values = tuple(values)
    first = SampleFilter(
        VenueCondition.HOME, SampleWindowKind.FULL_SEASON, season_ids=values
    )
    second = SampleFilter(
        VenueCondition.HOME,
        SampleWindowKind.FULL_SEASON,
        season_ids=tuple(reversed(values)),
    )
    assert first == second


@settings(max_examples=20, derandomize=True)
@given(st.integers(min_value=-12, max_value=12))
def test_equivalent_timezones_canonicalize_to_utc(offset: int) -> None:
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    shifted = instant.astimezone(UTC)
    assert MatchIdentity("match", shifted, MatchState.COMPLETED) == MatchIdentity(
        "match", instant, MatchState.COMPLETED
    )
