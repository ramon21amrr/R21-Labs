# Estado atual do LVFI

- **Atualizado em:** 2026-08-19
- **Referência integrada:** `2c2f34e7059c69d904250e4d0f5caa62ab36543d`
- **Branch de referência:** `main` / `origin/main`, integrada pelo PR #17
- **Última task institucional concluída:** `R21-GOV-001` — sistema permanente de
  continuidade, publicada e integrada pelo PR #15 no merge
  `a1610c85282e5d46ffc2b8094462d00d5135ca01`
- **Última task de produto concluída:** `LVFI-APP-010`
- **Task ativa:** nenhuma
- **Último marco institucional:** continuidade permanente encerrada
- **Último marco de produto:** frontend e tela inicial de precificação

## Capacidades disponíveis

Pricing Engine e Método 1 versionados; monólito modular FastAPI; PostgreSQL e
migrations; importação histórica controlada; consultas de competições, temporadas,
times, partidas e estatísticas; amostras determinísticas; execução do Método 1;
execuções persistidas append-only; histórico filtrável; comparação compatível; e
reprodução controlada append-only. `apps/web` fornece a interface inicial de
consulta e precificação auditável, sem reproduzir matemática no navegador.

## Versões e baseline

- API `0.1.0`; Python `>=3.13,<3.14`; PostgreSQL 16 na validação isolada.
- Distribuição `lvfi-pricing-engine` `1.1.1`; Pricing Engine `1.0.1`.
- Método 1 `1.0.0`; schema canônico do Método 1 `1`.
- API: 86 testes na baseline integrada; log local confirma 85 aprovados e 1
  teste de PostgreSQL isolado ignorado fora do banco da task, com 100% de
  statements e branches.
- Pricing Engine: 554 testes aprovados, 100% de statements e branches.
- Ruff, mypy, compileall e pip check foram informados como aprovados no
  encerramento da APP-009; esta task documental executará somente gates `docs`.

## Limitações e decisões pendentes

Autenticação, workflow completo de revisão/aprovação do MVP, Métodos 2 e 3,
Match Center, PDF, odds externas, oportunidades, Value Tracker e deploy não estão
concluídos. O Método 2 permanece sem ID. Decisões de PDF, retenção,
recuperação, identidade, fornecedores, evento/CLV e piloto continuam nos originais
e no [registro de decisões](lvfi-decision-register.md).

## Próxima sequência oficial

- **Última task encerrada:** `LVFI-APP-010 — Fundação do frontend e tela inicial de precificação`, PR #17, merge `2c2f34e7059c69d904250e4d0f5caa62ab36543d`.
- **Próxima task oficial planejada:** `LVFI-APP-011 — Entrada de mercado e comparação entre modelo e mercado`; não iniciada.
- **Ação imediata:** aguardar detalhamento e autorização próprios antes de iniciar APP-011.

A APP-010 foi iniciada a partir da base autorizada `2c2c46447698de2641efe23b9a8491b2d6a7086d`.
Ela não autoriza alterações em APP-011, Pricing Engine, matemática, schemas, hashes
ou contratos públicos sem incompatibilidade demonstrada.

## Validação integrada da APP-010

A matriz inicial com ESLint `10.8.1` era incompatível com os plugins transitivos
de `eslint-config-next` `16.3.1`. Com a autorização do Product Owner para
continuar, ESLint `9.39.5` foi fixado e o lint passou limpo. Typecheck, Vitest,
build, documentação, API e Pricing Engine foram validados. O smoke frontend →
API → PostgreSQL real passou em `127.0.0.1:55432` com banco descartável removido
ao final. A feature foi publicada no PR #17 e integrada por merge commit
`2c2f34e7059c69d904250e4d0f5caa62ab36543d`; APP-011 não foi iniciada.
