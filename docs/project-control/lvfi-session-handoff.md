# Handoff de sessão do LVFI

## Identidade e autoridade

Ramon é o Product Owner e usuário administrador inicial do LVFI. Git e documentos
versionados são a memória oficial. Antes de qualquer task, leia
[current-state](lvfi-current-state.md), valide
[project-state](lvfi-project-state.yaml), consulte o
[task registry](lvfi-task-registry.md) e confirme a decisão mais recente no
[registro](lvfi-decision-register.md). Não infira ID, task ou autorização.

## Baseline e estado corrente

- Base estável histórica da última task `R21-GOV-003`:
  `0b012291e78fb3b20eb887964ebc26d170e0a81c`.
- `reference_commit` significa exclusivamente essa base aprovada. Não deve ser
  trocado pelo commit ou merge produzido pela própria task.
- Resolva o estado corrente, em vez de reutilizar um SHA deste handoff, com
  `git rev-parse HEAD`, `git rev-parse main` e `git rev-parse origin/main`.
- Última task de produto concluída: `LVFI-APP-014`, commit
  `251662b3b7e309fd610e5e2f664263b51e3c7167`, PR #40 e merge histórico
  `8fd593430cdf246932a2225e9f96d38916b05778`.
- Última task institucional concluída: `R21-GOV-003`, commit
  `39a1122b34ff467924962ec4320c0d77c065d0df`, PR #36 e merge histórico
  `c9726fae50bb3b355800e83d1ad9fb8f77216536`.
- Pricing Engine `1.0.1`; distribuição `1.1.1`; Método 1 `1.0.0`; schema 1.

## Última entrega publicada

`LVFI-APP-014 — Catálogo e Configuração` foi publicada e integrada pela branch
`codex/lvfi-app-014-catalog-configuration`, commit `251662b3`, PR #40 e merge
commit `8fd5934`. Não há task ativa. O catálogo `lvfi-mvp@1.0.0`, o ledger
append-only, a precedência reproduzível e a evidência por hash foram validados
em PostgreSQL isolado, incluindo oito revisões concorrentes na mesma cadeia.
Métodos 1/2/3 e Pricing Engine seguem intactos.

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

Gates atuais: API 234 testes, 5 skips condicionais e 100% de statements/branches
(`gates-20260910-151340-full.log`); Pricing 554 testes e 100%; frontend 14
testes, lint, typecheck e build; docs, diff-check, secret scan e QA independente
PASS. A migration `20260910_08` e o teste PostgreSQL real APP-014 passaram, e o
banco descartável foi removido sem `codex_task_*` residual.

**Ação imediata:** não iniciar task posterior; aguardar identificação e
autorização explícitas do Product Owner.
