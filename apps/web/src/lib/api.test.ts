import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, listMatches } from "@/lib/api";

describe("public API client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("uses the same-origin API rewrite and public query parameters", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], page: 1, page_size: 10, total: 0 }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await listMatches({ team_id: 7, date_from: "2026-01-01", date_to: undefined });
    expect(fetchMock).toHaveBeenCalledWith("/api/matches?page=1&page_size=10&team_id=7&date_from=2026-01-01", expect.objectContaining({ headers: { Accept: "application/json" } }));
  });

  it("maps an API failure to a sanitized message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("internal detail", { status: 500 })));
    await expect(listMatches({})).rejects.toEqual(new ApiError(500, "O serviço não pôde concluir a operação. Tente novamente mais tarde."));
  });
});
