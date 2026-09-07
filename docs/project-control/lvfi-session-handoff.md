# Handoff de sessão do LVFI

## Identidade e autoridade

Ramon é o Product Owner e usuário administrador inicial do LVFI. Git e documentos
versionados são a memória oficial. Antes de qualquer task, leia
[current-state](lvfi-current-state.md), valide
[project-state](lvfi-project-state.yaml), consulte o
[task registry](lvfi-task-registry.md) e confirme a decisão mais recente no
[registro](lvfi-decision-register.md). Não infira ID, task ou autorização.

## Baseline integrado

- `main` / `origin/main`: `62b3791e55aca8df501943dfe7fef9f6a27e8bd2`,
  merge do PR #28.
- Última task de produto concluída: `LVFI-APP-012`, commit
  `0bec8682912ebfd6c2e597dbda56b6edd34555bd`, PR #26 e merge
  `88d7ab486f007d946a053adba4a8ab552b78ee35`.
- Última task institucional concluída: `R21-DEV-003`, commit
  `522bbbfb96e3c9835c5f1e43e8b295c605cc4650`, PR #28 e merge
  `62b3791e55aca8df501943dfe7fef9f6a27e8bd2`.
- Pricing Engine `1.0.1`; distribuição `1.1.1`; Método 1 `1.0.0`; schema 1.
- APP-012 validou 116 testes de backend PostgreSQL isolado/100% de cobertura;
  lint, typecheck, 9 testes e build do frontend, além do smoke frontend → API →
  PostgreSQL isolado.

## Task ativa

Não há task ativa. `R21-DEV-003 — Orquestração Multiagente do Codex` foi
concluída, publicada e integrada: commit
`522bbbfb96e3c9835c5f1e43e8b295c605cc4650`, PR #28 e merge
`62b3791e55aca8df501943dfe7fef9f6a27e8bd2`. A Skill central, documentação e
templates estão prontos para reutilização. A entrega preservou o Pricing Engine,
Método 1, schemas, hashes, fixtures, versões e roadmap funcional.

## Plano aprovado

A primeira versão será local, para um administrador, com importação revisada de
Excel/CSV e manutenção web de partidas/estatísticas. Ela cobrirá resultado, gols,
escanteios, chutes no gol, finalizações, cartões e faltas; Métodos 1, 2 e 3
separados; configurações versionadas; aprovação e snapshot; Match Center;
PDF-resumo; launcher, backup e restauração.

Método 1 permanece congelado. Método 2 continua sem ID. `LVFI-ENG-005` continua
reservado ao Método 3 e não está autorizado. Mercados estatísticos adicionais
serão experimentais até calibração. Jogadores, membros, deploy remoto, dados/odds
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

Gate atual: perfil `docs`, seguido de `git diff --check`, revisão de escopo e
varredura de segredos. Publicação usa autorização e fluxo próprios.

**Ação imediata:** aguardar o Product Owner nomear e autorizar uma única task
posterior. Nenhuma task funcional sucessora está autorizada.
