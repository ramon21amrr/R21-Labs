"use client";

import { FormEvent, useEffect, useState } from "react";

import { ApiError, createMarketReference, getMarketReferenceComparison, listMarketPricings, listMarketReferences } from "@/lib/api";
import type { MarketPricing, MarketReferenceObservation, ModelReferenceComparison } from "@/lib/contracts";

function quarterLabel(value: number | null): string {
  return value === null ? "—" : String(value / 4);
}

export function MarketReferencePanel({ matchId }: { matchId: number }) {
  const [snapshots, setSnapshots] = useState<MarketPricing[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState("");
  const [history, setHistory] = useState<MarketReferenceObservation[]>([]);
  const [comparison, setComparison] = useState<ModelReferenceComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void listMarketPricings(matchId)
      .then(({ items }) => {
        if (!active) return;
        setSnapshots(items);
        setSelectedSnapshot(items[0]?.market_pricing_id ?? "");
      })
      .catch((reason: unknown) => active && setError(reason instanceof ApiError ? reason.message : "Não foi possível carregar os snapshots."))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [matchId]);

  useEffect(() => {
    if (!selectedSnapshot) return;
    void listMarketReferences(matchId, selectedSnapshot)
      .then(({ items }) => setHistory(items))
      .catch((reason: unknown) => setError(reason instanceof ApiError ? reason.message : "Não foi possível carregar o histórico."));
  }, [matchId, selectedSnapshot]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const modelLine = data.get("model-line") as string;
    const referenceLine = data.get("reference-line") as string;
    setSaving(true); setError(null);
    try {
      const created = await createMarketReference(matchId, {
        market_pricing_id: selectedSnapshot,
        market_code: String(data.get("market-code")),
        selection: String(data.get("selection")),
        model_line_quarters: modelLine === "" ? null : Number(modelLine),
        reference_line_quarters: referenceLine === "" ? null : Number(referenceLine),
        reference_value: Number(data.get("reference-value")),
        observed_at: new Date(String(data.get("observed-at"))).toISOString()
      }, crypto.randomUUID());
      setHistory(current => [created, ...current]);
      setComparison(await getMarketReferenceComparison(created.observation_id));
    } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Não foi possível registrar a referência."); }
    finally { setSaving(false); }
  }

  return <section className="panel" aria-labelledby="market-reference-title"><div className="section-heading"><div><p className="eyebrow">Mercado externo manual</p><h2 id="market-reference-title">Modelo × Referência</h2></div></div>{loading && <p className="status" role="status">Carregando snapshots ENG-006…</p>}{error && <p className="status error" role="alert">{error}</p>}{!loading && snapshots.length === 0 && <p className="empty">Ainda não há snapshot ENG-006 persistido para esta partida.</p>}{!loading && snapshots.length > 0 && <><label>Snapshot ENG-006<select value={selectedSnapshot} onChange={event => setSelectedSnapshot(event.target.value)}>{snapshots.map(snapshot => <option key={snapshot.market_pricing_id} value={snapshot.market_pricing_id}>{snapshot.finalized_at} · {snapshot.market_pricing_id}</option>)}</select></label><form onSubmit={event => void submit(event)}><div className="sample-grid"><label>Mercado<select name="market-code" defaultValue="asian_handicap"><option value="asian_handicap">Handicap Asiático</option><option value="asian_total">Asian Total</option><option value="total_goals">Total de gols</option><option value="three_way_result">1×2</option></select></label><label>Seleção<input name="selection" required defaultValue="home" /></label><label>Linha teórica (quartos)<input name="model-line" inputMode="numeric" /></label><label>Linha de referência (quartos)<input name="reference-line" inputMode="numeric" /></label><label>Valor de referência<input name="reference-value" type="number" min="0.01" step="0.01" required defaultValue="2" /></label><label>Observada em<input name="observed-at" type="datetime-local" required /></label></div><button type="submit" disabled={saving || !selectedSnapshot}>{saving ? "Registrando…" : "Registrar referência"}</button></form>{comparison && <section aria-live="polite"><h3>Comparação do registro</h3><dl className="metadata"><dt>Snapshot</dt><dd><code>{comparison.observation.market_pricing_id}</code></dd><dt>Linha teórica</dt><dd>{quarterLabel(comparison.observation.model_line_quarters)}</dd><dt>Linha de referência</dt><dd>{quarterLabel(comparison.observation.reference_line_quarters)}</dd><dt>Diferença (passos de 0,25)</dt><dd>{comparison.line_difference_quarters ?? "—"}</dd><dt>Modelo</dt><dd>{comparison.model_value}</dd><dt>Referência</dt><dd>{comparison.observation.reference_value}</dd><dt>Timestamp</dt><dd>{comparison.observation.observed_at}</dd></dl></section>}<section><h3>Histórico imutável</h3>{history.length === 0 ? <p className="empty">Nenhuma referência para o snapshot selecionado.</p> : <ul>{history.map(item => <li key={item.observation_id}>{item.observed_at} · {item.market_code}/{item.selection} · <code>{item.observation_id}</code></li>)}</ul>}</section></>}</section>;
}
