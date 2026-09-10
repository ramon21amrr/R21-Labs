import type { ConfigurationCatalog, ConfigurationRevision, ConfigurationRevisionDraft, EffectiveConfiguration, FutureMatch, FutureMatchDraft, ImportPreview, MarketPricing, MarketReferenceObservation, Match, MethodOneSample, ModelReferenceComparison, Page, PricingExecution, StatisticRevision, StatisticRevisionDraft, StatisticsSample, StatisticsSampleRequest } from "@/lib/contracts";

const defaultApiUrl = "/api";

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
  }
}

function apiUrl(path: string, params?: URLSearchParams): string {
  const base = (process.env.NEXT_PUBLIC_LVFI_API_URL ?? defaultApiUrl).replace(/\/$/, "");
  return `${base}${path}${params && params.size > 0 ? `?${params.toString()}` : ""}`;
}

function sanitizedMessage(status: number): string {
  if (status === 404) return "O registro solicitado não foi encontrado.";
  if (status === 422) return "A operação foi bloqueada pelos dados ou parâmetros disponíveis.";
  if (status >= 500) return "O serviço não pôde concluir a operação. Tente novamente mais tarde.";
  return "Não foi possível concluir a solicitação.";
}

async function request<T>(path: string, init?: RequestInit, params?: URLSearchParams): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path, params), {
      ...init,
      headers: { Accept: "application/json", ...init?.headers }
    });
  } catch {
    throw new ApiError(0, "Não foi possível conectar à API do LVFI.");
  }
  if (!response.ok) throw new ApiError(response.status, sanitizedMessage(response.status));
  return response.json() as Promise<T>;
}

export function listMatches(filters: Record<string, string | number | undefined>): Promise<Page<Match>> {
  const params = new URLSearchParams({ page: String(filters.page ?? 1), page_size: "10" });
  for (const key of ["team_id", "competition_id", "season_id", "date_from", "date_to"] as const) {
    const value = filters[key];
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  return request<Page<Match>>("/matches", undefined, params);
}

export const getMatch = (matchId: number) => request<Match>(`/matches/${matchId}`);
export function getStatisticsSample(matchId: number, sample: StatisticsSampleRequest): Promise<StatisticsSample> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(sample)) {
    if (value !== undefined) params.set(key, String(value));
  }
  return request<StatisticsSample>(`/matches/${matchId}/statistics/sample`, undefined, params);
}
export const getMethodOneSample = (matchId: number) => request<MethodOneSample>(`/matches/${matchId}/method-one/sample`);
export const listPricingExecutions = (matchId: number) =>
  request<Page<PricingExecution>>(`/matches/${matchId}/method-one/pricing-executions`);
export const getPricingExecution = (executionId: string) => request<PricingExecution>(`/pricing-executions/${executionId}`);
export const createPricingExecution = (matchId: number, idempotencyKey: string) =>
  request<PricingExecution>(`/matches/${matchId}/method-one/pricing-executions`, {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey }
  });
export const listMarketPricings = (matchId: number) =>
  request<Page<MarketPricing>>(`/matches/${matchId}/market-pricings`);
export const listMarketReferences = (matchId: number, marketPricingId: string) =>
  request<Page<MarketReferenceObservation>>(
    `/matches/${matchId}/market-pricings/${marketPricingId}/market-references`
  );
export const createMarketReference = (
  matchId: number,
  payload: Omit<MarketReferenceObservation, "observation_id" | "match_id" | "created_at" | "correlation_id">,
  idempotencyKey: string
) =>
  request<MarketReferenceObservation>(`/matches/${matchId}/market-references`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(payload)
  });
export const getMarketReferenceComparison = (observationId: string) =>
  request<ModelReferenceComparison>(`/market-references/${observationId}/comparison`);

async function importRequest(path: string, file: File): Promise<ImportPreview> {
  const params = new URLSearchParams({ filename: file.name });
  let response: Response;
  try {
    response = await fetch(apiUrl(path, params), { method: "POST", headers: { Accept: "application/json", "Content-Type": file.type || "application/octet-stream" }, body: file });
  } catch {
    throw new ApiError(0, "Não foi possível conectar à API do LVFI.");
  }
  if (!response.ok) throw new ApiError(response.status, sanitizedMessage(response.status));
  return response.json() as Promise<ImportPreview>;
}

export const previewImport = (file: File) => importRequest("/administration/imports/preview", file);
export const confirmImport = (file: File) => importRequest("/administration/imports/confirm", file);
export const createFutureMatch = (payload: FutureMatchDraft) =>
  request<FutureMatch>("/administration/matches", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
export const createStatisticRevision = (matchId: number, payload: StatisticRevisionDraft) =>
  request<StatisticRevision>(`/administration/matches/${matchId}/statistic-revisions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });

export const getConfigurationCatalog = () =>
  request<ConfigurationCatalog>("/configuration-catalogs/lvfi-mvp/1.0.0");
export const createConfigurationRevision = (payload: ConfigurationRevisionDraft) =>
  request<ConfigurationRevision>("/administration/configuration-revisions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
export const getEffectiveConfiguration = (matchId: number) =>
  request<EffectiveConfiguration>(`/matches/${matchId}/configuration/effective`);
