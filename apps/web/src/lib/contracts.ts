export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface Reference {
  id: number;
  display_name: string;
  created_at: string;
}

export interface Season {
  id: number;
  competition: Reference;
  label: string;
  created_at: string;
}

export interface Match {
  id: number;
  played_on: string;
  competition: Reference;
  season: Season;
  home_team: Reference;
  away_team: Reference;
  has_statistics: boolean;
  created_at: string;
}

export interface TeamSample {
  venue_condition: string;
  expected_count: number;
  found_count: number;
  complete: boolean;
  insufficient_reason: string | null;
  matches: Array<{ match: Match }>;
}

export interface MethodOneSample {
  target_match: Match;
  parameters: {
    requested_count: number;
    competition_id: number;
    season_id: number;
    include_previous_season: boolean;
    ordering: string;
    statistic_periods: string[];
  };
  home_sample: TeamSample;
  away_sample: TeamSample;
  warnings: string[];
}

export type PricingExecutionStatus =
  | "completed"
  | "blocked_sample_incomplete"
  | "technical_failure";

export interface PricingExecution {
  execution_id: string;
  match_id: number;
  status: PricingExecutionStatus;
  created_at: string;
  finalized_at: string;
  correlation_id: string;
  sample_fingerprint: string;
  input_fingerprint: string | null;
  result_fingerprint: string | null;
  pricing_engine_version: string;
  distribution_version: string;
  method_one_version: string;
  schema_version: number;
  public_parameters: Record<string, unknown>;
  canonical_input: Record<string, unknown> | null;
  canonical_result: Record<string, unknown> | null;
  failure_code: string | null;
}

export interface MarketPricing {
  market_pricing_id: string;
  match_id: number;
  created_at: string;
  finalized_at: string;
  correlation_id: string;
  pricing_engine_version: string;
  canonical_input: Record<string, unknown>;
  canonical_result: Record<string, unknown>;
}

export interface MarketReferenceObservation {
  observation_id: string;
  match_id: number;
  market_pricing_id: string;
  market_code: string;
  selection: string;
  model_line_quarters: number | null;
  reference_line_quarters: number | null;
  reference_value: number;
  observed_at: string;
  created_at: string;
  correlation_id: string;
}

export interface ModelReferenceComparison {
  observation: MarketReferenceObservation;
  model_value: number;
  line_difference_quarters: number | null;
}
