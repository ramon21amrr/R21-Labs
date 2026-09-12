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
- Última task de produto concluída: `LVFI-APP-018`, commit
  `28bae5f3ba64eddf86a344239dbd4eece5590538`, PR #48 e merge histórico
  `80e785c7a8e6f2b8b111a6c56e6a6c97092647db`.
- Última task de governança concluída: `R21-GOV-003`, commit
  `39a1122b34ff467924962ec4320c0d77c065d0df`, PR #36 e merge histórico
  `c9726fae50bb3b355800e83d1ad9fb8f77216536`.
- Pricing Engine `1.0.1`; distribuição `1.1.1`; Método 1 `1.0.0`; schema 1.

## Última entrega publicada

`LVFI-APP-018 — PDF-resumo e Operação Local` é a última entrega publicada e
integrada pela branch `codex/lvfi-app-018-pdf-operacao-local`, commit `28bae5f`,
PR #48 e merge `80e785c`. Adiciona PDF Chromium determinístico de snapshot
aprovado, launcher Windows e recuperação local ensaiada sem alterar APP-012 a
APP-017, Métodos 1/2/3 ou Pricing Engine.

## Plano aprovado

A primeira versão é local, para um administrador, com importação revisada de
Excel/CSV e manutenção web de partidas/estatísticas. Ela cobre resultado, gols,
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

Gates finais APP-018: profile full PASS (parser, diff-check, links locais, API
267 + 6 skips condicionais/100% e Pricing 554/100%); frontend com 19 testes,
lint, typecheck e build PASS; PDF Chromium real, launcher e PostgreSQL 16 real
PASS. O ensaio de backup/restauração passou com RPO de 408,86 s e RTO de 5,62 s;
o ambiente descartável foi removido sem `codex_task_*` residual. QA e revisão de
segurança não encontraram P0/P1. Para HTTPS com rewrite interno, configurar
`LVFI_EXTERNAL_HTTPS=true`; cobertura dedicada de `proxy.ts` permanece melhoria
P2 futura.

**Ação imediata:** nenhuma task posterior está autorizada; aguardar instrução
explícita do Product Owner.
