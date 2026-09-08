# Estado atual do LVFI

- **Atualizado em:** 2026-09-07
- **Referência integrada:** `4d9c481627c0447e30ef794cf8645b677441c027`
- **Branch de referência:** `main` / `origin/main`, merge do PR #30
- **Última task institucional concluída:** `R21-DEV-003`
- **Última task de produto concluída:** `LVFI-APP-013`
- **Task ativa:** nenhuma
- **Estado da última task:** concluída, publicada, integrada e encerrada
  institucionalmente

## Capacidades disponíveis

Pricing Engine e Método 1 versionados; monólito modular FastAPI; PostgreSQL e
migrations; importação histórica controlada; consultas de competições, temporadas,
times, partidas e estatísticas; amostras determinísticas; execução do Método 1;
execuções persistidas append-only; histórico filtrável; comparação compatível; e
reprodução controlada append-only. A ENG-006 fornece snapshots teóricos de
mercado versionados, a APP-011 acrescenta referência externa manual e comparação
Modelo × Referência, e a APP-012 acrescenta prévia/confirmação idempotente de
importação, partidas futuras e revisões estatísticas auditáveis. `apps/web`
fornece interfaces iniciais sem reproduzir matemática no navegador. A
`LVFI-APP-013` acrescenta uma camada estatística comum somente leitura, com
amostras configuráveis e evidência pública de valores, agregados, frequências,
IDs e completude; a task está publicada e integrada.

## Versões e baseline

- API `0.1.0`; Python `>=3.13,<3.14`; PostgreSQL 16 na validação isolada.
- Distribuição `lvfi-pricing-engine` `1.1.1`; Pricing Engine `1.0.1`.
- Método 1 `1.0.0`; schema canônico do Método 1 `1`.
- APP-011: 103 testes de backend no PostgreSQL isolado com 100% de cobertura;
  frontend com lint, typecheck, testes e build aprovados.
- APP-012: 116 testes de backend no PostgreSQL isolado com 100% de cobertura;
  lint, typecheck, 9 testes e build do frontend aprovados; smoke frontend → API
  → PostgreSQL isolado aprovado.
- Pricing Engine: 554 testes e cobertura integral no último gate aplicável.
- A `R21-GOV-002` é documental e não altera aplicação, contratos, schemas,
  versões, hashes, fixtures ou matemática.

## R21-GOV-002

O Product Owner autorizou em 2026-09-06 o ID `R21-GOV-002` para regularizar o
estado institucional e consolidar o plano mestre. O documento
[39](../products/linha-de-valor-football-intelligence/39-lvfi-master-plan-rebaseline.md)
registra:

- fingerprints dos quatro materiais privados auditados, sem incorporá-los ao Git;
- primeira versão local para um administrador e sete grupos estatísticos;
- importação revisada por Excel/CSV e manutenção manual pela web;
- Métodos 1, 2 e 3 separados, com o Método 1 congelado;
- workflow de análise, Match Center, PDF-resumo, operação local e gates de piloto;
- sequência econômica de tasks, sem autorizar ou inferir uma task sucessora.

A revisão corrigida do XLSM tem SHA-256
`FDCA46B855CC3FA28A34F622D282221F9B8E3EA41B0B6664432D9614D45D3924`.
As 2.694 linhas foram revalidadas sem inconsistência relacional, valor negativo
ou chave duplicada; a divergência anteriormente registrada na linha 2224 foi
resolvida na origem pelo Product Owner.

O Graphify local foi identificado como desatualizado no início da task e
reconstruído em 2026-09-06 no modo local `code-only`: 1.078 nós e 2.998 relações.
A varredura dos artefatos principais não encontrou caminhos pessoais, arquivos
privados ou padrões de credenciais. O grafo permanece apenas um índice; decisões
materiais foram confirmadas nos originais.

O Product Owner confirmou a correção da fonte XLSM, aceitou a entrega e autorizou
a publicação. A unidade documental foi registrada no commit
`1134f683f414cb16af0880386c078ea1d0c3c95c`, publicada pelo PR #24 e integrada
em `main` no merge `7819f3fc1a2c76d196c51584c0027cec65e7a67e`.

## Limitações vigentes

Autenticação, Métodos 2 e 3, configurações, workflow
completo, Match Center, PDF, launcher, backup/restauração, odds automáticas,
oportunidades, Value Tracker e deploy remoto não estão concluídos.

O Método 2 permanece sem ID. `LVFI-ENG-005` permanece reservado ao Método 3 e não
está autorizado como task ativa. Os mercados estatísticos adicionais serão
experimentais até calibração.

## LVFI-APP-012

O Product Owner confirmou em 2026-09-06 a task `LVFI-APP-012 — Fundação
Operacional de Dados`. Ela implementa prévia/confirmação de importações,
partidas futuras e revisões estatísticas auditáveis, sem alterar a matemática
congelada. O contrato completo está no
[documento 40](../products/linha-de-valor-football-intelligence/40-lvfi-app-012-operational-data-foundation.md).

A validação final confirmou, em banco PostgreSQL 16 descartável recém-criado,
migrations até `20260906_07`, prévia/confirmação idempotente, duplicidade,
partida futura, revisão disponível e ausente, e trigger append-only. O banco
`codex_task_lvfi_app_012` foi removido ao final e a instância permanente em
`5432` não foi acessada. A instabilidade observada era o encerramento
intermitente `0xC000013A` do processo da tarefa isolada; o harness agora inicia
a tarefa oficial e aguarda `55432` antes de operar, sem alterar serviço,
cluster, credenciais ou configuração institucional.

O Product Owner autorizou a publicação técnica. A entrega foi registrada no
commit `0bec8682912ebfd6c2e597dbda56b6edd34555bd`, publicada pelo PR #26 e
integrada em `main` pelo merge commit
`88d7ab486f007d946a053adba4a8ab552b78ee35`. O escopo, o Pricing Engine e o
Método 1 permaneceram preservados.

## R21-DEV-003

O Product Owner autorizou em 2026-09-07 a task institucional `R21-DEV-003 —
Orquestração Multiagente do Codex`, baseada em
`242375ac68236ba56307821afc267d871092423f`. O escopo cria um pool seletivo de
nove papéis, a Skill central `r21-multi-agent-orchestration`, documentação,
templates, worktrees com ownership disjunto, handoff compacto e gates.

A simulação documental executou Scout read-only e dois executores em worktrees e
branches temporárias separadas. No checkpoint inicial, os sete arquivos integrados
coincidiram por hash, sem conflito ou retrabalho; a extensão posterior do Lead
explica a medição final 6/7. A task não altera `apps/`, `packages/`, migrations,
contratos, schemas, hashes, fixtures, versões, matemática ou roadmap funcional do
LVFI.

O Graphify, anterior ao HEAD no início, foi reconstruído localmente em modo
`code-only`: 316 nós e 663 relações. A consulta de código voltou a responder e a
varredura dos artefatos principais não encontrou caminhos pessoais, attachments,
XLSM, `connection.json` ou URLs PostgreSQL com valores.

O Product Owner autorizou publicação e encerramento institucional. A entrega foi
registrada no commit `522bbbfb96e3c9835c5f1e43e8b295c605cc4650`, publicada
pelo PR #28 e integrada em `main` pelo merge commit
`62b3791e55aca8df501943dfe7fef9f6a27e8bd2`. A Skill
`r21-multi-agent-orchestration` está disponível para as próximas tasks aprovadas.

## LVFI-APP-013

O Product Owner autorizou em 2026-09-07 a `LVFI-APP-013 — Camada Estatística
Comum`, baseada em `2aad5b82359ef0cabcadc66ce9e40583ff033175`. A entrega cria
contratos e endpoint reutilizáveis para amostras históricas configuráveis, sem
alterar o Pricing Engine, o Método 1 ou APP-007 a APP-012. O documento de
contrato e aceite está em
[41](../products/linha-de-valor-football-intelligence/41-lvfi-app-013-statistics-layer.md).

O PostgreSQL institucional em `127.0.0.1:55432` validou migrations até
`20260906_07`, 174 testes da API sem skips por indisponibilidade e cobertura de
statements/branches em 100%. Vitest (11), lint, typecheck e build passaram; o
smoke frontend → API → PostgreSQL passou via proxy local. O banco isolado será
removido após o gate. A entrega técnica foi registrada no commit
`4a28bd4d5b3e7b9cfb75c1a94834c078d5e55641`, publicada pelo PR #30 e integrada
em `main` pelo merge commit `4d9c481627c0447e30ef794cf8645b677441c027`.
O encerramento documental confirma que a task está concluída sem iniciar
`LVFI-ENG-005`.

## Próxima sequência oficial

- **Task ativa:** nenhuma.
- **Próxima task funcional sucessora:** nenhuma; não inferir ID ou autorização.
- **Ação imediata:** aguardar o Product Owner nomear e autorizar uma única task
  posterior; `LVFI-ENG-005` continua não autorizada.
