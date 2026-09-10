# Estado atual do LVFI

- **Atualizado em:** 2026-09-10
- **Referência-base estável registrada:** `0b012291e78fb3b20eb887964ebc26d170e0a81c`
- **Branch de referência:** `main`; o SHA corrente de `HEAD`, `main` e
  `origin/main` é sempre resolvido no runtime por Git, não registrado como valor
  corrente neste handoff.
- **Última task institucional concluída:** `R21-GOV-003`
- **Última task de produto concluída:** `LVFI-ENG-007 — Método 2 — Poisson ajustado`.
- **Task ativa:** nenhuma.
- **Estado da última task concluída:** `LVFI-ENG-007` publicada, integrada e
  encerrada institucionalmente; nenhuma task sucessora foi autorizada.

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

Autenticação, configurações, workflow
completo, Match Center, PDF, launcher, backup/restauração, odds automáticas,
oportunidades, Value Tracker e deploy remoto não estão concluídos.

`LVFI-ENG-007` entregou e publicou o núcleo do Método 2. `LVFI-ENG-005`
entregou exclusivamente o Método 3 — frequência observada; os mercados
estatísticos adicionais serão experimentais até calibração.

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
smoke frontend → API → PostgreSQL passou via proxy local. O banco isolado foi
removido após o gate. A entrega técnica foi registrada no commit
`4a28bd4d5b3e7b9cfb75c1a94834c078d5e55641`, publicada pelo PR #30 e integrada
em `main` pelo merge commit `4d9c481627c0447e30ef794cf8645b677441c027`.
O encerramento documental pelo PR #31 confirma que a task está concluída sem
iniciar `LVFI-ENG-005`; o merge commit final é
`6e620f778bed4871961425f639a9b4617e75964c`.

## LVFI-ENG-005

O Product Owner autorizou a publicação da `LVFI-ENG-005 — Método 3 — frequência
observada`. O núcleo, contrato e testes foram publicados no commit
`8f55ecdd62d71d4439a6c082b0571cbbd8f0f709`, PR #33, e integrados por merge
commit `9998319b4fd9920fbe8bc54623155ea7352b0d84`. Os gates finais aprovados
foram documentação, API (190 testes, 100% statements/branches) e Pricing (554
testes, 100% coverage). Método 1 `1.0.0` e Pricing Engine `1.0.1` permaneceram
preservados. O XLSM local divergente não foi usado; a paridade numérica continua
indisponível sem a revisão com fingerprint aprovado.

## R21-GOV-003

O Product Owner autorizou em 2026-09-09 a `R21-GOV-003 — Referência Git não
autorreferencial`, baseada em `0b012291e78fb3b20eb887964ebc26d170e0a81c`. A
task corrige exclusivamente a governança de continuidade: `reference_commit`
passa a significar a base estável aprovada da task, e não o HEAD/merge que ela
mesma criar. Os valores correntes são obtidos no momento da verificação com
`git rev-parse HEAD`, `git rev-parse main` e `git rev-parse origin/main`.

`LVFI-ENG-005` é a última task de produto concluída e não pertence a
`planned_tasks`. Não há task funcional sucessora autorizada; Método 2 não foi
iniciado. Esta task não altera `apps/`, `packages/`, migrations ou roadmap
funcional.

A entrega foi registrada no commit `39a1122b34ff467924962ec4320c0d77c065d0df`,
publicada pelo PR #36 e integrada por merge commit
`c9726fae50bb3b355800e83d1ad9fb8f77216536`. O encerramento institucional é
registrado separadamente para manter o merge histórico fora de
`reference_commit`.

## LVFI-ENG-007

O Product Owner autorizou em 2026-09-09 a `LVFI-ENG-007 — Método 2 — Poisson
ajustado`. O runtime confirmou `HEAD`, `main` e `origin/main` em
`3a9cc087a2ee0ef0ca771b3115131fbd50e5726b` antes da abertura da branch
`codex/lvfi-eng-007-poisson-adjusted`. O Graphify existente era anterior ao
HEAD e foi usado somente como índice parcial; as conclusões foram confirmadas
por busca dirigida nos originais.

O contrato sustentado é apenas o Método 2 conceitual de força relativa ao
campeonato: força ofensiva, fragilidade defensiva adversária e expectativa como
seus produtos com a média correspondente da liga; Poisson padrão converte uma
expectativa `λ` em `P(X=k)=e^(-λ) × λ^k / k!`. A documentação da `APP-013`
cobre amostras e agregados por time, mas não formaliza o agregado da liga para o
Método 2. O fingerprint
aprovado de `METODOS E CALCULOS.docx` é
`A17074F736EE830F03DA5EB3ADAF12BBAA22DA0CFCCB3B3366FEA8AD0429FFD3`; o
conteúdo privado não é versionado e o fingerprint não completa a semântica.

O Product Owner fechou os seletores matemáticos: `N` é 5/10/15/20, séries
parciais usam todos os jogos disponíveis, contexto e referência respeitam
mandante/visitante ou geral, temporada é atual ou atual+passada, o cutoff aceita
somente jogos concluídos anteriores, não há pesos/multiplicadores e o total soma
os dois lambdas. A implementação `method_two_adjusted_poisson` `1.0.0` está no
[documento 43](../products/linha-de-valor-football-intelligence/43-lvfi-eng-007-method-two-adjusted-poisson.md):
o adaptador APP-013 centraliza a seleção de jogos, deriva produção e complemento
em pares da mesma seleção, aplica `match_statistics.match_id IS NOT NULL` e
registra N, contexto, temporadas, cutoff, ordenação, IDs, valores válidos e
ausentes, universo da referência e hashes SHA-256. QA independente confirmou os
quatro P0 após a correção. Método 1, Método 3, APP-013 público e Pricing Engine
permanecem sem alteração. API: 221 testes, quatro skips condicionais e 100% de
statements/branches; Pricing: 554 testes e 100%. A entrega técnica foi registrada
no commit `e4b43b4f7926acef309c16a045f057745f218066`, publicada pelo PR #38 e
integrada por merge commit `842eb955a367d3c1e3e2e45d61057ae8c298475a`.

## Próxima sequência oficial

- **Task ativa:** nenhuma.
- **Próxima ação:** aguardar identificação e autorização explícitas do Product
  Owner para qualquer task posterior.
