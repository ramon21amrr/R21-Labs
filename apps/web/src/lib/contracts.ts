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

export interface ImportPreview {
  source_sha256: string;
  sheet_name: string;
  total_records: number;
  accepted_records: number;
  rejected_records: number;
  warning_records: number;
  dry_run: boolean;
  already_imported: boolean;
}

export interface FutureMatchDraft {
  played_on: string;
  competition: string;
  season: string;
  home_team: string;
  away_team: string;
  actor?: string;
}

export interface FutureMatch extends Required<FutureMatchDraft> {
  match_id: number;
  created_at: string;
}

export interface StatisticRevisionDraft {
  statistic_field: string;
  availability: "available" | "missing";
  new_value: number | null;
  actor?: string;
  reason: string;
}

export interface StatisticRevision extends Required<StatisticRevisionDraft> {
  revision_id: number;
  match_id: number;
  previous_value: number | null;
  created_at: string;
}

export type StatisticsSampleSize = 5 | 10 | 15 | 20;
export type StatisticsVenue = "home" | "away" | "overall";
export type StatisticsCompetitionScope = "target_competition" | "all_eligible";
export type StatisticsSeasonScope = "current" | "current_and_previous";
export type StatisticsMetric = "goals_scored" | "goals_conceded" | "result_win" | "corners" | "shots_on_target" | "shots" | "cards" | "fouls";
export type StatisticsComparator = "at_least" | "at_most" | "equal";

export interface StatisticsSampleRequest {
  team_id: number;
  sample_size: StatisticsSampleSize;
  venue: StatisticsVenue;
  competition_scope: StatisticsCompetitionScope;
  season_scope: StatisticsSeasonScope;
  previous_season_id?: number;
  metric: StatisticsMetric;
  comparator?: StatisticsComparator;
  achievement_target?: number;
}

export interface StatisticsSampleFilters {
  team_id: number;
  sample_size: StatisticsSampleSize;
  venue: StatisticsVenue;
  competition_scope: StatisticsCompetitionScope;
  season_scope: StatisticsSeasonScope;
  previous_season_id: number | null;
  metric: StatisticsMetric;
  comparator: StatisticsComparator | null;
  achievement_target: number | null;
}

export interface StatisticsSampleTarget {
  match_id: number;
  played_on: string;
  competition_id: number;
  competition_name: string;
  season_id: number;
  season_label: string;
  home_team_id: number;
  home_team_name: string;
  away_team_id: number;
  away_team_name: string;
}

export interface StatisticsSampleMatch {
  match_id: number;
  played_on: string;
  competition_id: number;
  competition_name: string;
  season_id: number;
  season_label: string;
  home_team_id: number;
  home_team_name: string;
  away_team_id: number;
  away_team_name: string;
  venue: Exclude<StatisticsVenue, "overall">;
  value: number | null;
  unavailable_reason: string | null;
}

export interface StatisticsUnavailableValue {
  match_id: number;
  reason: string;
}

export interface StatisticsFrequency {
  value: number;
  count: number;
}

export interface StatisticsSample {
  target_match: StatisticsSampleTarget;
  filters: StatisticsSampleFilters;
  ordering: string;
  candidate_count: number;
  used_count: number;
  candidate_match_ids: number[];
  used_match_ids: number[];
  candidates: StatisticsSampleMatch[];
  used_matches: StatisticsSampleMatch[];
  valid_values: number[];
  unavailable_values: StatisticsUnavailableValue[];
  available_count: number;
  mean: number | null;
  standard_deviation: number | null;
  coefficient_of_variation: number | null;
  frequencies: StatisticsFrequency[];
  achievement_count: number | null;
  achievement_rate: number | null;
  warnings: string[];
}

export type ConfigurationScope = "global" | "competition" | "match";
export type ConfigurationValue = string | number;

export interface ConfigurationParameter {
  code: string;
  allowed_values: ConfigurationValue[];
}

export interface ProbabilityBand {
  code: string;
  lower_exclusive?: number;
  lower_inclusive?: number;
  upper_exclusive?: number;
  upper_inclusive?: number;
}

export interface ConfigurationCatalogPayload {
  catalog_id: string;
  schema_version: number;
  statistical_parameters: ConfigurationParameter[];
  statistical_lines: {
    handicap_line_quarters: number[];
    total_line_quarters: number[];
  };
  probability_bands: ProbabilityBand[];
}

export interface ConfigurationCatalog {
  catalog_id: string;
  schema_version: number;
  payload: ConfigurationCatalogPayload;
  content_hash: string;
  created_at: string;
}

export interface ConfigurationRevisionDraft {
  catalog_id: string;
  scope: ConfigurationScope;
  parameter_code: string;
  value: ConfigurationValue;
  competition_id?: number | null;
  match_id?: number | null;
  actor: string;
  reason: string;
}

export interface ConfigurationRevision extends Required<Omit<ConfigurationRevisionDraft, "competition_id" | "match_id">> {
  revision_id: number;
  catalog_hash: string;
  competition_id: number | null;
  match_id: number | null;
  replaces_revision_id: number | null;
  revision_hash: string;
  created_at: string;
}

export interface EffectiveConfiguration {
  match_id: number;
  competition_id: number;
  catalog_id: string;
  catalog_hash: string;
  values: Record<string, ConfigurationValue>;
  selected_revisions: ConfigurationRevision[];
  discarded_revisions: ConfigurationRevision[];
  effective_hash: string;
}

export type AnalysisStatus = "draft" | "calculated" | "approved";
export type AnalysisEventType = "calculated" | "reviewed" | "approved";

/** Immutable audit event returned by the APP-015 workflow API. */
export interface AnalysisEvent {
  event_id: number;
  event_type: AnalysisEventType;
  execution_id: string | null;
  actor: string | null;
  reason: string | null;
  created_at: string;
}

export interface Analysis {
  analysis_id: string;
  match_id: number;
  status: AnalysisStatus;
  created_at: string;
  events: AnalysisEvent[];
}

export interface AnalysisHistory {
  analyses: Analysis[];
}

export interface WorkflowDecisionDraft {
  actor: string;
  reason: string;
}

/** The payload is frozen by the API and intentionally remains opaque to the UI. */
export interface AnalysisSnapshot {
  snapshot_id: string;
  analysis_id: string;
  payload: Record<string, unknown>;
  snapshot_hash: string;
  created_at: string;
}

export interface AnalysisApproval {
  analysis: Analysis;
  snapshot: AnalysisSnapshot;
}
