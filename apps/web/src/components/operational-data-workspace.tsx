"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { ApiError, confirmImport, createFutureMatch, createStatisticRevision, previewImport } from "@/lib/api";
import type { ImportPreview } from "@/lib/contracts";

const fields = ["home_goals_full_match", "away_goals_full_match", "home_shots_full_match", "away_shots_full_match", "home_shots_on_target_full_match", "away_shots_on_target_full_match", "home_corners_full_match", "away_corners_full_match", "home_fouls_full_match", "away_fouls_full_match", "home_cards_full_match", "away_cards_full_match"];

function message(reason: unknown): string { return reason instanceof ApiError ? reason.message : "Não foi possível concluir a operação."; }

export function OperationalDataWorkspace() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function previewFile() {
    if (!file) return;
    setBusy(true); setNotice(null);
    try { setPreview(await previewImport(file)); } catch (reason) { setPreview(null); setNotice(message(reason)); } finally { setBusy(false); }
  }

  async function confirmFile() {
    if (!file) return;
    setBusy(true); setNotice(null);
    try { const value = await confirmImport(file); setPreview(value); setNotice(value.already_imported ? "Este arquivo já havia sido importado." : "Importação confirmada com sucesso."); } catch (reason) { setNotice(message(reason)); } finally { setBusy(false); }
  }

  async function submitMatch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setNotice(null);
    const values = new FormData(event.currentTarget);
    try { const match = await createFutureMatch({ played_on: String(values.get("played_on")), competition: String(values.get("competition")), season: String(values.get("season")), home_team: String(values.get("home_team")), away_team: String(values.get("away_team")) }); setNotice(`Partida cadastrada com ID ${match.match_id}.`); event.currentTarget.reset(); } catch (reason) { setNotice(message(reason)); } finally { setBusy(false); }
  }

  async function submitRevision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setNotice(null);
    const values = new FormData(event.currentTarget); const availability = String(values.get("availability")) as "available" | "missing";
    try { const revision = await createStatisticRevision(Number(values.get("match_id")), { statistic_field: String(values.get("statistic_field")), availability, new_value: availability === "available" ? Number(values.get("new_value")) : null, reason: String(values.get("reason")) }); setNotice(`Revisão ${revision.revision_id} registrada.`); } catch (reason) { setNotice(message(reason)); } finally { setBusy(false); }
  }

  return <main className="shell"><Link className="back-link" href="/">← Precificação histórica</Link><header className="app-header"><p className="eyebrow">Administração local</p><h1>Dados operacionais</h1><p>Importe dados controlados, cadastre partidas futuras e registre correções justificadas.</p></header>{notice && <p className="status" role="status">{notice}</p>}<section className="panel"><h2>Importar arquivo</h2><label>Arquivo CSV, XLSX ou XLSM<input type="file" accept=".csv,.xlsx,.xlsm" onChange={(event) => { setFile(event.target.files?.[0] ?? null); setPreview(null); }} /></label><p className="hint">A prévia valida o arquivo antes de gravar qualquer dado. A confirmação envia exatamente o arquivo selecionado.</p><button type="button" onClick={() => void previewFile()} disabled={!file || busy}>Gerar prévia</button>{preview && <><dl className="metadata"><dt>Linhas</dt><dd>{preview.total_records}</dd><dt>Aceitas</dt><dd>{preview.accepted_records}</dd><dt>Rejeitadas</dt><dd>{preview.rejected_records}</dd><dt>Hash</dt><dd><code>{preview.source_sha256}</code></dd></dl><button type="button" onClick={() => void confirmFile()} disabled={busy || preview.rejected_records > 0}>Confirmar importação</button></>}</section><section className="panel"><h2>Cadastrar partida futura</h2><form className="filters" onSubmit={(event) => void submitMatch(event)}><label>Data<input required name="played_on" type="date" /></label><label>Competição<input required name="competition" /></label><label>Temporada<input required name="season" placeholder="2026" /></label><label>Mandante<input required name="home_team" /></label><label>Visitante<input required name="away_team" /></label><button disabled={busy} type="submit">Cadastrar</button></form></section><section className="panel"><h2>Corrigir estatística</h2><form className="filters" onSubmit={(event) => void submitRevision(event)}><label>ID da partida<input required min="1" name="match_id" type="number" /></label><label>Campo<select name="statistic_field">{fields.map((field) => <option key={field}>{field}</option>)}</select></label><label>Disponibilidade<select name="availability"><option value="available">Disponível</option><option value="missing">Ausente</option></select></label><label>Novo valor<input min="0" name="new_value" type="number" /></label><label>Motivo<input required name="reason" /></label><button disabled={busy} type="submit">Registrar revisão</button></form></section></main>;
}
