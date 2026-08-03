# Estado atual do LVFI

- **Atualizado em:** 2026-08-02
- **Referência integrada:** `094b9ea51d6dabbac6154ec66e987d5fe83d8033`
- **Branch de referência:** `main` / `origin/main`, verificada em `0/0`
- **Task institucional ativa:** `R21-GOV-001` — continuidade permanente
- **Última task de produto concluída:** `LVFI-APP-009`
- **Último marco:** reprodução controlada de execuções de precificação

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
- **Ação imediata:** executar a APP-010 após a integração da R21-GOV-001.

Antes disso é proibido iniciar APP-010/011, alterar Pricing Engine, backend,
PostgreSQL, APIs, matemática, frontend ou dependências dentro da R21-GOV-001.
