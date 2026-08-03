# Estado atual do LVFI

- **Atualizado em:** 2026-08-02
- **Referência integrada:** `a1610c85282e5d46ffc2b8094462d00d5135ca01`
- **Branch de referência:** `main` / `origin/main`, verificada em `0/0`
- **Última task institucional concluída:** `R21-GOV-001` — sistema permanente de
  continuidade, publicada e integrada pelo PR #15 no merge
  `a1610c85282e5d46ffc2b8094462d00d5135ca01`
- **Última task de produto concluída:** `LVFI-APP-009`
- **Tasks ativas:** nenhuma
- **Último marco institucional:** continuidade permanente encerrada
- **Último marco de produto:** reprodução controlada de execuções de precificação

## Capacidades disponíveis

Pricing Engine e Método 1 versionados; monólito modular FastAPI; PostgreSQL e
migrations; importação histórica controlada; consultas de competições, temporadas,
times, partidas e estatísticas; amostras determinísticas; execução do Método 1;
execuções persistidas append-only; histórico filtrável; comparação compatível; e
reprodução controlada append-only. `apps/web` ainda não existe.

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

Frontend, autenticação, workflow completo de revisão/aprovação do MVP, Métodos 2
e 3, Match Center, PDF, odds externas, oportunidades, Value Tracker e deploy não
estão concluídos. O Método 2 permanece sem ID. Decisões de PDF, retenção,
recuperação, identidade, fornecedores, evento/CLV e piloto continuam nos originais
e no [registro de decisões](lvfi-decision-register.md).

## Próxima sequência oficial

- **Próxima task oficial:** `LVFI-APP-010 — Fundação do frontend e tela inicial de precificação`.
- **Próxima etapa planejada:** `LVFI-APP-011 — Entrada de mercado e comparação entre modelo e mercado`.
- **Ação imediata:** iniciar `LVFI-APP-010 — Fundação do frontend e tela inicial
  de precificação` após a publicação deste encerramento institucional.

Este encerramento não iniciou APP-010/011 e não alterou Pricing Engine, backend,
PostgreSQL, APIs, matemática, frontend, migrations, dependências ou lockfiles.
