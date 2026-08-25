"""Public-only Pricing Engine adapter for versioned market-pricing snapshots."""

from __future__ import annotations

from lvfi_pricing.core import CalculationError, NumericPolicy
from lvfi_pricing.domain import PoissonRate, QuarterLine
from lvfi_pricing.engine import (
    AsianHandicapMainLineRequest,
    AsianHandicapRequest,
    AsianTotalMainLineRequest,
    AsianTotalRequest,
    BothTeamsToScoreRequest,
    DoubleChanceRequest,
    PricingRequest,
    ThreeWayResultRequest,
    TotalGoalsRequest,
    run_pricing_engine,
)
from lvfi_pricing.markets import HalfGoalLine
from lvfi_pricing.serialization import serialize_pricing_result
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection

from lvfi_api.domain.market_pricings import RequestedMarket


class PublicMarketPricingEngineFacade:
    """Use exported Engine modules, never its implementation modules."""

    @staticmethod
    def price(
        home_rate: float, away_rate: float, requested: tuple[RequestedMarket, ...]
    ) -> tuple[bytes, str, str] | None:
        home = PoissonRate.create(home_rate)
        away = PoissonRate.create(away_rate)
        if isinstance(home, CalculationError) or isinstance(away, CalculationError):
            return None
        engine_requests = tuple(_engine_request(item) for item in requested)
        if any(item is None for item in engine_requests):
            return None
        pricing_request = PricingRequest.create(
            home,
            away,
            tuple(item for item in engine_requests if item is not None),
            NumericPolicy(),
        )
        if isinstance(pricing_request, CalculationError):
            return None
        result = run_pricing_engine(pricing_request)
        if isinstance(result, CalculationError):
            return None
        payload = serialize_pricing_result(result)
        if isinstance(payload, CalculationError):
            return None
        return (
            payload.canonical_bytes,
            payload.content_hash,
            result.metadata.package_version,
        )


def _engine_request(value: RequestedMarket) -> object | None:
    if value.code == "three_way_result" and _empty(value):
        return ThreeWayResultRequest()
    if value.code == "double_chance" and _empty(value):
        return DoubleChanceRequest()
    if value.code == "both_teams_to_score" and _empty(value):
        return BothTeamsToScoreRequest()
    if (
        value.code == "total_goals"
        and value.line_half_units is not None
        and value.selection is None
        and value.line_quarters is None
    ):
        return TotalGoalsRequest(HalfGoalLine(value.line_half_units))
    if (
        value.code == "asian_handicap"
        and value.selection is not None
        and value.line_quarters is not None
        and value.line_half_units is None
    ):
        try:
            return AsianHandicapRequest(
                HandicapSelection(value.selection), QuarterLine(value.line_quarters)
            )
        except (TypeError, ValueError):
            return None
    if (
        value.code == "asian_total"
        and value.selection is not None
        and value.line_quarters is not None
        and value.line_half_units is None
    ):
        try:
            return AsianTotalRequest(
                AsianTotalSelection(value.selection), QuarterLine(value.line_quarters)
            )
        except (TypeError, ValueError):
            return None
    if value.code == "asian_handicap_main_line" and _empty(value):
        return AsianHandicapMainLineRequest()
    if value.code == "asian_total_main_line" and _empty(value):
        return AsianTotalMainLineRequest()
    return None


def _empty(value: RequestedMarket) -> bool:
    return (
        value.selection is None
        and value.line_half_units is None
        and value.line_quarters is None
    )


public_market_pricing_engine = PublicMarketPricingEngineFacade()


def pricing_engine_public_api_is_available() -> bool:
    """Executable guard for the public-only boundary."""
    return callable(public_market_pricing_engine.price)
