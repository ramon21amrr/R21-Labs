"""Repeatable development benchmark for complete Asian-pricing scenarios."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
from time import perf_counter

from lvfi_pricing.core import CalculationError
from lvfi_pricing.domain import PoissonRate, QuarterLine
from lvfi_pricing.engine import (
    AsianHandicapMainLineRequest,
    AsianHandicapRequest,
    AsianTotalMainLineRequest,
    AsianTotalRequest,
    BothTeamsToScoreRequest,
    DoubleChanceRequest,
    MarketRequest,
    PricingRequest,
    ThreeWayResultRequest,
    TotalGoalsRequest,
    run_pricing_engine,
)
from lvfi_pricing.markets import HalfGoalLine
from lvfi_pricing.serialization import serialize_pricing_result
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection

CASES = (
    (1.0, 1.0),
    (2.5, 1.2),
    (5.0, 3.0),
    (7.5, 7.5),
    (10.0, 10.0),
)


def _markets() -> tuple[MarketRequest, ...]:
    return (
        ThreeWayResultRequest(),
        DoubleChanceRequest(),
        BothTeamsToScoreRequest(),
        TotalGoalsRequest(HalfGoalLine(5)),
        AsianHandicapRequest(HandicapSelection.HOME, QuarterLine(0)),
        AsianHandicapRequest(HandicapSelection.AWAY, QuarterLine(1)),
        AsianHandicapRequest(HandicapSelection.HOME, QuarterLine(2)),
        AsianTotalRequest(AsianTotalSelection.OVER, QuarterLine(8)),
        AsianTotalRequest(AsianTotalSelection.UNDER, QuarterLine(9)),
        AsianTotalRequest(AsianTotalSelection.OVER, QuarterLine(10)),
        AsianHandicapMainLineRequest(),
        AsianTotalMainLineRequest(),
    )


def _run(home: float, away: float) -> None:
    request = PricingRequest.create(PoissonRate(home), PoissonRate(away), _markets())
    if isinstance(request, CalculationError):
        raise request
    result = run_pricing_engine(request)
    if isinstance(result, CalculationError):
        raise result
    payload = serialize_pricing_result(result)
    if isinstance(payload, CalculationError):
        raise payload
    if not payload.canonical_bytes:
        raise RuntimeError("canonical payload is empty")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", nargs=2, type=float, metavar=("HOME", "AWAY"))
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--repeat", type=int, default=5)
    args = parser.parse_args()
    cases = (tuple(args.case),) if args.case is not None else CASES
    output: dict[str, object] = {
        "python": sys.version,
        "platform": platform.platform(),
        "warmup": args.warmup,
        "repeat": args.repeat,
        "cases": {},
    }
    measured_value = output["cases"]
    assert isinstance(measured_value, dict)
    measured: dict[str, object] = measured_value
    for home, away in cases:
        for _ in range(args.warmup):
            _run(home, away)
        timings: list[float] = []
        for _ in range(args.repeat):
            started = perf_counter()
            _run(home, away)
            timings.append(perf_counter() - started)
        measured[f"{home:.1f}x{away:.1f}"] = {
            "seconds": timings,
            "median": statistics.median(timings),
            "maximum": max(timings),
        }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
