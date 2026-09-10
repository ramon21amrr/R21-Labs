"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiError, createConfigurationRevision, getConfigurationCatalog, getEffectiveConfiguration } from "@/lib/api";
import type { ConfigurationCatalog, ConfigurationParameter, ConfigurationRevision, ConfigurationScope, ConfigurationValue, EffectiveConfiguration } from "@/lib/contracts";

function failureMessage(reason: unknown): string {
  return reason instanceof ApiError ? reason.message : "Não foi possível concluir a operação.";
}

function scopeLabel(scope: ConfigurationScope): string {
  return ({ global: "Global", competition: "Competição", match: "Partida" })[scope];
}

function RevisionEvidence({ revisions, title, empty }: { revisions: ConfigurationRevision[]; title: string; empty: string }) {
  return <section aria-label={title}>
    <h3>{title}</h3>
    {revisions.length === 0 ? <p className="empty">{empty}</p> : <div className="table-wrap"><table><caption className="sr-only">{title}</caption><thead><tr><th>Parâmetro</th><th>Valor</th><th>Escopo</th><th>Revisão</th><th>Hash</th></tr></thead><tbody>{revisions.map((revision) => <tr key={revision.revision_id}><td>{revision.parameter_code}</td><td>{String(revision.value)}</td><td>{scopeLabel(revision.scope)}</td><td>{revision.revision_id}</td><td><code>{revision.revision_hash}</code></td></tr>)}</tbody></table></div>}
  </section>;
}

function CatalogDetails({ catalog }: { catalog: ConfigurationCatalog }) {
  const { payload } = catalog;
  return <section className="panel" aria-labelledby="configuration-catalog-title">
    <p className="eyebrow">Catálogo imutável da API</p><h2 id="configuration-catalog-title">Catálogo de configuração</h2>
    <dl className="metadata"><dt>Identificador</dt><dd>{catalog.catalog_id}</dd><dt>Schema</dt><dd>{catalog.schema_version}</dd><dt>Hash do conteúdo</dt><dd><code>{catalog.content_hash}</code></dd></dl>
    <section><h3>Parâmetros estatísticos autorizados</h3><div className="table-wrap"><table><caption className="sr-only">Parâmetros e valores enumerados do catálogo</caption><thead><tr><th>Parâmetro</th><th>Valores permitidos</th></tr></thead><tbody>{payload.statistical_parameters.map((parameter) => <tr key={parameter.code}><td>{parameter.code}</td><td>{parameter.allowed_values.map(String).join(" · ")}</td></tr>)}</tbody></table></div></section>
    <section><h3>Linhas estatísticas</h3><p className="hint">Handicap em quartos: {payload.statistical_lines.handicap_line_quarters.join(" · ")}</p><p className="hint">Total em quartos: {payload.statistical_lines.total_line_quarters.join(" · ")}</p></section>
    <section><h3>Bandas de probabilidade</h3><p>{payload.probability_bands.map((band) => band.code).join(" · ")}</p></section>
  </section>;
}

export function ConfigurationCatalogWorkspace() {
  const [catalog, setCatalog] = useState<ConfigurationCatalog | null>(null);
  const [parameterCode, setParameterCode] = useState("");
  const [valueIndex, setValueIndex] = useState(0);
  const [scope, setScope] = useState<ConfigurationScope>("global");
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const selectedParameter = useMemo<ConfigurationParameter | null>(() => catalog?.payload.statistical_parameters.find((parameter) => parameter.code === parameterCode) ?? null, [catalog, parameterCode]);

  useEffect(() => {
    let active = true;
    void getConfigurationCatalog().then((loaded) => {
      if (!active) return;
      setCatalog(loaded);
      setParameterCode(loaded.payload.statistical_parameters[0]?.code ?? "");
      setValueIndex(0);
      setNotice(null);
    }).catch((reason: unknown) => { if (active) setNotice(failureMessage(reason)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!catalog || !selectedParameter) return;
    const values = new FormData(event.currentTarget);
    const contextId = Number(values.get(scope === "competition" ? "competition_id" : "match_id"));
    const value = selectedParameter.allowed_values[valueIndex];
    if (value === undefined) return;
    setBusy(true); setNotice(null);
    try {
      const revision = await createConfigurationRevision({
        catalog_id: catalog.catalog_id,
        scope,
        parameter_code: selectedParameter.code,
        value,
        ...(scope === "competition" ? { competition_id: contextId } : {}),
        ...(scope === "match" ? { match_id: contextId } : {}),
        actor: String(values.get("actor")),
        reason: String(values.get("reason"))
      });
      setNotice(`Revisão ${revision.revision_id} registrada para ${scopeLabel(revision.scope).toLowerCase()}.`);
      event.currentTarget.reset();
      setScope("global");
      setValueIndex(0);
    } catch (reason) { setNotice(failureMessage(reason)); } finally { setBusy(false); }
  }

  return <section className="shell" aria-labelledby="configuration-admin-title">
    <header className="app-header"><p className="eyebrow">Administração local</p><h1 id="configuration-admin-title">Catálogo e configuração</h1><p>Registre revisões justificadas com valores enumerados no catálogo. Pesos e multiplicadores não são configuráveis aqui.</p></header>
    {loading && <p className="status" role="status">Carregando catálogo versionado…</p>}
    {!loading && notice && <p className={`status${notice.startsWith("Revisão") ? "" : " error"}`} role={notice.startsWith("Revisão") ? "status" : "alert"}>{notice}</p>}
    {catalog && <><CatalogDetails catalog={catalog} /><section className="panel" aria-labelledby="configuration-revision-title"><p className="eyebrow">Revisão append-only</p><h2 id="configuration-revision-title">Configurar parâmetro estatístico</h2><p className="hint">A precedência e o hash efetivo são calculados exclusivamente pela API.</p><form className="filters" onSubmit={(event) => void submit(event)}>
      <label>Parâmetro<select aria-label="Parâmetro de configuração" value={parameterCode} onChange={(event) => { setParameterCode(event.target.value); setValueIndex(0); }}>{catalog.payload.statistical_parameters.map((parameter) => <option key={parameter.code} value={parameter.code}>{parameter.code}</option>)}</select></label>
      <label>Valor<select aria-label="Valor de configuração" value={valueIndex} onChange={(event) => setValueIndex(Number(event.target.value))}>{selectedParameter?.allowed_values.map((value, index) => <option key={`${String(value)}-${index}`} value={index}>{String(value)}</option>)}</select></label>
      <label>Escopo<select aria-label="Escopo de configuração" value={scope} onChange={(event) => setScope(event.target.value as ConfigurationScope)}><option value="global">Global</option><option value="competition">Competição</option><option value="match">Partida</option></select></label>
      {scope === "competition" && <label>ID da competição<input aria-label="ID da competição" required min="1" name="competition_id" type="number" /></label>}
      {scope === "match" && <label>ID da partida<input aria-label="ID da partida" required min="1" name="match_id" type="number" /></label>}
      <label>Autor<input aria-label="Autor" required name="actor" /></label><label>Justificativa<input aria-label="Justificativa" required name="reason" /></label><button disabled={busy} type="submit">{busy ? "Registrando…" : "Registrar revisão"}</button>
    </form></section></>}
  </section>;
}

export function EffectiveConfigurationPanel({ matchId }: { matchId: number }) {
  const [effective, setEffective] = useState<EffectiveConfiguration | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const invalidMatchId = !Number.isSafeInteger(matchId) || matchId < 1;

  useEffect(() => {
    if (invalidMatchId) return;
    let active = true;
    void getEffectiveConfiguration(matchId).then((value) => { if (active) { setEffective(value); setError(null); } }).catch((reason: unknown) => { if (active) setError(failureMessage(reason)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [invalidMatchId, matchId]);

  return <section className="shell" aria-labelledby="effective-configuration-title"><div className="panel"><p className="eyebrow">Resposta reproduzível da API</p><h2 id="effective-configuration-title">Configuração efetiva</h2><p className="hint">A API resolve a precedência partida → competição → global e fornece a evidência abaixo.</p>
    {invalidMatchId && <p className="status error" role="alert">Identificador de partida inválido.</p>}
    {!invalidMatchId && loading && <p className="status" role="status">Carregando configuração efetiva…</p>}
    {!invalidMatchId && error && <p className="status error" role="alert">{error}</p>}
    {effective && <><dl className="metadata"><dt>Partida</dt><dd>{effective.match_id}</dd><dt>Competição</dt><dd>{effective.competition_id}</dd><dt>Catálogo</dt><dd>{effective.catalog_id}</dd><dt>Hash do catálogo</dt><dd><code>{effective.catalog_hash}</code></dd><dt>Hash efetivo</dt><dd><code>{effective.effective_hash}</code></dd></dl>
      <section><h3>Valores efetivos</h3><div className="table-wrap"><table><caption className="sr-only">Valores efetivos fornecidos pela API</caption><thead><tr><th>Parâmetro</th><th>Valor</th></tr></thead><tbody>{Object.entries(effective.values).map(([parameter, value]) => <tr key={parameter}><td>{parameter}</td><td>{String(value)}</td></tr>)}</tbody></table></div></section>
      <RevisionEvidence title="Revisões selecionadas" revisions={effective.selected_revisions} empty="Não há revisão configurada para esta partida." />
      <RevisionEvidence title="Candidatas de menor precedência" revisions={effective.discarded_revisions} empty="Não houve revisões candidatas substituídas por maior precedência." />
    </>}
  </div></section>;
}
