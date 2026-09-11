"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import { CanonicalValue } from "@/components/canonical-value";
import { ApiError, approveAnalysis, calculateAnalysis, createAnalysis, getAnalysis, getAnalysisSnapshot, listAnalyses, reviewAnalysis } from "@/lib/api";
import type { Analysis, AnalysisEventType, AnalysisSnapshot, WorkflowDecisionDraft } from "@/lib/contracts";

function failureMessage(reason: unknown, fallback: string): string {
  return reason instanceof ApiError ? reason.message : fallback;
}

function statusLabel(status: Analysis["status"]): string {
  return ({ draft: "Rascunho", calculated: "Calculada", approved: "Aprovada" })[status];
}

function eventLabel(event: AnalysisEventType): string {
  return ({ calculated: "Calculada", reviewed: "Revisada", approved: "Aprovada" })[event];
}

function replaceAnalysis(history: Analysis[], value: Analysis): Analysis[] {
  return [value, ...history.filter((item) => item.analysis_id !== value.analysis_id)];
}

function WorkflowHistory({ analyses, select }: { analyses: Analysis[]; select: (analysisId: string) => void }) {
  return <section aria-labelledby="analysis-history-title"><h3 id="analysis-history-title">Histórico append-only</h3>
    {analyses.length === 0 ? <p className="empty">Ainda não há análises para esta partida.</p> : <div className="table-wrap"><table><caption className="sr-only">Histórico de análises da partida</caption><thead><tr><th>Criada em</th><th>Estado</th><th>Analysis ID</th><th><span className="sr-only">Consultar</span></th></tr></thead><tbody>{analyses.map((analysis) => <tr key={analysis.analysis_id}><td>{analysis.created_at}</td><td><span className={`badge ${analysis.status}`}>{statusLabel(analysis.status)}</span></td><td><code>{analysis.analysis_id}</code></td><td><button className="secondary" type="button" onClick={() => select(analysis.analysis_id)}>Consultar</button></td></tr>)}</tbody></table></div>}
  </section>;
}

function SnapshotDetails({ snapshot }: { snapshot: AnalysisSnapshot }) {
  return <section aria-labelledby="analysis-snapshot-title"><h3 id="analysis-snapshot-title">Snapshot imutável</h3><p className="hint">O payload, hash e evidências abaixo foram congelados pela API após a aprovação; o navegador não os recalcula.</p><dl className="metadata"><dt>Snapshot ID</dt><dd><code>{snapshot.snapshot_id}</code></dd><dt>Criado em</dt><dd>{snapshot.created_at}</dd><dt>SHA-256</dt><dd><code>{snapshot.snapshot_hash}</code></dd></dl><CanonicalValue value={snapshot.payload} /></section>;
}

export function AnalysisWorkflow({ matchId }: { matchId: number }) {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [selected, setSelected] = useState<Analysis | null>(null);
  const [snapshot, setSnapshot] = useState<AnalysisSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const invalidMatchId = !Number.isSafeInteger(matchId) || matchId < 1;

  useEffect(() => {
    if (invalidMatchId) return;
    let active = true;
    void listAnalyses(matchId).then((history) => {
      if (!active) return;
      setAnalyses(history.analyses);
      setMessage(null);
    }).catch((reason: unknown) => {
      if (active) setMessage(failureMessage(reason, "Não foi possível carregar o histórico de análises."));
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [invalidMatchId, matchId]);

  async function openAnalysis(analysisId: string) {
    setBusy(true); setMessage(null); setSnapshot(null);
    try {
      const analysis = await getAnalysis(analysisId);
      setSelected(analysis); setAnalyses((current) => replaceAnalysis(current, analysis));
      if (analysis.status === "approved") setSnapshot(await getAnalysisSnapshot(analysis.analysis_id));
    } catch (reason) { setMessage(failureMessage(reason, "Não foi possível consultar a análise.")); }
    finally { setBusy(false); }
  }

  async function createDraft() {
    setBusy(true); setMessage(null); setSnapshot(null);
    try {
      const analysis = await createAnalysis(matchId);
      setSelected(analysis); setAnalyses((current) => replaceAnalysis(current, analysis));
      setMessage("Rascunho criado. Vincule uma execução concluída para calcular.");
    } catch (reason) { setMessage(failureMessage(reason, "Não foi possível criar o rascunho.")); }
    finally { setBusy(false); }
  }

  async function calculate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const executionId = String(new FormData(event.currentTarget).get("execution_id") ?? "");
    setBusy(true); setMessage(null);
    try {
      const analysis = await calculateAnalysis(selected.analysis_id, executionId);
      setSelected(analysis); setAnalyses((current) => replaceAnalysis(current, analysis));
      setMessage("Análise calculada a partir da execução persistida informada.");
    } catch (reason) { setMessage(failureMessage(reason, "Não foi possível vincular a execução.")); }
    finally { setBusy(false); }
  }

  async function decide(event: FormEvent<HTMLFormElement>, action: "review" | "approve") {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    const payload: WorkflowDecisionDraft = { actor: String(data.get("actor") ?? ""), reason: String(data.get("reason") ?? "") };
    setBusy(true); setMessage(null);
    try {
      if (action === "review") {
        const analysis = await reviewAnalysis(selected.analysis_id, payload);
        setSelected(analysis); setAnalyses((current) => replaceAnalysis(current, analysis));
        setMessage("Revisão registrada no histórico imutável.");
      } else {
        const approved = await approveAnalysis(selected.analysis_id, payload);
        setSelected(approved.analysis); setSnapshot(approved.snapshot); setAnalyses((current) => replaceAnalysis(current, approved.analysis));
        setMessage("Análise aprovada e snapshot imutável criado.");
      }
      event.currentTarget.reset();
    } catch (reason) { setMessage(failureMessage(reason, action === "review" ? "Não foi possível registrar a revisão." : "Não foi possível aprovar a análise.")); }
    finally { setBusy(false); }
  }

  return <section className="shell" aria-labelledby="analysis-workflow-title"><div className="panel"><div className="section-heading"><div><p className="eyebrow">APP-015 · fluxo auditável</p><h2 id="analysis-workflow-title">Revisão, aprovação e snapshot</h2></div><button type="button" onClick={() => void createDraft()} disabled={busy || invalidMatchId}>{busy ? "Aguarde…" : "Criar rascunho"}</button></div><p className="hint">As transições e a captura reprodutível são aplicadas pela API. Esta tela não calcula resultados, hashes ou fingerprints.</p>
    {invalidMatchId && <p className="status error" role="alert">Identificador de partida inválido.</p>}
    {!invalidMatchId && loading && <p className="status" role="status">Carregando histórico de análises…</p>}
    {message && <p className={`status${message.startsWith("Não foi") ? " error" : ""}`} role={message.startsWith("Não foi") ? "alert" : "status"}>{message}</p>}
    {selected && <section aria-labelledby="selected-analysis-title"><h3 id="selected-analysis-title">Análise selecionada · {statusLabel(selected.status)}</h3><dl className="metadata"><dt>Analysis ID</dt><dd><code>{selected.analysis_id}</code></dd><dt>Criada em</dt><dd>{selected.created_at}</dd><dt>Estado</dt><dd>{statusLabel(selected.status)}</dd></dl>
      {selected.status === "draft" && <form className="filters" onSubmit={(event) => void calculate(event)}><label>Execution ID concluída<input aria-label="Execution ID concluída" name="execution_id" required minLength={36} maxLength={36} /></label><div><button type="submit" disabled={busy}>Vincular e calcular</button></div></form>}
      {selected.status === "calculated" && <><form className="filters" onSubmit={(event) => void decide(event, "review")}><label>Autor da revisão<input aria-label="Autor da revisão" name="actor" required defaultValue="local-admin" maxLength={128} /></label><label>Justificativa da revisão<input aria-label="Justificativa da revisão" name="reason" required maxLength={2000} /></label><div><button type="submit" disabled={busy}>Registrar revisão</button></div></form><form className="filters" onSubmit={(event) => void decide(event, "approve")}><label>Autor da aprovação<input aria-label="Autor da aprovação" name="actor" required defaultValue="local-admin" maxLength={128} /></label><label>Justificativa da aprovação<input aria-label="Justificativa da aprovação" name="reason" required maxLength={2000} /></label><div><button type="submit" disabled={busy}>Aprovar e criar snapshot</button></div></form></>}
      <section><h4>Eventos auditáveis</h4>{selected.events.length === 0 ? <p className="empty">O rascunho ainda não possui eventos.</p> : <div className="table-wrap"><table><caption className="sr-only">Eventos auditáveis da análise</caption><thead><tr><th>Evento</th><th>Em</th><th>Autor</th><th>Justificativa</th><th>Execução</th></tr></thead><tbody>{selected.events.map((item) => <tr key={item.event_id}><td>{eventLabel(item.event_type)}</td><td>{item.created_at}</td><td>{item.actor ?? "—"}</td><td>{item.reason ?? "—"}</td><td>{item.execution_id ? <code>{item.execution_id}</code> : "—"}</td></tr>)}</tbody></table></div>}</section>
      {snapshot && <SnapshotDetails snapshot={snapshot} />}
    </section>}
    {!loading && <WorkflowHistory analyses={analyses} select={(analysisId) => void openAnalysis(analysisId)} />}
  </div></section>;
}
