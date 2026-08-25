import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createMarketReference, getMarketReferenceComparison, listMarketPricings, listMarketReferences } from "@/lib/api";
import { MarketReferencePanel } from "@/components/market-reference-panel";

vi.mock("@/lib/api", async (importOriginal) => ({ ...(await importOriginal<typeof import("@/lib/api")>()), createMarketReference: vi.fn(), getMarketReferenceComparison: vi.fn(), listMarketPricings: vi.fn(), listMarketReferences: vi.fn() }));

const snapshot = { market_pricing_id: "00000000-0000-4000-8000-000000000001", match_id: 11, created_at: "2026-08-01T00:00:00Z", finalized_at: "2026-08-01T00:01:00Z", correlation_id: "snapshot", pricing_engine_version: "1.0.1", canonical_input: {}, canonical_result: {} };
const observation = { observation_id: "00000000-0000-4000-8000-000000000002", match_id: 11, market_pricing_id: snapshot.market_pricing_id, market_code: "asian_handicap", selection: "home", model_line_quarters: -1, reference_line_quarters: 0, reference_value: 2.05, observed_at: "2026-08-01T12:00:00Z", created_at: "2026-08-01T12:00:01Z", correlation_id: "reference" };

describe("MarketReferencePanel", () => {
  beforeEach(() => {
    vi.stubGlobal("crypto", { randomUUID: () => "reference-retry" });
    vi.mocked(listMarketReferences).mockResolvedValue({ items: [], page: 1, page_size: 25, total: 0 });
  });
  afterEach(() => vi.restoreAllMocks());

  it("shows a loading then empty state when no ENG-006 snapshot exists", async () => {
    vi.mocked(listMarketPricings).mockResolvedValue({ items: [], page: 1, page_size: 25, total: 0 });
    render(<MarketReferencePanel matchId={11} />);
    expect(screen.getByRole("status").textContent).toContain("Carregando snapshots");
    expect(await screen.findByText("Ainda não há snapshot ENG-006 persistido para esta partida.")).toBeTruthy();
  });

  it("registers and displays a comparison supplied by the API", async () => {
    vi.mocked(listMarketPricings).mockResolvedValue({ items: [snapshot], page: 1, page_size: 25, total: 1 });
    vi.mocked(createMarketReference).mockResolvedValue(observation);
    vi.mocked(getMarketReferenceComparison).mockResolvedValue({ observation, model_value: 2, line_difference_quarters: 1 });
    render(<MarketReferencePanel matchId={11} />);
    await screen.findByRole("button", { name: "Registrar referência" });
    fireEvent.change(screen.getByLabelText("Linha teórica (quartos)"), { target: { value: "-1" } });
    fireEvent.change(screen.getByLabelText("Linha de referência (quartos)"), { target: { value: "0" } });
    fireEvent.change(screen.getByLabelText("Observada em"), { target: { value: "2026-08-01T12:00" } });
    fireEvent.click(screen.getByRole("button", { name: "Registrar referência" }));
    await waitFor(() => expect(createMarketReference).toHaveBeenCalled());
    expect(await screen.findByText("Diferença (passos de 0,25)")).toBeTruthy();
    expect(screen.getByText("1")).toBeTruthy();
  });
});
