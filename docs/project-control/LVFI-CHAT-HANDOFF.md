# LVFI — handoff único para novo chat

## Estado

R21 Labs transforma conhecimento em produtos digitais próprios. O LVFI é seu
primeiro produto: plataforma auditável de dados e inteligência de futebol. Ramon
é o Product Owner e usuário administrador inicial; decisões finais são humanas.

- Referência integrada: `2c2f34e7059c69d904250e4d0f5caa62ab36543d` em `main` / `origin/main`, PR #17.
- Última task institucional concluída: `R21-GOV-001` — continuidade permanente,
  publicada e integrada pelo PR #15.
- Última task de produto concluída: `LVFI-APP-010` — frontend e tela inicial de precificação, integrada pelo PR #17.
- Task ativa: nenhuma.
- Próxima task oficial planejada: `LVFI-APP-011`; não iniciada.
- Próxima etapa planejada: `LVFI-APP-011` — entrada/comparação de mercado.
- Ação imediata: aguardar detalhamento e autorização próprios para APP-011.

O frontend está implementado e passou em lint, typecheck, testes e build. A
incompatibilidade inicial entre ESLint `10.8.1` e os plugins transitivos do
`eslint-config-next` `16.3.1` foi resolvida pelo pin estável `9.39.5`. O smoke
frontend → API → PostgreSQL real passou com banco isolado removido; a publicação
foi concluída no PR #17 pelo merge `2c2f34e7059c69d904250e4d0f5caa62ab36543d`.

Capacidades atuais: Pricing Engine `1.0.1`, distribuição `1.1.1`, Método 1
`1.0.0`, schema 1; FastAPI/PostgreSQL; importação/consulta histórica; amostras;
execução; persistência append-only; histórico; comparação; reprodução. Baseline:
API 86 testes e Pricing Engine 554, ambos com cobertura integral. Frontend,
autenticação, workflow completo do MVP, Métodos 2/3, PDF, odds, oportunidades,
Value Tracker e deploy permanecem não concluídos.

## Roadmap compacto

`dados → modelo → preço → mercado → oportunidade → resultado → melhoria contínua`

APP-010 entregou a interface inicial e está encerrada institucionalmente; APP-011 é a etapa planejada de mercado. Depois, tasks e
decisões próprias completam o MVP utilizável, piloto, preparação comercial e
lançamento. O Método 2 permanece sem ID. Mercado automatizado, oportunidades e
Value Tracker estão fora do MVP/futuros conforme os documentos originais.

O roadmap completo permanece preservado no
[roadmap institucional](lvfi-product-roadmap.md): fundações concluídas; APP-010 e
APP-011; MVP interno e utilizável; relatórios; deploy/recuperação; piloto;
operação de mercado; oportunidades; Value Tracker/resultados; preparação
comercial; lançamento e evolução.

## Decisões e regras

- Git e documentos versionados são a memória oficial.
- Não inferir próxima task, ID, decisão ou roadmap.
- `LVFI-ENG-004` é a correção numérica publicada no PR #4, nunca Método 2.
- Toda task atualiza continuidade antes de encerramento institucional.
- Graphify é mapa; fatos críticos vêm dos originais.
- Branch não-main, gates, diff/segredos e autorização separada para commit, push,
  PR e merge. Nunca force-push ou reescreva histórico.

Decisões pendentes: ID/plano do Método 2; detalhamento APP-011; PDF; autenticação;
retenção/recuperação; deploy; fornecedores; evento/CLV do Value Tracker; piloto.

## Bootstrap

```text
Trate este handoff e o Git como fontes de verdade. Comece por
docs/project-control/lvfi-current-state.md e valide lvfi-project-state.yaml contra
o reference_commit. Não infira a próxima task, não replaneje o produto e não
sobrescreva decisões aprovadas. Consulte os documentos originais em caso de dúvida
e apresente uma ação imediata por vez. Sempre informe: Modelo, Esforço, Agente,
Modo, Onde, Mesma tarefa ou nova tarefa, Ação única, O que conclui e Próximo passo.
```

Fontes: [índice de controle](README.md), [estado](lvfi-current-state.md),
[YAML](lvfi-project-state.yaml), [roadmap](lvfi-product-roadmap.md),
[tasks](lvfi-task-registry.md), [decisões](lvfi-decision-register.md),
[Company Context](../company/company-context.md) e
[produto](../products/linha-de-valor-football-intelligence/README.md).
