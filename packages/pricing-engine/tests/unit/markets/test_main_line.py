"""Unit tests for deterministic Asian candidate catalogues and main lines."""

import math

from lvfi_pricing.core.errors import CalculationError
from lvfi_pricing.distributions import (
    PoissonDistribution,
    ScoreProbabilityMatrix,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.domain import PoissonRate, QuarterLine
from lvfi_pricing.markets import (
    AsianMainLine,
    generate_asian_handicap_candidates,
    generate_asian_total_candidates,
    select_asian_handicap_main_line,
    select_asian_total_main_line,
)
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection


def matrix(home: float = 1.0, away: float = 1.5) -> ScoreProbabilityMatrix:
    distributions = []
    for value in (home, away):
        rate = PoissonRate.create(value)
        assert isinstance(rate, PoissonRate)
        distribution = build_poisson_distribution(rate)
        assert isinstance(distribution, PoissonDistribution)
        distributions.append(distribution)
    result = build_score_probability_matrix(distributions[0], distributions[1])
    assert isinstance(result, ScoreProbabilityMatrix)
    return result


def test_candidate_catalogues_are_canonical() -> None:
    source = matrix()
    handicap = generate_asian_handicap_candidates(source)
    total = generate_asian_total_candidates(source)
    assert isinstance(handicap, tuple) and isinstance(total, tuple)
    assert tuple(line.quarters for line in handicap) == tuple(
        sorted(line.quarters for line in handicap)
    )
    assert len({line.quarters for line in handicap}) == len(handicap)
    assert total[0] == QuarterLine(0)
    assert all(line.quarters >= 0 for line in total)
    away = generate_asian_handicap_candidates(source, HandicapSelection.AWAY)
    assert isinstance(away, tuple) and handicap != away
    assert isinstance(
        generate_asian_handicap_candidates(object()),  # type: ignore[arg-type]
        CalculationError,
    )
    assert isinstance(
        generate_asian_handicap_candidates(source, object()),  # type: ignore[arg-type]
        CalculationError,
    )


def test_main_lines_are_balanced_and_have_canonical_opposites() -> None:
    source = matrix()
    handicap = select_asian_handicap_main_line(source)
    total = select_asian_total_main_line(source)
    assert isinstance(handicap, AsianMainLine) and isinstance(total, AsianMainLine)
    assert handicap.reference_selection is HandicapSelection.HOME
    assert handicap.opposite_price.selection is HandicapSelection.AWAY
    assert handicap.opposite_price.line.quarters == -handicap.line.quarters
    assert total.reference_selection is AsianTotalSelection.OVER
    assert total.opposite_price.selection is AsianTotalSelection.UNDER
    assert total.opposite_price.line == total.line
    for result in (handicap, total):
        assert result.evaluated_lines > 0
        assert result.balance_distance == abs(result.balance_value)
        assert math.isclose(
            result.balance_value,
            2.0 * result.reference_price.expected_profile.won_fraction
            + result.reference_price.expected_profile.pushed_fraction
            - 1.0,
        )


def test_custom_catalogue_validation_and_tie_breaking() -> None:
    source = matrix(0.0, 0.0)
    selected = select_asian_handicap_main_line(
        source, (QuarterLine(-1), QuarterLine(1))
    )
    assert isinstance(selected, AsianMainLine)
    assert selected.line == QuarterLine(-1)
    for invalid in (
        (),
        (QuarterLine(1), QuarterLine(0)),
        (QuarterLine(0), QuarterLine(0)),
    ):
        assert isinstance(
            select_asian_total_main_line(source, invalid), CalculationError
        )
