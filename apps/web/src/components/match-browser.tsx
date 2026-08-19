"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ApiError, listMatches } from "@/lib/api";
import type { Match, Page } from "@/lib/contracts";

type Filters = { team_id: string; date_from: string; date_to: string };

const initialFilters: Filters = { team_id: "", date_from: "", date_to: "" };

function matchLabel(match: Match): string {
  return `${match.home_team.display_name} × ${match.away_team.display_name}`;
}

export function MatchBrowser() {
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [appliedFilters, setAppliedFilters] = useState<Filters>(initialFilters);
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page<Match> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await listMatches({ ...appliedFilters, page }));
    } catch (reason) {
      setData(null);
      setError(reason instanceof ApiError ? reason.message : "Não foi possível carregar as partidas.");
    } finally {
      setLoading(false);
    }
  }, [appliedFilters, page]);

  useEffect(() => {
    let active = true;

    void listMatches({ ...appliedFilters, page })
      .then((result) => { if (active) { setData(result); setError(null); } })
      .catch((reason: unknown) => {
        if (active) {
          setData(null);
          setError(reason instanceof ApiError ? reason.message : "Não foi possível carregar as partidas.");
        }
      })
      .finally(() => { if (active) setLoading(false); });

    return () => { active = false; };
  }, [appliedFilters, page]);

  function changeFilter(name: keyof Filters, value: string) {
    setFilters((current) => ({ ...current, [name]: value }));
  }

  return <section aria-labelledby="match-list-title" className="panel">
    <div className="section-heading"><div><p className="eyebrow">Partidas históricas</p><h2 id="match-list-title">Encontre uma partida</h2></div><button className="secondary" type="button" onClick={() => void load()} disabled={loading}>Atualizar</button></div>
    <form className="filters" onSubmit={(event) => { event.preventDefault(); setLoading(true); setPage(1); setAppliedFilters(filters); }}>
      <label>Identificador público do time<input inputMode="numeric" value={filters.team_id} onChange={(event) => changeFilter("team_id", event.target.value)} placeholder="Ex.: 12" /></label>
      <label>Data inicial<input type="date" value={filters.date_from} onChange={(event) => changeFilter("date_from", event.target.value)} /></label>
      <label>Data final<input type="date" value={filters.date_to} onChange={(event) => changeFilter("date_to", event.target.value)} /></label>
      <button type="submit" disabled={loading}>Aplicar filtros</button>
      <button className="secondary" type="button" onClick={() => { setLoading(true); setFilters(initialFilters); setAppliedFilters(initialFilters); setPage(1); }}>Limpar</button>
    </form>
    {loading && <p className="status" role="status">Carregando partidas…</p>}
    {error && <p className="status error" role="alert">{error}</p>}
    {!loading && !error && data?.items.length === 0 && <p className="empty">Nenhuma partida encontrada para os filtros selecionados.</p>}
    {!loading && data && data.items.length > 0 && <div className="table-wrap"><table><caption className="sr-only">Partidas históricas disponíveis</caption><thead><tr><th>Data</th><th>Competição</th><th>Temporada</th><th>Partida</th><th>Dados</th><th><span className="sr-only">Abrir</span></th></tr></thead><tbody>{data.items.map((match) => <tr key={match.id}><td>{match.played_on}</td><td>{match.competition.display_name}</td><td>{match.season.label}</td><td>{matchLabel(match)}</td><td>{match.has_statistics ? "Com estatísticas" : "Sem estatísticas"}</td><td><Link className="button-link" href={`/matches/${match.id}`} aria-label={`Abrir ${matchLabel(match)}`}>Selecionar</Link></td></tr>)}</tbody></table></div>}
    {data && data.total > 0 && <nav className="pagination" aria-label="Paginação de partidas"><span>Página {data.page} de {Math.max(1, Math.ceil(data.total / data.page_size))} · {data.total} partidas</span><button type="button" className="secondary" disabled={loading || page === 1} onClick={() => { setLoading(true); setPage((current) => current - 1); }}>Anterior</button><button type="button" className="secondary" disabled={loading || page * data.page_size >= data.total} onClick={() => { setLoading(true); setPage((current) => current + 1); }}>Próxima</button></nav>}
  </section>;
}
