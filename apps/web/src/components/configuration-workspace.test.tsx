import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createConfigurationRevision, getConfigurationCatalog, getEffectiveConfiguration } from "@/lib/api";
import { ConfigurationCatalogWorkspace, EffectiveConfigurationPanel } from "@/components/configuration-workspace";

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  createConfigurationRevision: vi.fn(),
  getConfigurationCatalog: vi.fn(),
  getEffectiveConfiguration: vi.fn()
}));

const catalog = {
  catalog_id: "lvfi-mvp@1.0.0",
  schema_version: 1,
  content_hash: "catalog-hash",
  created_at: "2026-09-10T00:00:00Z",
  payload: {
    catalog_id: "lvfi-mvp@1.0.0",
    schema_version: 1,
    statistical_parameters: [{ code: "sample_size", allowed_values: [5, 10, 15, 20] }, { code: "venue", allowed_values: ["home", "away", "overall"] }],
    statistical_lines: { handicap_line_quarters: [-1, 0, 1], total_line_quarters: [1, 2] },
    probability_bands: [{ code: "lt_0_4", upper_exclusive: 0.4 }]
  }
};

const revision = {
  revision_id: 9,
  catalog_id: "lvfi-mvp@1.0.0",
  catalog_hash: "catalog-hash",
  scope: "competition" as const,
  parameter_code: "venue",
  value: "away",
  competition_id: 3,
  match_id: null,
  actor: "admin",
  reason: "teste",
  replaces_revision_id: null,
  revision_hash: "revision-hash",
  created_at: "2026-09-10T00:00:00Z"
};

describe("Configuration workspaces", () => {
  beforeEach(() => {
    vi.mocked(getConfigurationCatalog).mockResolvedValue(catalog);
    vi.mocked(createConfigurationRevision).mockResolvedValue(revision);
    vi.mocked(getEffectiveConfiguration).mockResolvedValue({
      match_id: 11,
      competition_id: 3,
      catalog_id: "lvfi-mvp@1.0.0",
      catalog_hash: "catalog-hash",
      values: { sample_size: 10, venue: "away" },
      selected_revisions: [revision],
      discarded_revisions: [{ ...revision, revision_id: 8, scope: "global", competition_id: null, revision_hash: "global-hash" }],
      effective_hash: "effective-hash"
    });
  });
  afterEach(() => vi.restoreAllMocks());

  it("renders only catalog enumerations and submits the selected parameter revision", async () => {
    render(<ConfigurationCatalogWorkspace />);
    expect(await screen.findByRole("heading", { name: "Catálogo de configuração" })).toBeTruthy();
    expect(screen.getByText("catalog-hash")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Parâmetro de configuração"), { target: { value: "venue" } });
    fireEvent.change(screen.getByLabelText("Valor de configuração"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Escopo de configuração"), { target: { value: "competition" } });
    fireEvent.change(screen.getByLabelText("ID da competição"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("Autor"), { target: { value: "admin" } });
    fireEvent.change(screen.getByLabelText("Justificativa"), { target: { value: "teste" } });
    fireEvent.click(screen.getByRole("button", { name: "Registrar revisão" }));
    await waitFor(() => expect(createConfigurationRevision).toHaveBeenCalledWith({
      catalog_id: "lvfi-mvp@1.0.0",
      scope: "competition",
      parameter_code: "venue",
      value: "away",
      competition_id: 3,
      actor: "admin",
      reason: "teste"
    }));
  });

  it("renders the API-owned effective configuration and precedence evidence", async () => {
    render(<EffectiveConfigurationPanel matchId={11} />);
    expect(await screen.findByRole("heading", { name: "Configuração efetiva" })).toBeTruthy();
    expect(getEffectiveConfiguration).toHaveBeenCalledWith(11);
    expect(screen.getByText("effective-hash")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Revisões selecionadas" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Candidatas de menor precedência" })).toBeTruthy();
    expect(screen.getByText("global-hash")).toBeTruthy();
  });
});
