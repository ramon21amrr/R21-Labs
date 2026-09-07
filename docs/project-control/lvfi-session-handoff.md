# Handoff de sessão do LVFI

## Identidade e autoridade

Ramon é o Product Owner e usuário administrador inicial do LVFI. Git e documentos
versionados são a memória oficial. Antes de qualquer task, leia
[current-state](lvfi-current-state.md), valide
[project-state](lvfi-project-state.yaml), consulte o
[task registry](lvfi-task-registry.md) e confirme a decisão mais recente no
[registro](lvfi-decision-register.md). Não infira ID, task ou autorização.

## Baseline integrado

- `main` / `origin/main`: `88d7ab486f007d946a053adba4a8ab552b78ee35`,
  merge do PR #26.
- Última task de produto concluída: `LVFI-APP-012`, commit
  `0bec8682912ebfd6c2e597dbda56b6edd34555bd`, PR #26 e merge
  `88d7ab486f007d946a053adba4a8ab552b78ee35`.
- Última task institucional concluída: `R21-GOV-002`.
- Pricing Engine `1.0.1`; distribuição `1.1.1`; Método 1 `1.0.0`; schema 1.
- APP-012 validou 116 testes de backend PostgreSQL isolado/100% de cobertura;
  lint, typecheck, 9 testes e build do frontend, além do smoke frontend → API →
  PostgreSQL isolado.

## Task ativa

Não há task ativa. `LVFI-APP-012 — Fundação Operacional de Dados` foi concluída,
publicada, integrada e encerrada institucionalmente em 2026-09-06: commit
`0bec8682912ebfd6c2e597dbda56b6edd34555bd`, PR #26 e merge
`88d7ab486f007d946a053adba4a8ab552b78ee35`. Ela acrescentou prévia/confirmação
de importação, partidas futuras e revisões estatísticas auditáveis, sem alterar
o Pricing Engine, Método 1, seus schemas, hashes, fixtures ou fórmulas.

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

O Graphify foi reconstruído em 2026-09-06 no modo `code-only`, com 1.078 nós e
2.998 relações. A varredura dos artefatos principais não encontrou caminhos
pessoais, arquivos privados ou padrões de credenciais. Ele permanece somente um
índice; confirme originais quando for insuficiente.

Gate atual: perfil `docs`, seguido de `git diff --check`, revisão de escopo e
varredura de segredos. Publicação usa autorização e fluxo próprios.

**Ação imediata:** o Product Owner deve nomear e autorizar uma única task
posterior; nenhuma sucessora está autorizada até essa decisão.
