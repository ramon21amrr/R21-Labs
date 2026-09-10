# Handoff de sessão do LVFI

## Identidade e autoridade

Ramon é o Product Owner e usuário administrador inicial do LVFI. Git e documentos
versionados são a memória oficial. Antes de qualquer task, leia
[current-state](lvfi-current-state.md), valide
[project-state](lvfi-project-state.yaml), consulte o
[task registry](lvfi-task-registry.md) e confirme a decisão mais recente no
[registro](lvfi-decision-register.md). Não infira ID, task ou autorização.

## Baseline e estado corrente

- Base estável da task ativa `R21-GOV-003`:
  `0b012291e78fb3b20eb887964ebc26d170e0a81c`.
- `reference_commit` significa exclusivamente essa base aprovada. Não deve ser
  trocado pelo commit ou merge produzido pela própria task.
- Resolva o estado corrente, em vez de reutilizar um SHA deste handoff, com
  `git rev-parse HEAD`, `git rev-parse main` e `git rev-parse origin/main`.
- Última task de produto concluída: `LVFI-ENG-005`, commit
  `8f55ecdd62d71d4439a6c082b0571cbbd8f0f709`, PR #33 e merge histórico
  `9998319b4fd9920fbe8bc54623155ea7352b0d84`.
- Última task institucional concluída: `R21-GOV-002`.
- Pricing Engine `1.0.1`; distribuição `1.1.1`; Método 1 `1.0.0`; schema 1.

## Task ativa

`R21-GOV-003 — Referência Git não autorreferencial` está em execução, sem
autorização de commit, push, PR ou merge. O escopo é somente continuidade:
estabilizar a semântica de `reference_commit`, obter HEAD/main/origin/main em
runtime e retirar ENG-005 de `planned_tasks`. Não iniciar Método 2 nem qualquer
sucessora funcional.

## Plano aprovado

A primeira versão será local, para um administrador, com importação revisada de
Excel/CSV e manutenção web de partidas/estatísticas. Ela cobrirá resultado, gols,
escanteios, chutes no gol, finalizações, cartões e faltas; Métodos 1, 2 e 3
separados; configurações versionadas; aprovação e snapshot; Match Center;
PDF-resumo; launcher, backup e restauração.

Método 1 permanece congelado. Método 2 continua sem ID. `LVFI-ENG-005` foi
concluída exclusivamente como Método 3. Mercados estatísticos adicionais serão
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

Gate atual: R21-GOV-003 requer gates de documentação, diff/check, links, secrets
e QA. Nenhuma task funcional sucessora está autorizada.

**Ação imediata:** concluir somente R21-GOV-003; depois, aguardar o Product
Owner nomear e autorizar uma única task posterior.
