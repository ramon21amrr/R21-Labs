"use client";

import { useEffect, useState } from "react";

import { ApiError, getMatch, getStatisticsSample } from "@/lib/api";
import type { Match, StatisticsAchievementComparator, StatisticsCompetitionScope, StatisticsMetric, StatisticsSample, StatisticsSampleRequest, StatisticsSampleSize, StatisticsSeasonScope, StatisticsVenue } from "@/lib/contracts";

type Draft = {
  team_id: number | null;
  sample_size: StatisticsSampleSize;
  venue: StatisticsVenue;
  competition_scope: StatisticsCompetitionScope;
  season_scope: StatisticsSeasonScope;
  previous_season_id: string;
  metric: StatisticsMetric;
  achievement_comparator: "" | StatisticsAchievementComparator;
  achievement_target: string;
};

const initialDraft: Draft = {
  team_id: null,
  sample_size: 10,
  venue: "overall",
  competition_scope: "target_competition",
  season_scope: "current",
  previous_season_id: "",
  metric: "goals",
  achievement_comparator: "",
  achievement_target: ""
};

function formatValue(value: number | null): string {
  return value === null ? "Indisponível" : String(value);
}

function asRequest(draft: Draft): StatisticsSampleRequest | null {
  if (draft.team_id === null) return null;
  const previousSeason = Number(draft.previous_season_id);
  const achievementTarget = Number(draft.achievement_target);
  return {
    team_id: draft.team_id,
    sample_size: draft.sample_size,
    venue: draft.venue,
    competition_scope: draft.competition_scope,
    season_scope: draft.season_scope,
    ...(draft.season_scope === "current_and_previous" && Number.isSafeInteger(previousSeason) && previousSeason > 0 ? { previous_season_id: previousSeason } : {}),
    metric: draft.metric,
    ...(draft.achievement_comparator && Number.isFinite(achievementTarget) ? { achievement_comparator: draft.achievement_comparator, achievement_target: achievementTarget } : {})
  };
}

function SampleResults({ sample }: { sample: StatisticsSample }) {
  const { configuration, summary } = sample;
  return <section className="panel" aria-labelledby="statistics-result-title">
    <div className="section-heading"><div><p className="eyebrow">Resposta pública da API</p><h2 id="statistics-result-title">Resultado da amostra</h2></div></div>
    <p className="hint">Os indicadores abaixo são fornecidos pela API; esta interface não recalcula estatísticas.</p>
    <dl className="metadata">
      <dt>Filtros aplicados</dt><dd>Time {sample.team_id} · {configuration.venue} · {configuration.sample_size} jogos · {configuration.competition_scope} · {configuration.season_scope} · {configuration.metric}</dd>
      <dt>Temporada atual</dt><dd>{configuration.current_season_label}</dd>
      {configuration.previous_season_label && <><dt>Temporada anterior</dt><dd>{configuration.previous_season_label}</dd></>}
      <dt>Ordenação</dt><dd>{configuration.ordering}</dd>
      <dt>Partidas candidatas</dt><dd>{sample.candidate_count}</dd>
      <dt>Partidas efetivamente usadas</dt><dd>{sample.used_count}</dd>
      <dt>Valores disponíveis</dt><dd>{summary.available_count}</dd>
      <dt>Média</dt><dd>{formatValue(summary.mean)}</dd>
      <dt>Desvio-padrão</dt><dd>{formatValue(summary.standard_deviation)}</dd>
      <dt>Coeficiente de variação</dt><dd>{formatValue(summary.coefficient_of_variation)}</dd>
    </dl>
    <section aria-labelledby="statistics-ids-title"><h3 id="statistics-ids-title">Partidas usadas</h3><p>{sample.used_match_ids.length === 0 ? "Nenhuma partida foi usada." : sample.used_match_ids.map((id) => `ID ${id}`).join(" · ")}</p></section>
    <section aria-labelledby="statistics-frequencies-title"><h3 id="statistics-frequencies-title">Frequências</h3>{summary.frequencies.length === 0 ? <p className="empty">Não há frequências para os valores disponíveis.</p> : <div className="table-wrap"><table><caption className="sr-only">Frequências fornecidas pela amostra estatística</caption><thead><tr><th>Valor</th><th>Atingimentos</th><th>Frequência</th></tr></thead><tbody>{summary.frequencies.map((frequency) => <tr key={frequency.value}><td>{frequency.value}</td><td>{frequency.count}</td><td>{formatValue(frequency.rate)}</td></tr>)}</tbody></table></div>}{summary.achievement && <p>Atingimento configurado: {summary.achievement.comparator} {summary.achievement.target} · {summary.achievement.count} · {formatValue(summary.achievement.rate)}</p>}</section>
    <section aria-labelledby="statistics-candidates-title"><h3 id="statistics-candidates-title">Partidas consideradas</h3>{sample.candidates.length === 0 ? <p className="empty">Nenhuma partida elegível foi encontrada antes da partida analisada.</p> : <div className="table-wrap"><table><caption className="sr-only">Partidas candidatas e disponibilidade dos valores</caption><thead><tr><th>ID</th><th>Data</th><th>Condição</th><th>Valor</th><th>Disponibilidade</th></tr></thead><tbody>{sample.candidates.map((candidate) => <tr key={candidate.match_id}><td>{candidate.match_id}</td><td>{candidate.played_on}</td><td>{candidate.venue}</td><td>{formatValue(candidate.value)}</td><td>{candidate.availability}</td></tr>)}</tbody></table></div>}</section>
    {sample.unavailable_values.length > 0 && <p className="warning">Valores indisponíveis: {sample.unavailable_values.map(({ match_id, availability }) => `ID ${match_id} (${availability})`).join(" · ")}</p>}
    {sample.warnings.length > 0 && <aside className="warnings" aria-label="Avisos e completude da amostra"><h3>Avisos e completude</h3><ul>{sample.warnings.map((warning, index) => <li key={`${warning}-${index}`}>{warning}</li>)}</ul></aside>}
  </section>;
}

export function StatisticsWorkspace({ matchId }: { matchId: number }) {
  const [match, setMatch] = useState<Match | null>(null);
  const [draft, setDraft] = useState<Draft>(initialDraft);
  const [sample, setSample] = useState<StatisticsSample | null>(null);
  const [loadingMatch, setLoadingMatch] = useState(true);
  const [loadingSample, setLoadingSample] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const invalidMatchId = !Number.isSafeInteger(matchId) || matchId < 1;

  useEffect(() => {
    if (invalidMatchId) return;
    let active = true;
    void getMatch(matchId)
      .then((loadedMatch) => {
        if (!active) return;
        setMatch(loadedMatch);
        setDraft((current) => current.team_id === null ? { ...current, team_id: loadedMatch.home_team.id } : current);
        setError(null);
      })
      .catch((reason: unknown) => { if (active) setError(reason instanceof ApiError ? reason.message : "Não foi possível carregar a partida."); })
      .finally(() => { if (active) setLoadingMatch(false); });
    return () => { active = false; };
  }, [invalidMatchId, matchId]);

  function update<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  async function loadSample(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const request = asRequest(draft);
    if (!request) return;
    setLoadingSample(true); setError(null);
    try {
      setSample(await getStatisticsSample(matchId, request));
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Não foi possível carregar a amostra estatística.");
    } finally { setLoadingSample(false); }
  }

  return <section className="shell statistics-shell" aria-labelledby="statistics-title">
    <div className="panel"><div className="section-heading"><div><p className="eyebrow">Camada estatística reutilizável</p><h2 id="statistics-title">Amostra estatística</h2></div></div>
      {invalidMatchId && <p className="status error" role="alert">Identificador de partida inválido.</p>}
      {!invalidMatchId && loadingMatch && <p className="status" role="status">Carregando configuração da partida…</p>}
      {!invalidMatchId && error && <p className="status error" role="alert">{error}</p>}
      {!invalidMatchId && !loadingMatch && match && <form onSubmit={(event) => void loadSample(event)}>
        <div className="filters">
          <label>Time<select aria-label="Time" value={draft.team_id ?? ""} onChange={(event) => update("team_id", Number(event.target.value))}><option value={match.home_team.id}>{match.home_team.display_name} (casa)</option><option value={match.away_team.id}>{match.away_team.display_name} (fora)</option></select></label>
          <label>Tamanho<select aria-label="Tamanho" value={draft.sample_size} onChange={(event) => update("sample_size", Number(event.target.value) as StatisticsSampleSize)}>{([5, 10, 15, 20] as const).map((size) => <option key={size} value={size}>{size} jogos</option>)}</select></label>
          <label>Condição<select aria-label="Condição" value={draft.venue} onChange={(event) => update("venue", event.target.value as StatisticsVenue)}><option value="overall">Geral</option><option value="home">Casa</option><option value="away">Fora</option></select></label>
          <label>Competição<select aria-label="Competição" value={draft.competition_scope} onChange={(event) => update("competition_scope", event.target.value as StatisticsCompetitionScope)}><option value="target_competition">Competição da partida</option><option value="all_eligible">Todos os jogos elegíveis</option></select></label>
          <label>Temporada<select aria-label="Temporada" value={draft.season_scope} onChange={(event) => update("season_scope", event.target.value as StatisticsSeasonScope)}><option value="current">Temporada atual</option><option value="current_and_previous">Atual e anterior</option></select></label>
          {draft.season_scope === "current_and_previous" && <label>ID da temporada anterior<input aria-label="ID da temporada anterior" inputMode="numeric" min="1" required value={draft.previous_season_id} onChange={(event) => update("previous_season_id", event.target.value)} /></label>}
          <label>Métrica<select aria-label="Métrica" value={draft.metric} onChange={(event) => update("metric", event.target.value as StatisticsMetric)}><option value="goals">Gols</option><option value="corners">Escanteios</option><option value="shots_on_target">Chutes no gol</option><option value="shots">Finalizações</option><option value="cards">Cartões</option><option value="fouls">Faltas</option></select></label>
          <label>Atingimento<select aria-label="Comparador de atingimento" value={draft.achievement_comparator} onChange={(event) => update("achievement_comparator", event.target.value as Draft["achievement_comparator"])}><option value="">Não configurar</option><option value="gte">Maior ou igual</option><option value="gt">Maior que</option><option value="lte">Menor ou igual</option><option value="lt">Menor que</option><option value="eq">Igual</option></select></label>
          {draft.achievement_comparator && <label>Valor do atingimento<input aria-label="Valor do atingimento" type="number" required value={draft.achievement_target} onChange={(event) => update("achievement_target", event.target.value)} /></label>}
        </div>
        <button type="submit" disabled={loadingSample}>{loadingSample ? "Consultando…" : "Consultar amostra"}</button>
      </form>}
    </div>
    {sample && <SampleResults sample={sample} />}
  </section>;
}
