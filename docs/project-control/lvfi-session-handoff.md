# Handoff de sessão do LVFI

## Identidade e autoridade

Ramon é o Product Owner e usuário administrador inicial do LVFI. Git e documentos
versionados são a memória oficial. Antes de qualquer task, leia
[current-state](lvfi-current-state.md), valide
[project-state](lvfi-project-state.yaml), consulte o
[task registry](lvfi-task-registry.md) e confirme a decisão mais recente no
[registro](lvfi-decision-register.md). Não infira ID, task ou autorização.

## Baseline e estado corrente

- Base estável aprovada da `LVFI-APP-016`:
  `9bc9a7cdb58fcdf5947b5a433c602465add453e3`.
- `reference_commit` significa exclusivamente essa base aprovada. Não deve ser
  trocado pelo commit ou merge produzido pela própria task.
- Resolva o estado corrente, em vez de reutilizar um SHA deste handoff, com
  `git rev-parse HEAD`, `git rev-parse main` e `git rev-parse origin/main`.
- Última task de produto tecnicamente concluída: `LVFI-APP-016`; sem commit,
  push, PR ou merge nesta execução.
- Última task de governança concluída: `R21-GOV-003`, commit
  `39a1122b34ff467924962ec4320c0d77c065d0df`, PR #36 e merge histórico
  `c9726fae50bb3b355800e83d1ad9fb8f77216536`.
- Pricing Engine `1.0.1`; distribuição `1.1.1`; Método 1 `1.0.0`; schema 1.

## Última entrega publicada

`LVFI-APP-015 — Workflow de Revisão, Aprovação e Snapshot` é a última entrega
publicada e integrada. A `LVFI-APP-016 — Match Center` está tecnicamente
concluída na branch `codex/lvfi-app-016-match-center` e aguarda autorização
posterior de publicação. Integra uma jornada por partida sem alterar APP-012 a
APP-015, Métodos 1/2/3 ou Pricing Engine.

## Plano aprovado

A primeira versão será local, para um administrador, com importação revisada de
Excel/CSV e manutenção web de partidas/estatísticas. Ela cobrirá resultado, gols,
escanteios, chutes no gol, finalizações, cartões e faltas; Métodos 1, 2 e 3
separados; configurações versionadas; aprovação e snapshot; Match Center;
PDF-resumo; launcher, backup e restauração.

Método 1 permanece congelado. Método 2 possui agora o ID `LVFI-ENG-007` e a
versão `method_two_adjusted_poisson` `1.0.0`, com schemas 1. `LVFI-ENG-005` foi concluída exclusivamente
como Método 3. Mercados estatísticos adicionais serão
experimentais até calibração. Jogadores, membros, deploy remoto, dados/odds
automáticos, oportunidades e Value Tracker estão fora da primeira versão.

Os quatro materiais privados estão registrados apenas por SHA-256 no documento
39. Não anexar ou ler novamente se os fingerprints não mudarem. A revisão
corrigida do XLSM é
`FDCA46B855CC3FA28A34F622D282221F9B8E3EA41B0B6664432D9614D45D3924`:
as 2.694 linhas foram revalidadas sem inconsistência relacional, valor negativo
ou chave duplicada; a divergência anterior da linha 2224 foi resolvida na origem.

## Navegação, gates e ação imediata

O Graphify disponível no início da R21-DEV-003 estava anterior ao HEAD e foi usado
somente como índice parcial, com fallback dirigido e confirmação nos originais.
Ele foi reconstruído no gate final em modo local `code-only`, com 316 nós e 663
relações; a consulta de código respondeu e a varredura dos artefatos principais
não encontrou os padrões sensíveis verificados.

Gates finais APP-016: profile full PASS (parser, diff-check, links locais, API
253/100% e Pricing 554/100%) em `gates-20260911-080410-full.log`; frontend com
18 testes, lint, typecheck e build PASS; API em PostgreSQL 16 real com migrations
até `20260910_09`, 258 testes e 100% PASS. O banco descartável foi removido sem
`codex_task_*` residual. QA independente não encontrou P0; acessibilidade por
teclado/foco e a cobertura foram revalidadas após os ajustes.

**Ação imediata:** aguardar autorização de publicação da `LVFI-APP-016`; não
iniciar task sucessora.
