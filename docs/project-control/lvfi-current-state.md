# Estado atual do LVFI

- **Atualizado em:** 2026-08-25
- **Referência integrada:** `0d59956283f8efcab4f04e372ffe95cadaab9deb`
- **Branch de referência:** `main` / `origin/main`, integrada pelo PR #20
- **Última task institucional concluída:** `LVFI-ENG-006` — camada versionada de
  precificação de mercados, publicada e integrada pelo PR #20
- **Última task de produto concluída:** `LVFI-ENG-006`
- **Task ativa:** `LVFI-APP-011` — implementação e validação pré-publicação em andamento
- **Último marco institucional:** ENG-006 encerrada institucionalmente
- **Último marco de produto:** precificação de mercados versionada e auditável

## Capacidades disponíveis

Pricing Engine e Método 1 versionados; monólito modular FastAPI; PostgreSQL e
migrations; importação histórica controlada; consultas de competições, temporadas,
times, partidas e estatísticas; amostras determinísticas; execução do Método 1;
execuções persistidas append-only; histórico filtrável; comparação compatível; e
reprodução controlada append-only. A ENG-006 acrescenta snapshots teóricos de
mercado versionados, canônicos e append-only, recebendo taxas imutáveis sem
reexecutar o Método 1. `apps/web` fornece a interface inicial de
consulta e precificação auditável, sem reproduzir matemática no navegador.

## Versões e baseline

- API `0.1.0`; Python `>=3.13,<3.14`; PostgreSQL 16 na validação isolada.
- Distribuição `lvfi-pricing-engine` `1.1.1`; Pricing Engine `1.0.1`.
- Método 1 `1.0.0`; schema canônico do Método 1 `1`.
- API: 96 testes aprovados no PostgreSQL isolado da task, com 100% de statements
  e branches; banco `codex_task_lvfi_eng_006` removido após a validação.
- Pricing Engine: 554 testes aprovados, 100% de statements e branches, sem diff
  no pacote, Método 1 ou matemática.
- Gates institucionais `api` e `pricing` aprovados; logs em
  `.r21-artifacts/quality/`.

## Limitações e decisões pendentes

Autenticação, workflow completo de revisão/aprovação do MVP, Métodos 2 e 3,
Match Center, PDF, odds externas, oportunidades, Value Tracker e deploy não estão
concluídos. O Método 2 permanece sem ID. Decisões de PDF, retenção,
recuperação, identidade, fornecedores, evento/CLV e piloto continuam nos originais
e no [registro de decisões](lvfi-decision-register.md).

## Próxima sequência oficial

- **Última task encerrada:** `LVFI-ENG-006 — Camada versionada de precificação de mercados`, feature commit `5cd76cebc5b5bfc25f804f53fe7f315c03fc209d`, PR #20, merge `0d59956283f8efcab4f04e372ffe95cadaab9deb`.
- **Próxima task oficial:** `LVFI-APP-011 — Entrada de mercado e comparação entre
  modelo e mercado`; planejada, ainda não iniciada e dependente de autorização própria.
- **Ação imediata:** concluir revisão de escopo e publicação autorizada da APP-011.

A ENG-006 receberá taxas imutáveis produzidas pelo Método 1 e usará capacidades
existentes do Pricing Engine, sem alterar a matemática congelada. Terá
versionamento, snapshot, hashes e persistência/auditoria próprios e viabilizará
posteriormente Handicap Asiático e Totais para comparação com mercado. Ela não
autoriza alterações no Método 1 `1.0.0`, Pricing Engine, matemática, schemas,
hashes ou contratos públicos.

## Validação da ENG-006

A API pública cria e lê snapshots de precificação por mercado; os contratos de
taxas e mercados têm schema próprio `1`, serialização canônica e fingerprints
SHA-256. A migration `20260825_05` cria o ledger `market_pricings` com trigger
PostgreSQL que impede update/delete. Os resultados canônicos preservam a saída do
Pricing Engine para `three_way_result`, Totais, Asian Total, Asian Handicap e os
demais mercados públicos, incluindo push e liquidações parciais. Não houve
alteração de `packages/pricing-engine`, Método 1, hashes, baselines ou APP-011.

## Validação integrada da APP-010

A matriz inicial com ESLint `10.8.1` era incompatível com os plugins transitivos
de `eslint-config-next` `16.3.1`. Com a autorização do Product Owner para
continuar, ESLint `9.39.5` foi fixado e o lint passou limpo. Typecheck, Vitest,
build, documentação, API e Pricing Engine foram validados. O smoke frontend →
API → PostgreSQL real passou em `127.0.0.1:55432` com banco descartável removido
ao final. A feature foi publicada no PR #17 e integrada por merge commit
`2c2f34e7059c69d904250e4d0f5caa62ab36543d`; APP-011 não foi iniciada.
