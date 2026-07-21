"""Thin, deterministic composition of the approved pricing modules."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from types import MappingProxyType
from typing import cast

from lvfi_pricing.core.errors import CalculationError, CalculationWarning, ErrorCode
from lvfi_pricing.core.numeric import NumericPolicy
from lvfi_pricing.distributions import (
    GoalDifferenceDistribution,
    ScoreProbabilityMatrix,
    build_goal_difference_distribution,
    build_poisson_distribution,
    build_score_probability_matrix,
)
from lvfi_pricing.markets import (
    MarketPrices,
    price_asian_handicap,
    price_asian_total,
    price_btts,
    price_double_chance,
    price_three_way_result,
    price_total_goals,
    select_asian_handicap_main_line,
    select_asian_total_main_line,
)

from .contracts import (
    PACKAGE_VERSION,
    RESULT_SCHEMA_VERSION,
    AsianHandicapMainLineRequest,
    AsianHandicapRequest,
    AsianTotalMainLineRequest,
    AsianTotalRequest,
    BothTeamsToScoreRequest,
    DoubleChanceRequest,
    MarketRequest,
    MarketResult,
    PricingEngineMetadata,
    PricingExecutionResult,
    PricingRequest,
    PricingResult,
    RequestedMarketCode,
    ThreeWayResultRequest,
    TotalGoalsRequest,
)


def _validate_request(request: object) -> PricingRequest | CalculationError:
    if not isinstance(request, PricingRequest):
        return CalculationError(
            ErrorCode.CONFIGURATION_ERROR, "request must be a PricingRequest", "request"
        )
    return PricingRequest.create(
        request.home_rate,
        request.away_rate,
        request.requested_markets,
        request.numeric_policy,
        request.request_schema_version,
        request.engine_version,
    )


def _warning_key(warning: CalculationWarning) -> tuple[str, str, str, str, str]:
    return (
        warning.code.value,
        warning.severity.value,
        warning.message,
        "" if warning.field is None else warning.field,
        repr(warning.context),
    )


def _warnings(items: Iterable[object]) -> tuple[CalculationWarning, ...]:
    values: list[CalculationWarning] = []
    for item in items:
        item_warnings = getattr(item, "warnings", ())
        if isinstance(item_warnings, tuple):
            values.extend(
                warning
                for warning in item_warnings
                if isinstance(warning, CalculationWarning)
            )
    unique: dict[tuple[str, str, str, str, str], CalculationWarning] = {}
    for warning in values:
        unique.setdefault(_warning_key(warning), warning)
    return tuple(sorted(unique.values(), key=_warning_key))


def _price_market(
    request: MarketRequest,
    matrix: ScoreProbabilityMatrix,
    difference: GoalDifferenceDistribution,
    policy: NumericPolicy,
    three_way: MarketPrices | None,
) -> MarketResult | CalculationError:
    handler = _MARKET_HANDLERS.get(type(request))
    if handler is None:
        raise TypeError("market route received an incompatible request")
    if isinstance(request, ThreeWayResultRequest):
        return cast(_ThreeWayHandler, handler)(
            request, matrix, difference, policy, three_way
        )
    if isinstance(request, DoubleChanceRequest):
        return cast(_DoubleChanceHandler, handler)(
            request, matrix, difference, policy, three_way
        )
    if isinstance(request, BothTeamsToScoreRequest):
        return cast(_BttsHandler, handler)(
            request, matrix, difference, policy, three_way
        )
    if isinstance(request, TotalGoalsRequest):
        return cast(_TotalHandler, handler)(
            request, matrix, difference, policy, three_way
        )
    if isinstance(request, AsianHandicapRequest):
        return cast(_HandicapHandler, handler)(
            request, matrix, difference, policy, three_way
        )
    if isinstance(request, AsianTotalRequest):
        return cast(_AsianTotalHandler, handler)(
            request, matrix, difference, policy, three_way
        )
    if isinstance(request, AsianHandicapMainLineRequest):
        return cast(_HandicapMainHandler, handler)(
            request, matrix, difference, policy, three_way
        )
    return cast(_TotalMainHandler, handler)(
        request, matrix, difference, policy, three_way
    )


type _ThreeWayHandler = Callable[
    [
        ThreeWayResultRequest,
        ScoreProbabilityMatrix,
        GoalDifferenceDistribution,
        NumericPolicy,
        MarketPrices | None,
    ],
    MarketResult | CalculationError,
]
type _DoubleChanceHandler = Callable[
    [
        DoubleChanceRequest,
        ScoreProbabilityMatrix,
        GoalDifferenceDistribution,
        NumericPolicy,
        MarketPrices | None,
    ],
    MarketResult | CalculationError,
]
type _BttsHandler = Callable[
    [
        BothTeamsToScoreRequest,
        ScoreProbabilityMatrix,
        GoalDifferenceDistribution,
        NumericPolicy,
        MarketPrices | None,
    ],
    MarketResult | CalculationError,
]
type _TotalHandler = Callable[
    [
        TotalGoalsRequest,
        ScoreProbabilityMatrix,
        GoalDifferenceDistribution,
        NumericPolicy,
        MarketPrices | None,
    ],
    MarketResult | CalculationError,
]
type _HandicapHandler = Callable[
    [
        AsianHandicapRequest,
        ScoreProbabilityMatrix,
        GoalDifferenceDistribution,
        NumericPolicy,
        MarketPrices | None,
    ],
    MarketResult | CalculationError,
]
type _AsianTotalHandler = Callable[
    [
        AsianTotalRequest,
        ScoreProbabilityMatrix,
        GoalDifferenceDistribution,
        NumericPolicy,
        MarketPrices | None,
    ],
    MarketResult | CalculationError,
]
type _HandicapMainHandler = Callable[
    [
        AsianHandicapMainLineRequest,
        ScoreProbabilityMatrix,
        GoalDifferenceDistribution,
        NumericPolicy,
        MarketPrices | None,
    ],
    MarketResult | CalculationError,
]
type _TotalMainHandler = Callable[
    [
        AsianTotalMainLineRequest,
        ScoreProbabilityMatrix,
        GoalDifferenceDistribution,
        NumericPolicy,
        MarketPrices | None,
    ],
    MarketResult | CalculationError,
]
type _MarketHandler = (
    _ThreeWayHandler
    | _DoubleChanceHandler
    | _BttsHandler
    | _TotalHandler
    | _HandicapHandler
    | _AsianTotalHandler
    | _HandicapMainHandler
    | _TotalMainHandler
)


def _three_way(
    request: ThreeWayResultRequest,
    matrix: ScoreProbabilityMatrix,
    difference: GoalDifferenceDistribution,
    policy: NumericPolicy,
    three_way: MarketPrices | None,
) -> MarketResult | CalculationError:
    return price_three_way_result(difference, policy)


def _double_chance(
    request: DoubleChanceRequest,
    matrix: ScoreProbabilityMatrix,
    difference: GoalDifferenceDistribution,
    policy: NumericPolicy,
    three_way: MarketPrices | None,
) -> MarketResult | CalculationError:
    result = (
        three_way
        if three_way is not None
        else price_three_way_result(difference, policy)
    )
    return (
        result
        if isinstance(result, CalculationError)
        else price_double_chance(result, policy)
    )


def _btts(
    request: BothTeamsToScoreRequest,
    matrix: ScoreProbabilityMatrix,
    difference: GoalDifferenceDistribution,
    policy: NumericPolicy,
    three_way: MarketPrices | None,
) -> MarketResult | CalculationError:
    return price_btts(matrix, policy)


def _total(
    request: TotalGoalsRequest,
    matrix: ScoreProbabilityMatrix,
    difference: GoalDifferenceDistribution,
    policy: NumericPolicy,
    three_way: MarketPrices | None,
) -> MarketResult | CalculationError:
    return price_total_goals(matrix, request.line, policy)


def _handicap(
    request: AsianHandicapRequest,
    matrix: ScoreProbabilityMatrix,
    difference: GoalDifferenceDistribution,
    policy: NumericPolicy,
    three_way: MarketPrices | None,
) -> MarketResult | CalculationError:
    return price_asian_handicap(matrix, request.selection, request.line, policy)


def _asian_total(
    request: AsianTotalRequest,
    matrix: ScoreProbabilityMatrix,
    difference: GoalDifferenceDistribution,
    policy: NumericPolicy,
    three_way: MarketPrices | None,
) -> MarketResult | CalculationError:
    return price_asian_total(matrix, request.selection, request.line, policy)


def _handicap_main(
    request: AsianHandicapMainLineRequest,
    matrix: ScoreProbabilityMatrix,
    difference: GoalDifferenceDistribution,
    policy: NumericPolicy,
    three_way: MarketPrices | None,
) -> MarketResult | CalculationError:
    return select_asian_handicap_main_line(matrix, policy=policy)


def _total_main(
    request: AsianTotalMainLineRequest,
    matrix: ScoreProbabilityMatrix,
    difference: GoalDifferenceDistribution,
    policy: NumericPolicy,
    three_way: MarketPrices | None,
) -> MarketResult | CalculationError:
    return select_asian_total_main_line(matrix, policy=policy)


_VALID_REQUEST_TYPES: tuple[type[MarketRequest], ...] = (
    ThreeWayResultRequest,
    DoubleChanceRequest,
    BothTeamsToScoreRequest,
    TotalGoalsRequest,
    AsianHandicapRequest,
    AsianTotalRequest,
    AsianHandicapMainLineRequest,
    AsianTotalMainLineRequest,
)
_MARKET_HANDLERS: Mapping[type[MarketRequest], _MarketHandler] = MappingProxyType(
    {
        ThreeWayResultRequest: _three_way,
        DoubleChanceRequest: _double_chance,
        BothTeamsToScoreRequest: _btts,
        TotalGoalsRequest: _total,
        AsianHandicapRequest: _handicap,
        AsianTotalRequest: _asian_total,
        AsianHandicapMainLineRequest: _handicap_main,
        AsianTotalMainLineRequest: _total_main,
    }
)


def run_pricing_engine(request: PricingRequest) -> PricingExecutionResult:
    valid_request = _validate_request(request)
    if isinstance(valid_request, CalculationError):
        return valid_request
    home = build_poisson_distribution(
        valid_request.home_rate, valid_request.numeric_policy
    )
    if isinstance(home, CalculationError):
        return home
    away = build_poisson_distribution(
        valid_request.away_rate, valid_request.numeric_policy
    )
    if isinstance(away, CalculationError):
        return away
    matrix = build_score_probability_matrix(home, away, valid_request.numeric_policy)
    if isinstance(matrix, CalculationError):
        return matrix
    difference = build_goal_difference_distribution(
        matrix, valid_request.numeric_policy
    )
    if isinstance(difference, CalculationError):
        return difference
    results: list[MarketResult] = []
    three_way: MarketPrices | None = None
    for market_request in valid_request.requested_markets:
        result = _price_market(
            market_request, matrix, difference, valid_request.numeric_policy, three_way
        )
        if isinstance(result, CalculationError):
            return result
        results.append(result)
        if market_request.code is RequestedMarketCode.THREE_WAY_RESULT:
            three_way = cast(MarketPrices, result)
    warnings = _warnings((home, away, matrix, difference, *results))
    metadata = PricingEngineMetadata(
        PACKAGE_VERSION,
        valid_request.request_schema_version,
        RESULT_SCHEMA_VERSION,
        valid_request.numeric_policy,
        home.max_count,
        away.max_count,
        (matrix.home_max_goals + 1, matrix.away_max_goals + 1),
        tuple(item.code for item in valid_request.requested_markets),
        len(warnings),
    )
    return PricingResult(
        valid_request,
        home,
        away,
        matrix,
        difference,
        tuple(results),
        metadata,
        warnings,
    )
