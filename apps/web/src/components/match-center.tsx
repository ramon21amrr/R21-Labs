"use client";

import type { KeyboardEvent } from "react";
import { useEffect, useId, useState } from "react";

import { AnalysisWorkflow } from "@/components/analysis-workflow";
import { CanonicalValue } from "@/components/canonical-value";
import { EffectiveConfigurationPanel } from "@/components/configuration-workspace";
import { PricingWorkspace } from "@/components/pricing-workspace";
import { StatisticsWorkspace } from "@/components/statistics-workspace";
import { ApiError, getMatch, getMethodThreeResult, getMethodTwoResult } from "@/lib/api";
import type { Match, MethodResult, StatisticsMetric } from "@/lib/contracts";
import styles from "@/components/match-center.module.css";

type Tab = "overview" | "pricing" | "statistics" | "configuration" | "workflow" | "evidence";
type MethodDraft = {
  sampleSize: "" | "5" | "10" | "15" | "20";
  seasonScope: "" | "current" | "current_and_previous";
  previousSeasonId: string;
  metric: "" | StatisticsMetric;
  context: "" | "venue" | "overall";
  competitionScope: "" | "target_competition" | "all_eligible";
  comparator: "" | "at_least" | "at_most" | "equal";
  achievementTarget: string;
};

const initialDraft: MethodDraft = {
  sampleSize: "",
  seasonScope: "",
  previousSeasonId: "",
  metric: "",
  context: "",
  competitionScope: "",
  comparator: "",
  achievementTarget: ""
};

const tabs: Array<{ id: Tab; label: string }> = [
  { id: "overview", label: "Visão geral" },
  { id: "pricing", label: "Precificação" },
  { id: "statistics", label: "Estatísticas" },
  { id: "configuration", label: "Configuração" },
  { id: "workflow", label: "Análise e snapshot" },
  { id: "evidence", label: "Histórico e evidência" }
];

function failureMessage(reason: unknown): string {
  return reason instanceof ApiError ? reason.message : "Não foi possível consultar os resultados dos métodos.";
}

function value(payload: Record<string, unknown>, key: string): string {
  const item = payload[key];
  return item === null || item === undefined ? "Indisponível" : String(item);
}

function MethodResults({ matchId }: { matchId: number }) {
  const [draft, setDraft] = useState<MethodDraft>(initialDraft);
  const [two, setTwo] = useState<MethodResult | null>(null);
  const [three, setThree] = useState<MethodResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update<Key extends keyof MethodDraft>(key: Key, next: MethodDraft[Key]) {
    setDraft((current) => ({ ...current, [key]: next }));
  }

  async function loadResults() {
    const sampleSize = Number(draft.sampleSize);
    const previousSeasonId = Number(draft.previousSeasonId);
    const achievementTarget = Number(draft.achievementTarget);
    if (!sampleSize || !draft.seasonScope || !draft.metric || !draft.context || !draft.competitionScope || !draft.comparator || !Number.isInteger(achievementTarget) || achievementTarget < 0 || (draft.seasonScope === "current_and_previous" && (!Number.isSafeInteger(previousSeasonId) || previousSeasonId < 1))) {
      setError("Informe todos os seletores obrigatórios; a central não inventa configuração para os métodos.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const previous = draft.seasonScope === "current_and_previous" ? previousSeasonId : undefined;
      const [methodTwo, methodThree] = await Promise.all([
        getMethodTwoResult(matchId, {
          sample_size: sampleSize as 5 | 10 | 15 | 20,
          context: draft.context,
          season_scope: draft.seasonScope,
          previous_season_id: previous,
          metric: draft.metric as "goals_scored" | "corners" | "shots_on_target" | "shots" | "cards" | "fouls"
        }),
        getMethodThreeResult(matchId, {
          sample_size: sampleSize as 5 | 10 | 15 | 20,
          competition_scope: draft.competitionScope,
          season_scope: draft.seasonScope,
          previous_season_id: previous,
          metric: draft.metric,
          comparator: draft.comparator,
          achievement_target: achievementTarget
        })
      ]);
      setTwo(methodTwo);
      setThree(methodThree);
    } catch (reason) {
      setError(failureMessage(reason));
      setTwo(null);
      setThree(null);
    } finally {
      setLoading(false);
    }
  }

  return <section className="panel" aria-labelledby="method-results-title">
    <p className="eyebrow">Métodos separados · leitura da API</p><h2 id="method-results-title">Resultados dos Métodos 2 e 3</h2>
    <p className="hint">Os seletores são explícitos e a API executa os serviços versionados. A interface não calcula lambdas, frequências, hashes ou amostras.</p>
    <div className="filters">
      <label>Amostra<select className={styles.focusable} aria-label="Amostra para os métodos" value={draft.sampleSize} onChange={(event) => update("sampleSize", event.target.value as MethodDraft["sampleSize"])}><option value="">Selecione</option><option value="5">5 jogos</option><option value="10">10 jogos</option><option value="15">15 jogos</option><option value="20">20 jogos</option></select></label>
      <label>Temporada<select className={styles.focusable} aria-label="Temporada para os métodos" value={draft.seasonScope} onChange={(event) => update("seasonScope", event.target.value as MethodDraft["seasonScope"])}><option value="">Selecione</option><option value="current">Atual</option><option value="current_and_previous">Atual e anterior</option></select></label>
      {draft.seasonScope === "current_and_previous" && <label>ID da temporada anterior<input aria-label="ID da temporada anterior para os métodos" type="number" min="1" value={draft.previousSeasonId} onChange={(event) => update("previousSeasonId", event.target.value)} /></label>}
      <label>Métrica comum aos Métodos 2 e 3<select className={styles.focusable} aria-label="Métrica para os métodos" value={draft.metric} onChange={(event) => update("metric", event.target.value as MethodDraft["metric"])}><option value="">Selecione</option><option value="goals_scored">Gols marcados</option><option value="corners">Escanteios</option><option value="shots_on_target">Chutes no gol</option><option value="shots">Finalizações</option><option value="cards">Cartões</option><option value="fouls">Faltas</option></select></label>
      <label>Contexto do Método 2<select className={styles.focusable} aria-label="Contexto do Método 2" value={draft.context} onChange={(event) => update("context", event.target.value as MethodDraft["context"])}><option value="">Selecione</option><option value="venue">Mandante/visitante</option><option value="overall">Geral</option></select></label>
      <label>Competição do Método 3<select className={styles.focusable} aria-label="Escopo de competição do Método 3" value={draft.competitionScope} onChange={(event) => update("competitionScope", event.target.value as MethodDraft["competitionScope"])}><option value="">Selecione</option><option value="target_competition">Competição da partida</option><option value="all_eligible">Todas elegíveis</option></select></label>
      <label>Comparador do Método 3<select className={styles.focusable} aria-label="Comparador do Método 3" value={draft.comparator} onChange={(event) => update("comparator", event.target.value as MethodDraft["comparator"])}><option value="">Selecione</option><option value="at_least">Pelo menos</option><option value="at_most">No máximo</option><option value="equal">Igual a</option></select></label>
      <label>Valor do Método 3<input aria-label="Valor do Método 3" type="number" min="0" value={draft.achievementTarget} onChange={(event) => update("achievementTarget", event.target.value)} /></label>
      <div><button type="button" onClick={() => void loadResults()} disabled={loading}>{loading ? "Consultando…" : "Consultar Métodos 2 e 3"}</button></div>
    </div>
    {loading && <p className="status" role="status">Consultando resultados e evidências dos métodos…</p>}
    {error && <p className="status error" role="alert">{error}</p>}
    {!loading && !error && !two && !three && <p className="empty">Escolha os seletores para consultar os resultados auditáveis.</p>}
    <div className="sample-grid">
      {two && <article className="sample-card"><h3>Método 2 · Poisson ajustado</h3><dl><dt>Versão</dt><dd>{two.method_version}</dd><dt>Estado</dt><dd>{value(two.payload, "status")}</dd><dt>Lambda mandante</dt><dd>{value(two.payload, "home_lambda")}</dd><dt>Lambda visitante</dt><dd>{value(two.payload, "away_lambda")}</dd></dl><details><summary>Ver evidência recebida da API</summary><CanonicalValue value={two.payload} /></details></article>}
      {three && <article className="sample-card"><h3>Método 3 · Frequência observada</h3><dl><dt>Versão</dt><dd>{three.method_version}</dd><dt>Frequência combinada</dt><dd>{value((three.payload.combined as Record<string, unknown>) ?? {}, "frequency")}</dd><dt>Avisos</dt><dd>{Array.isArray(three.payload.warnings) ? three.payload.warnings.join(" · ") || "Nenhum" : "Indisponível"}</dd></dl><details><summary>Ver evidência recebida da API</summary><CanonicalValue value={three.payload} /></details></article>}
    </div>
  </section>;
}

function Overview({ match, matchId }: { match: Match; matchId: number }) {
  return <><section className="panel" aria-labelledby="overview-title"><p className="eyebrow">Partida selecionada · ID público {match.id}</p><h2 id="overview-title">{match.home_team.display_name} × {match.away_team.display_name}</h2><dl className="metadata"><dt>Competição</dt><dd>{match.competition.display_name}</dd><dt>Temporada</dt><dd>{match.season.label}</dd><dt>Data</dt><dd>{match.played_on}</dd><dt>Dados históricos</dt><dd>{match.has_statistics ? "Disponíveis" : "Indisponíveis"}</dd></dl><p className="hint">Use as abas para estatísticas, configuração, execução persistida do Método 1 e workflow/snapshot. Métodos não são fundidos automaticamente.</p></section><MethodResults matchId={matchId} /></>;
}

export function MatchCenter({ matchId }: { matchId: number }) {
  const [match, setMatch] = useState<Match | null>(null);
  const [active, setActive] = useState<Tab>("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const tabId = useId();
  const invalidMatchId = !Number.isSafeInteger(matchId) || matchId < 1;

  useEffect(() => {
    if (invalidMatchId) return;
    let current = true;
    void getMatch(matchId).then((value) => { if (current) { setMatch(value); setError(null); } }).catch((reason: unknown) => { if (current) setError(failureMessage(reason)); }).finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [invalidMatchId, matchId]);

  function moveTab(event: KeyboardEvent<HTMLButtonElement>, tab: Tab) {
    const index = tabs.findIndex((item) => item.id === tab);
    const nextIndex = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : event.key === "ArrowRight" ? (index + 1) % tabs.length : event.key === "ArrowLeft" ? (index - 1 + tabs.length) % tabs.length : null;
    if (nextIndex === null) return;
    event.preventDefault();
    const next = tabs[nextIndex];
    setActive(next.id);
    document.getElementById(`${tabId}-${next.id}`)?.focus();
  }

  return <main className="shell" aria-labelledby="match-center-title"><header className="app-header"><p className="eyebrow">Linha de Valor Football Intelligence</p><h1 id="match-center-title">Match Center</h1><p>Uma jornada auditável por partida, com dados e cálculos fornecidos exclusivamente pela API.</p></header>
    {invalidMatchId && <p className="status error" role="alert">Identificador de partida inválido.</p>}
    {!invalidMatchId && loading && <p className="status" role="status">Carregando contexto da partida…</p>}
    {!invalidMatchId && error && <p className="status error" role="alert">{error}</p>}
    {match && <><nav className={`tabs ${styles.tabs}`} aria-label="Seções da partida" role="tablist">{tabs.map((tab) => <button key={tab.id} id={`${tabId}-${tab.id}`} role="tab" type="button" tabIndex={active === tab.id ? 0 : -1} aria-selected={active === tab.id} aria-controls={`${tabId}-${tab.id}-panel`} className={active === tab.id ? "active" : "secondary"} onKeyDown={(event) => moveTab(event, tab.id)} onClick={() => setActive(tab.id)}>{tab.label}</button>)}</nav><section id={`${tabId}-${active}-panel`} role="tabpanel" aria-labelledby={`${tabId}-${active}`}>{active === "overview" && <Overview match={match} matchId={matchId} />}{active === "pricing" && <PricingWorkspace matchId={matchId} />}{active === "statistics" && <StatisticsWorkspace matchId={matchId} />}{active === "configuration" && <EffectiveConfigurationPanel matchId={matchId} />}{active === "workflow" && <AnalysisWorkflow matchId={matchId} />}{active === "evidence" && <section className="panel"><h2>Histórico e evidência</h2><p>As execuções persistidas do Método 1 ficam na aba Precificação. O histórico de revisão, aprovação e o snapshot aprovado permanecem na aba Análise e snapshot; ambos preservam seus contratos append-only.</p><p className="hint">A evidência estatística e dos Métodos 2/3 é exibida na Visão geral após consulta com seletores explícitos.</p></section>}</section></>}
  </main>;
}
