# Handoff de sessão do LVFI

## Identidade e autoridade

Ramon é o Product Owner e usuário administrador inicial do LVFI. Git e documentos
versionados são a memória oficial. Antes de qualquer task, leia
[current-state](lvfi-current-state.md), valide
[project-state](lvfi-project-state.yaml), consulte o
[task registry](lvfi-task-registry.md) e confirme a decisão mais recente no
[registro](lvfi-decision-register.md). Não infira ID, task ou autorização.

## Baseline integrado

- `main` / `origin/main`: `7552e73091f7e9f639873b259ebbb2b33ca74ed0`,
  merge do PR #23.
- Última task de produto concluída: `LVFI-APP-011`, feature `8dac389`, PR #22,
  merge `7ef9e0a7a4146637e3121196c6cc743590ddcc4b`.
- Última task institucional concluída: `R21-GOV-001`.
- Pricing Engine `1.0.1`; distribuição `1.1.1`; Método 1 `1.0.0`; schema 1.
- APP-011 validou 103 testes de backend/100% de cobertura e frontend com lint,
  typecheck, testes e build.

## Task ativa

`R21-GOV-002 — Plano mestre e rebaseline do LVFI` foi autorizada pelo Product
Owner em 2026-09-06.

- Branch: `codex/r21-gov-002-lvfi-master-plan`.
- Base: `7552e73091f7e9f639873b259ebbb2b33ca74ed0`.
- Escopo: documentação e continuidade; sem alteração de código, banco, contratos,
  schemas, hashes, fixtures, versões ou matemática.
- Estado: aceita pelo Product Owner; commit local autorizado; push, PR e merge
  não autorizados.
- Documento principal: [Plano mestre e rebaseline](../products/linha-de-valor-football-intelligence/39-lvfi-master-plan-rebaseline.md).

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

**Ação imediata:** criar o commit local autorizado e aguardar autorização
explícita para o push da branch. PR e merge são ações posteriores e separadas. Só
após a publicação deverá ser nomeada uma task da fundação operacional de dados;
nenhuma sucessora está autorizada.
