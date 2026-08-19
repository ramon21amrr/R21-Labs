"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError, createPricingExecution, getMatch, getMethodOneSample, getPricingExecution, listPricingExecutions } from "@/lib/api";
import type { Match, MethodOneSample, PricingExecution } from "@/lib/contracts";
import { CanonicalValue } from "@/components/canonical-value";

function executionStatus(status: PricingExecution["status"]): string {
  return ({ completed: "Concluída", blocked_sample_incomplete: "Bloqueada por amostra incompleta", technical_failure: "Falha técnica" })[status];
}

function SampleCard({ title, sample }: { title: string; sample: MethodOneSample["home_sample"] }) {
  return <article className="sample-card"><h3>{title}</h3><dl><dt>Condição</dt><dd>{sample.venue_condition}</dd><dt>Observações utilizadas</dt><dd>{sample.found_count} de {sample.expected_count}</dd><dt>Completude</dt><dd>{sample.complete ? "Completa" : "Incompleta"}</dd>{sample.insufficient_reason && <><dt>Bloqueio</dt><dd>{sample.insufficient_reason}</dd></>}</dl>{sample.matches.length > 0 && <details><summary>Ver partidas da amostra</summary><ul>{sample.matches.map(({ match }) => <li key={match.id}>{match.played_on} · {match.home_team.display_name} × {match.away_team.display_name} · ID {match.id}</li>)}</ul></details>}</article>;
}

function ExecutionDetails({ execution }: { execution: PricingExecution }) {
  return <section className="execution-details" aria-labelledby="execution-details-title"><div className="section-heading"><div><p className="eyebrow">Execução persistida</p><h2 id="execution-details-title">{executionStatus(execution.status)}</h2></div><span className={`badge ${execution.status}`}>{execution.status}</span></div><dl className="metadata"><dt>Execution ID</dt><dd><code>{execution.execution_id}</code></dd><dt>Finalizada em</dt><dd>{execution.finalized_at}</dd><dt>Correlation ID</dt><dd><code>{execution.correlation_id}</code></dd><dt>Pricing Engine</dt><dd>{execution.pricing_engine_version}</dd><dt>Distribuição</dt><dd>{execution.distribution_version}</dd><dt>Método 1</dt><dd>{execution.method_one_version}</dd><dt>Schema</dt><dd>{execution.schema_version}</dd><dt>Fingerprint da amostra</dt><dd><code>{execution.sample_fingerprint}</code></dd>{execution.input_fingerprint && <><dt>Fingerprint da entrada</dt><dd><code>{execution.input_fingerprint}</code></dd></>}{execution.result_fingerprint && <><dt>Fingerprint do resultado</dt><dd><code>{execution.result_fingerprint}</code></dd></>}{execution.failure_code && <><dt>Código sanitizado</dt><dd><code>{execution.failure_code}</code></dd></>}</dl>{execution.canonical_result ? <section aria-labelledby="canonical-result-title"><h3 id="canonical-result-title">Resultado canônico</h3><p className="hint">Valores recebidos da API, sem recálculo ou arredondamento no frontend.</p><CanonicalValue value={execution.canonical_result} /></section> : <p className="status warning">Esta execução não produziu resultado canônico.</p>}</section>;
}

export function PricingWorkspace({ matchId }: { matchId: number }) {
  const [match, setMatch] = useState<Match | null>(null);
  const [sample, setSample] = useState<MethodOneSample | null>(null);
  const [history, setHistory] = useState<PricingExecution[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<PricingExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const invalidMatchId = !Number.isSafeInteger(matchId) || matchId < 1;

  useEffect(() => {
    if (invalidMatchId) return;
    let active = true;

    void Promise.all([getMatch(matchId), getMethodOneSample(matchId), listPricingExecutions(matchId)])
      .then(([loadedMatch, loadedSample, loadedHistory]) => {
        if (active) {
          setMatch(loadedMatch);
          setSample(loadedSample);
          setHistory(loadedHistory.items);
          setError(null);
        }
      })
      .catch((reason: unknown) => { if (active) setError(reason instanceof ApiError ? reason.message : "Não foi possível carregar a partida."); })
      .finally(() => { if (active) setLoading(false); });

    return () => { active = false; };
  }, [invalidMatchId, matchId]);

  async function execute() {
    setRunning(true); setError(null);
    try {
      const execution = await createPricingExecution(matchId, crypto.randomUUID());
      setSelectedExecution(execution);
      setHistory((current) => [execution, ...current.filter((item) => item.execution_id !== execution.execution_id)]);
    } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Não foi possível executar o Método 1."); }
    finally { setRunning(false); }
  }

  async function openExecution(executionId: string) {
    setError(null);
    try { setSelectedExecution(await getPricingExecution(executionId)); }
    catch (reason) { setError(reason instanceof ApiError ? reason.message : "Não foi possível abrir a execução."); }
  }

  return <main className="shell"><Link className="back-link" href="/">← Partidas históricas</Link>{invalidMatchId && <p className="status error" role="alert">Identificador de partida inválido.</p>}{!invalidMatchId && loading && <p className="status" role="status">Carregando partida, amostras e execuções…</p>}{!invalidMatchId && error && <p className="status error" role="alert">{error}</p>}{!invalidMatchId && !loading && match && <><header className="app-header"><p className="eyebrow">Partida selecionada · ID público {match.id}</p><h1>{match.home_team.display_name} × {match.away_team.display_name}</h1><dl className="match-identity"><div><dt>Competição</dt><dd>{match.competition.display_name}</dd></div><div><dt>Temporada</dt><dd>{match.season.label}</dd></div><div><dt>Data</dt><dd>{match.played_on}</dd></div></dl></header>{sample && <section className="panel" aria-labelledby="sample-title"><div className="section-heading"><div><p className="eyebrow">Método 1</p><h2 id="sample-title">Amostras históricas</h2></div><span className={`badge ${sample.home_sample.complete && sample.away_sample.complete ? "completed" : "blocked_sample_incomplete"}`}>{sample.home_sample.complete && sample.away_sample.complete ? "Amostras completas" : "Amostras incompletas"}</span></div><p className="hint">Qualidade e bloqueios são informados pelo contrato público da API; esta interface não os recalcula.</p><div className="sample-grid"><SampleCard title={`${match.home_team.display_name} em casa`} sample={sample.home_sample} /><SampleCard title={`${match.away_team.display_name} fora`} sample={sample.away_sample} /></div>{sample.warnings.length > 0 && <aside className="warnings" aria-label="Avisos da amostra"><h3>Avisos</h3><ul>{sample.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></aside>}</section>}<section className="panel" aria-labelledby="run-title"><div className="section-heading"><div><p className="eyebrow">Fluxo auditável</p><h2 id="run-title">Executar Método 1</h2></div><button type="button" onClick={() => void execute()} disabled={running}>{running ? "Executando…" : "Executar precificação"}</button></div><p className="hint">A operação usa a execução persistida pública da API. Uma amostra incompleta pode gerar um registro bloqueado, sem cálculo no navegador.</p></section>{selectedExecution && <div className="panel"><ExecutionDetails execution={selectedExecution} /></div>}<section className="panel" aria-labelledby="history-title"><div className="section-heading"><div><p className="eyebrow">Auditoria</p><h2 id="history-title">Execuções persistidas</h2></div></div>{history.length === 0 ? <p className="empty">Ainda não há execuções persistidas para esta partida.</p> : <div className="table-wrap"><table><caption className="sr-only">Histórico de execuções de precificação</caption><thead><tr><th>Finalizada em</th><th>Estado</th><th>Execution ID</th><th><span className="sr-only">Abrir</span></th></tr></thead><tbody>{history.map((execution) => <tr key={execution.execution_id}><td>{execution.finalized_at}</td><td>{executionStatus(execution.status)}</td><td><code>{execution.execution_id}</code></td><td><button className="secondary" type="button" onClick={() => void openExecution(execution.execution_id)}>Abrir</button></td></tr>)}</tbody></table></div>}</section></>}</main>;
}
