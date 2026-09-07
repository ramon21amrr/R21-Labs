import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getMatch, getStatisticsSample } from "@/lib/api";
import { StatisticsWorkspace } from "@/components/statistics-workspace";

vi.mock("@/lib/api", async (importOriginal) => ({ ...(await importOriginal<typeof import("@/lib/api")>()), getMatch: vi.fn(), getStatisticsSample: vi.fn() }));

const ref = (id: number, display_name: string) => ({ id, display_name, created_at: "2026-01-01T00:00:00Z" });
const match = { id: 11, played_on: "2026-08-01", competition: ref(1, "Liga"), season: { id: 2, label: "2026", competition: ref(1, "Liga"), created_at: "2026-01-01T00:00:00Z" }, home_team: ref(3, "Casa"), away_team: ref(4, "Fora"), has_statistics: true, created_at: "2026-01-01T00:00:00Z" };
const sample = {
  target_match: { match_id: 11, played_on: "2026-08-01", competition_id: 1, competition_name: "Liga", season_id: 2, season_label: "2026", home_team_id: 3, home_team_name: "Casa", away_team_id: 4, away_team_name: "Fora" },
  filters: { team_id: 3, sample_size: 10 as const, venue: "overall" as const, competition_scope: "target_competition" as const, season_scope: "current" as const, metric: "goals_scored" as const },
  ordering: "played_on DESC, match_id DESC",
  candidate_count: 2,
  used_count: 2,
  candidate_match_ids: [10, 9],
  used_match_ids: [10, 9],
  candidates: [{ match_id: 10, played_on: "2026-07-01", competition_id: 1, competition_name: "Liga", season_id: 2, season_label: "2026", home_team_id: 3, home_team_name: "Casa", away_team_id: 4, away_team_name: "Fora", venue: "home" as const, value: 0, unavailable_reason: null }, { match_id: 9, played_on: "2026-06-01", competition_id: 1, competition_name: "Liga", season_id: 2, season_label: "2026", home_team_id: 5, home_team_name: "Outra", away_team_id: 3, away_team_name: "Casa", venue: "away" as const, value: null, unavailable_reason: "missing" }],
  used_matches: [],
  valid_values: [0],
  unavailable_values: [{ match_id: 9, reason: "missing" }],
  available_count: 1,
  mean: 0,
  standard_deviation: 0,
  coefficient_of_variation: null,
  frequencies: [{ value: 0, count: 1 }],
  achievement_count: null,
  achievement_rate: null,
  warnings: ["amostra_parcial"]
};

describe("StatisticsWorkspace", () => {
  beforeEach(() => {
    vi.mocked(getMatch).mockResolvedValue(match);
    vi.mocked(getStatisticsSample).mockResolvedValue(sample);
  });
  afterEach(() => vi.restoreAllMocks());

  it("sends only the configured public request and renders API statistics, including valid zero", async () => {
    render(<StatisticsWorkspace matchId={11} />);
    await screen.findByRole("button", { name: "Consultar amostra" });
    fireEvent.click(screen.getByRole("button", { name: "Consultar amostra" }));
    await waitFor(() => expect(getStatisticsSample).toHaveBeenCalledWith(11, {
      team_id: 3,
      sample_size: 10,
      venue: "overall",
      competition_scope: "target_competition",
      season_scope: "current",
      metric: "goals_scored"
    }));
    expect(await screen.findByRole("heading", { name: "Resultado da amostra" })).toBeTruthy();
    expect(screen.getAllByText("0").length).toBeGreaterThan(0);
    expect(screen.getByText("Indisponível")).toBeTruthy();
    expect(screen.getByText("ID 10 · ID 9")).toBeTruthy();
    expect(screen.getByText("amostra_parcial")).toBeTruthy();
  });

  it("includes the explicitly selected previous season and achievement parameters", async () => {
    render(<StatisticsWorkspace matchId={11} />);
    await screen.findByRole("button", { name: "Consultar amostra" });
    fireEvent.change(screen.getByLabelText("Temporada"), { target: { value: "current_and_previous" } });
    fireEvent.change(screen.getByLabelText("ID da temporada anterior"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Comparador de atingimento"), { target: { value: "at_least" } });
    fireEvent.change(screen.getByLabelText("Valor do atingimento"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Consultar amostra" }));
    await waitFor(() => expect(getStatisticsSample).toHaveBeenCalledWith(11, expect.objectContaining({
      previous_season_id: 1,
      comparator: "at_least",
      achievement_target: 2
    })));
  });
});
