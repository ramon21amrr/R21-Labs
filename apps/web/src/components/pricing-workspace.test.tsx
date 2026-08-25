import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createPricingExecution, getMatch, getMethodOneSample, getPricingExecution, listMarketPricings, listPricingExecutions } from "@/lib/api";
import { PricingWorkspace } from "@/components/pricing-workspace";

vi.mock("next/link", () => ({ default: ({ children, ...props }: React.ComponentProps<"a">) => <a {...props}>{children}</a> }));
vi.mock("@/lib/api", async (importOriginal) => ({ ...(await importOriginal<typeof import("@/lib/api")>()), createPricingExecution: vi.fn(), getMatch: vi.fn(), getMethodOneSample: vi.fn(), getPricingExecution: vi.fn(), listMarketPricings: vi.fn(), listPricingExecutions: vi.fn() }));

const ref = (id: number, display_name: string) => ({ id, display_name, created_at: "2026-01-01T00:00:00Z" });
const match = { id: 11, played_on: "2026-08-01", competition: ref(1, "Liga"), season: { id: 2, label: "2026", competition: ref(1, "Liga"), created_at: "2026-01-01T00:00:00Z" }, home_team: ref(3, "Casa"), away_team: ref(4, "Fora"), has_statistics: true, created_at: "2026-01-01T00:00:00Z" };
const completeSample = { target_match: match, parameters: { requested_count: 10, competition_id: 1, season_id: 2, include_previous_season: false, ordering: "played_on DESC", statistic_periods: ["goals_regulation_time"] }, home_sample: { venue_condition: "home", expected_count: 10, found_count: 10, complete: true, insufficient_reason: null, matches: [] }, away_sample: { venue_condition: "away", expected_count: 10, found_count: 10, complete: true, insufficient_reason: null, matches: [] }, warnings: ["warning_public"] };
const execution = { execution_id: "00000000-0000-4000-8000-000000000001", match_id: 11, status: "completed" as const, created_at: "2026-08-01T00:00:00Z", finalized_at: "2026-08-01T00:01:00Z", correlation_id: "support-1", sample_fingerprint: "a".repeat(64), input_fingerprint: "b".repeat(64), result_fingerprint: "c".repeat(64), pricing_engine_version: "1.0.1", distribution_version: "1.1.1", method_one_version: "1.0.0", schema_version: 1, public_parameters: { requested_count: 10 }, canonical_input: {}, canonical_result: { expected_rates: { home: 1.25 }, fair_odds: { home_win: 2.1 } }, failure_code: null };

describe("PricingWorkspace", () => {
  beforeEach(() => {
    vi.stubGlobal("crypto", { randomUUID: () => "retry-key" });
    vi.mocked(getMatch).mockResolvedValue(match);
    vi.mocked(getMethodOneSample).mockResolvedValue(completeSample);
    vi.mocked(listPricingExecutions).mockResolvedValue({ items: [execution], page: 1, page_size: 25, total: 1 });
    vi.mocked(listMarketPricings).mockResolvedValue({ items: [], page: 1, page_size: 25, total: 0 });
  });
  afterEach(() => vi.restoreAllMocks());

  it("shows complete samples, warnings and a canonical successful execution", async () => {
    vi.mocked(createPricingExecution).mockResolvedValue(execution);
    render(<PricingWorkspace matchId={11} />);
    expect(await screen.findByText("Amostras completas")).toBeTruthy();
    expect(screen.getByText("warning_public")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Executar precificação" }));
    await waitFor(() => expect(createPricingExecution).toHaveBeenCalledWith(11, "retry-key"));
    expect(await screen.findByText("Resultado canônico")).toBeTruthy();
    expect(screen.getByText("expected_rates")).toBeTruthy();
  });

  it("presents a blocked execution and opens a persisted record", async () => {
    const blocked = { ...execution, status: "blocked_sample_incomplete" as const, canonical_result: null, failure_code: "method_one_sample_incomplete" };
    vi.mocked(getMethodOneSample).mockResolvedValue({ ...completeSample, home_sample: { ...completeSample.home_sample, found_count: 8, complete: false, insufficient_reason: "insufficient_eligible_matches" } });
    vi.mocked(createPricingExecution).mockResolvedValue(blocked);
    vi.mocked(getPricingExecution).mockResolvedValue(execution);
    render(<PricingWorkspace matchId={11} />);
    expect(await screen.findByText("Amostras incompletas")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Executar precificação" }));
    expect(await screen.findByText("Esta execução não produziu resultado canônico.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Abrir" }));
    await waitFor(() => expect(getPricingExecution).toHaveBeenCalledWith(execution.execution_id));
  });

  it("does not expose a technical error from the API", async () => {
    vi.mocked(createPricingExecution).mockRejectedValue(new Error("stack trace"));
    render(<PricingWorkspace matchId={11} />);
    await screen.findByRole("heading", { name: "Executar Método 1" });
    fireEvent.click(screen.getByRole("button", { name: "Executar precificação" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Não foi possível executar o Método 1.");
  });
});
