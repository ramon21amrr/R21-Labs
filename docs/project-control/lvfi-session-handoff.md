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
- Última task de produto concluída: `LVFI-ENG-005`, commit
  `8f55ecdd62d71d4439a6c082b0571cbbd8f0f709`, PR #33 e merge histórico
  `9998319b4fd9920fbe8bc54623155ea7352b0d84`.
- Última task institucional concluída: `R21-GOV-003`, commit
  `39a1122b34ff467924962ec4320c0d77c065d0df`, PR #36 e merge histórico
  `c9726fae50bb3b355800e83d1ad9fb8f77216536`.
- Pricing Engine `1.0.1`; distribuição `1.1.1`; Método 1 `1.0.0`; schema 1.

## Task ativa

`LVFI-ENG-007 — Método 2 — Poisson ajustado` está ativa na branch
`codex/lvfi-eng-007-poisson-adjusted`, implementada e pronta para publicação.
O adaptador concreto APP-013 compartilha a seleção de jogos por pares de
produção/complemento, registra evidência e usa o predicado canônico de
concluída. Método 1, Método 3, APP-013 público e Pricing Engine seguem
intactos. Não houve autorização de publicação.

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

Gates atuais: API 221 testes, 4 skips condicionais e 100% de statements/branches
(`gates-20260910-082525-api.log`); Pricing 554 testes e 100%
(`gates-20260910-081242-pricing.log`); QA independente PASS após correção do
seletor compartilhado.

**Ação imediata:** aguardar autorização explícita de publicação, sem iniciar
task posterior.
