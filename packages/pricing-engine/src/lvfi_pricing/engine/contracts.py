"""Immutable request and result contracts for the internal pricing engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy
from lvfi_pricing.distributions import (
    GoalDifferenceDistribution,
    PoissonDistribution,
    ScoreProbabilityMatrix,
)
from lvfi_pricing.domain import PoissonRate, QuarterLine
from lvfi_pricing.markets import (
    AsianMainLine,
    AsianMarketPrice,
    HalfGoalLine,
    MarketPrices,
)
from lvfi_pricing.settlement import AsianTotalSelection, HandicapSelection

PACKAGE_VERSION = "0.10.0"
REQUEST_SCHEMA_VERSION = 1
RESULT_SCHEMA_VERSION = 1


class RequestedMarketCode(StrEnum):
    THREE_WAY_RESULT = "three_way_result"
    DOUBLE_CHANCE = "double_chance"
    BOTH_TEAMS_TO_SCORE = "both_teams_to_score"
    TOTAL_GOALS = "total_goals"
    ASIAN_HANDICAP = "asian_handicap"
    ASIAN_TOTAL = "asian_total"
    ASIAN_HANDICAP_MAIN_LINE = "asian_handicap_main_line"
    ASIAN_TOTAL_MAIN_LINE = "asian_total_main_line"


@dataclass(frozen=True, slots=True)
class ThreeWayResultRequest:
    code: RequestedMarketCode = RequestedMarketCode.THREE_WAY_RESULT


@dataclass(frozen=True, slots=True)
class DoubleChanceRequest:
    code: RequestedMarketCode = RequestedMarketCode.DOUBLE_CHANCE


@dataclass(frozen=True, slots=True)
class BothTeamsToScoreRequest:
    code: RequestedMarketCode = RequestedMarketCode.BOTH_TEAMS_TO_SCORE


@dataclass(frozen=True, slots=True)
class TotalGoalsRequest:
    line: HalfGoalLine
    code: RequestedMarketCode = RequestedMarketCode.TOTAL_GOALS


@dataclass(frozen=True, slots=True)
class AsianHandicapRequest:
    selection: HandicapSelection
    line: QuarterLine
    code: RequestedMarketCode = RequestedMarketCode.ASIAN_HANDICAP


@dataclass(frozen=True, slots=True)
class AsianTotalRequest:
    selection: AsianTotalSelection
    line: QuarterLine
    code: RequestedMarketCode = RequestedMarketCode.ASIAN_TOTAL


@dataclass(frozen=True, slots=True)
class AsianHandicapMainLineRequest:
    code: RequestedMarketCode = RequestedMarketCode.ASIAN_HANDICAP_MAIN_LINE


@dataclass(frozen=True, slots=True)
class AsianTotalMainLineRequest:
    code: RequestedMarketCode = RequestedMarketCode.ASIAN_TOTAL_MAIN_LINE


type MarketRequest = (
    ThreeWayResultRequest
    | DoubleChanceRequest
    | BothTeamsToScoreRequest
    | TotalGoalsRequest
    | AsianHandicapRequest
    | AsianTotalRequest
    | AsianHandicapMainLineRequest
    | AsianTotalMainLineRequest
)
type MarketResult = MarketPrices | AsianMarketPrice | AsianMainLine


def market_request_key(request: MarketRequest) -> tuple[int, int, str]:
    order = {code: index for index, code in enumerate(RequestedMarketCode)}
    line, selection = 0, ""
    if isinstance(request, TotalGoalsRequest):
        line = request.line.half_units
    elif isinstance(request, (AsianHandicapRequest, AsianTotalRequest)):
        line, selection = request.line.quarters, request.selection.value
    return order[request.code], line, selection


def _valid_market_request(value: object) -> bool:
    if isinstance(
        value,
        (
            ThreeWayResultRequest,
            DoubleChanceRequest,
            BothTeamsToScoreRequest,
            AsianHandicapMainLineRequest,
            AsianTotalMainLineRequest,
        ),
    ):
        return True
    if isinstance(value, TotalGoalsRequest):
        return value.code is RequestedMarketCode.TOTAL_GOALS and isinstance(
            value.line, HalfGoalLine
        )
    if isinstance(value, AsianHandicapRequest):
        return (
            value.code is RequestedMarketCode.ASIAN_HANDICAP
            and isinstance(value.selection, HandicapSelection)
            and isinstance(value.line, QuarterLine)
        )
    if isinstance(value, AsianTotalRequest):
        return (
            value.code is RequestedMarketCode.ASIAN_TOTAL
            and isinstance(value.selection, AsianTotalSelection)
            and isinstance(value.line, QuarterLine)
        )
    return False


@dataclass(frozen=True, slots=True)
class PricingRequest:
    home_rate: PoissonRate
    away_rate: PoissonRate
    requested_markets: tuple[MarketRequest, ...]
    numeric_policy: NumericPolicy
    request_schema_version: int = REQUEST_SCHEMA_VERSION
    engine_version: str = PACKAGE_VERSION

    @classmethod
    def create(
        cls,
        home_rate: object,
        away_rate: object,
        requested_markets: object,
        numeric_policy: object = NumericPolicy(),
        request_schema_version: object = REQUEST_SCHEMA_VERSION,
        engine_version: object = PACKAGE_VERSION,
    ) -> PricingRequest | CalculationError:
        if not isinstance(home_rate, PoissonRate) or not isinstance(
            away_rate, PoissonRate
        ):
            return CalculationError(
                ErrorCode.INVALID_LAMBDA, "rates must be PoissonRate values", "rate"
            )
        if not isinstance(numeric_policy, NumericPolicy):
            return CalculationError(
                ErrorCode.CONFIGURATION_ERROR,
                "numeric_policy must be a NumericPolicy",
                "numeric_policy",
            )
        if (
            isinstance(request_schema_version, bool)
            or request_schema_version != REQUEST_SCHEMA_VERSION
        ):
            return CalculationError(
                ErrorCode.SCHEMA_VERSION_UNSUPPORTED,
                "unsupported request schema version",
                "request_schema_version",
            )
        if not isinstance(engine_version, str) or engine_version != PACKAGE_VERSION:
            return CalculationError(
                ErrorCode.CONFIGURATION_ERROR,
                "engine_version is unsupported",
                "engine_version",
            )
        if not isinstance(requested_markets, tuple) or not requested_markets:
            return CalculationError(
                ErrorCode.INVALID_MARKET,
                "requested_markets must be a non-empty tuple",
                "requested_markets",
            )
        if any(not _valid_market_request(item) for item in requested_markets):
            return CalculationError(
                ErrorCode.INVALID_MARKET,
                "market request is invalid",
                "requested_markets",
            )
        canonical = tuple(sorted(requested_markets, key=market_request_key))
        if len(set(canonical)) != len(canonical):
            return CalculationError(
                ErrorCode.INVALID_MARKET,
                "market requests must be unique",
                "requested_markets",
            )
        return cls(
            home_rate,
            away_rate,
            canonical,
            numeric_policy,
            request_schema_version,
            engine_version,
        )


@dataclass(frozen=True, slots=True)
class PricingEngineMetadata:
    package_version: str
    request_schema_version: int
    result_schema_version: int
    numeric_policy: NumericPolicy
    home_poisson_max_count: int
    away_poisson_max_count: int
    score_matrix_dimensions: tuple[int, int]
    calculated_markets: tuple[RequestedMarketCode, ...]
    warnings_count: int
    deterministic: bool = True


@dataclass(frozen=True, slots=True)
class PricingResult:
    request: PricingRequest
    home_distribution: PoissonDistribution
    away_distribution: PoissonDistribution
    score_matrix: ScoreProbabilityMatrix
    goal_difference: GoalDifferenceDistribution
    market_results: tuple[MarketResult, ...]
    metadata: PricingEngineMetadata
    warnings: tuple[CalculationWarning, ...]
    errors: tuple[CalculationError, ...] = ()

    @property
    def success(self) -> bool:
        return not self.errors


type PricingExecutionResult = PricingResult | CalculationError
