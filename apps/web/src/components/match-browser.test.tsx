import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { listMatches } from "@/lib/api";
import { MatchBrowser } from "@/components/match-browser";

vi.mock("next/link", () => ({ default: ({ children, ...props }: React.ComponentProps<"a">) => <a {...props}>{children}</a> }));
vi.mock("@/lib/api", async (importOriginal) => ({ ...(await importOriginal<typeof import("@/lib/api")>()), listMatches: vi.fn() }));

const match = { id: 11, played_on: "2026-08-01", competition: { id: 1, display_name: "Liga", created_at: "2026-01-01T00:00:00Z" }, season: { id: 2, label: "2026", competition: { id: 1, display_name: "Liga", created_at: "2026-01-01T00:00:00Z" }, created_at: "2026-01-01T00:00:00Z" }, home_team: { id: 3, display_name: "Casa", created_at: "2026-01-01T00:00:00Z" }, away_team: { id: 4, display_name: "Fora", created_at: "2026-01-01T00:00:00Z" }, has_statistics: true, created_at: "2026-01-01T00:00:00Z" };

describe("MatchBrowser", () => {
  afterEach(() => vi.clearAllMocks());

  it("lists, filters and paginates public matches", async () => {
    vi.mocked(listMatches).mockResolvedValueOnce({ items: [match], page: 1, page_size: 10, total: 11 }).mockResolvedValueOnce({ items: [match], page: 1, page_size: 10, total: 11 }).mockResolvedValueOnce({ items: [], page: 2, page_size: 10, total: 11 });
    render(<MatchBrowser />);
    expect(await screen.findByText("Casa × Fora")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Identificador público do time"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "Aplicar filtros" }));
    await waitFor(() => expect(listMatches).toHaveBeenLastCalledWith({ team_id: "3", date_from: "", date_to: "", page: 1 }));
    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    await waitFor(() => expect(listMatches).toHaveBeenLastCalledWith({ team_id: "3", date_from: "", date_to: "", page: 2 }));
    expect(await screen.findByText("Nenhuma partida encontrada para os filtros selecionados.")).toBeTruthy();
  });

  it("shows a sanitized failure", async () => {
    vi.mocked(listMatches).mockRejectedValueOnce(new Error("internal details"));
    render(<MatchBrowser />);
    expect((await screen.findByRole("alert")).textContent).toContain("Não foi possível carregar as partidas.");
  });
});
