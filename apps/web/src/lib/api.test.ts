import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, createConfigurationRevision, getConfigurationCatalog, listMatches } from "@/lib/api";

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

  it("uses the versioned configuration catalog and additive revision contract", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({}), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({}), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await getConfigurationCatalog();
    await createConfigurationRevision({ catalog_id: "lvfi-mvp@1.0.0", scope: "global", parameter_code: "sample_size", value: 10, reason: "teste" });
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/configuration-catalogs/lvfi-mvp/1.0.0", expect.objectContaining({ headers: { Accept: "application/json" } }));
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/administration/configuration-revisions", expect.objectContaining({ method: "POST", body: JSON.stringify({ catalog_id: "lvfi-mvp@1.0.0", scope: "global", parameter_code: "sample_size", value: 10, reason: "teste" }) }));
  });
});
