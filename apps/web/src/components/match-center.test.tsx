import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getMatch, getMethodThreeResult, getMethodTwoResult } from "@/lib/api";
import { MatchCenter } from "@/components/match-center";

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  getMatch: vi.fn(),
  getMethodThreeResult: vi.fn(),
  getMethodTwoResult: vi.fn()
}));
vi.mock("@/components/pricing-workspace", () => ({ PricingWorkspace: () => <p>Precificação carregada</p> }));
vi.mock("@/components/statistics-workspace", () => ({ StatisticsWorkspace: () => <p>Estatísticas carregadas</p> }));
vi.mock("@/components/configuration-workspace", () => ({ EffectiveConfigurationPanel: () => <p>Configuração carregada</p> }));
vi.mock("@/components/analysis-workflow", () => ({ AnalysisWorkflow: () => <p>Workflow carregado</p> }));

const reference = (id: number, display_name: string) => ({ id, display_name, created_at: "2026-01-01T00:00:00Z" });
const match = { id: 11, played_on: "2026-08-01", competition: reference(1, "Liga"), season: { id: 2, label: "2026", competition: reference(1, "Liga"), created_at: "2026-01-01T00:00:00Z" }, home_team: reference(3, "Casa"), away_team: reference(4, "Fora"), has_statistics: true, created_at: "2026-01-01T00:00:00Z" };

describe("MatchCenter", () => {
  beforeEach(() => {
    vi.mocked(getMatch).mockResolvedValue(match);
    vi.mocked(getMethodTwoResult).mockResolvedValue({ method: "method_two_adjusted_poisson", method_version: "1.0.0", payload: { status: "completed", home_lambda: 1.2, away_lambda: 0.8 } });
    vi.mocked(getMethodThreeResult).mockResolvedValue({ method: "method_three_observed_frequency", method_version: "1.0.0", payload: { combined: { frequency: 0.5 }, warnings: [] } });
  });
  afterEach(() => vi.restoreAllMocks());

  it("keeps the match journey in accessible sections and obtains Method Two and Three from the API", async () => {
    render(<MatchCenter matchId={11} />);
    expect(await screen.findByRole("heading", { name: "Casa × Fora" })).toBeTruthy();
    const overview = screen.getByRole("tab", { name: "Visão geral" });
    expect(overview.getAttribute("aria-selected")).toBe("true");
    fireEvent.keyDown(overview, { key: "ArrowRight" });
    expect(await screen.findByText("Precificação carregada")).toBeTruthy();
    fireEvent.click(overview);
    fireEvent.change(screen.getByLabelText("Amostra para os métodos"), { target: { value: "10" } });
    fireEvent.change(screen.getByLabelText("Temporada para os métodos"), { target: { value: "current" } });
    fireEvent.change(screen.getByLabelText("Métrica para os métodos"), { target: { value: "goals_scored" } });
    fireEvent.change(screen.getByLabelText("Contexto do Método 2"), { target: { value: "venue" } });
    fireEvent.change(screen.getByLabelText("Escopo de competição do Método 3"), { target: { value: "target_competition" } });
    fireEvent.change(screen.getByLabelText("Comparador do Método 3"), { target: { value: "at_least" } });
    fireEvent.change(screen.getByLabelText("Valor do Método 3"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Consultar Métodos 2 e 3" }));
    await waitFor(() => expect(getMethodTwoResult).toHaveBeenCalledWith(11, { sample_size: 10, context: "venue", season_scope: "current", metric: "goals_scored" }));
    await waitFor(() => expect(getMethodThreeResult).toHaveBeenCalledWith(11, { sample_size: 10, competition_scope: "target_competition", season_scope: "current", metric: "goals_scored", comparator: "at_least", achievement_target: 1 }));
    expect(await screen.findByText("Método 2 · Poisson ajustado")).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", { name: "Análise e snapshot" }));
    expect(await screen.findByText("Workflow carregado")).toBeTruthy();
  });

  it("shows a local validation state rather than inventing selectors", async () => {
    render(<MatchCenter matchId={11} />);
    await screen.findByRole("heading", { name: "Casa × Fora" });
    fireEvent.click(screen.getByRole("button", { name: "Consultar Métodos 2 e 3" }));
    expect((await screen.findByRole("alert")).textContent).toContain("não inventa configuração");
    expect(getMethodTwoResult).not.toHaveBeenCalled();
  });
});
