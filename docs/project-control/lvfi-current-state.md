# Estado atual do LVFI

- **Atualizado em:** 2026-09-06
- **Referência integrada:** `7552e73091f7e9f639873b259ebbb2b33ca74ed0`
- **Branch de referência:** `main` / `origin/main`, merge do PR #23
- **Última task institucional concluída:** `R21-GOV-001`
- **Última task de produto concluída:** `LVFI-APP-011`
- **Task ativa:** `R21-GOV-002 — Plano mestre e rebaseline do LVFI`
- **Branch ativa:** `codex/r21-gov-002-lvfi-master-plan`
- **Estado da task:** aceita pelo Product Owner; commit local autorizado;
  publicação pendente

## Capacidades disponíveis

Pricing Engine e Método 1 versionados; monólito modular FastAPI; PostgreSQL e
migrations; importação histórica controlada; consultas de competições, temporadas,
times, partidas e estatísticas; amostras determinísticas; execução do Método 1;
execuções persistidas append-only; histórico filtrável; comparação compatível; e
reprodução controlada append-only. A ENG-006 fornece snapshots teóricos de
mercado versionados e a APP-011 acrescenta referência externa manual e comparação
Modelo × Referência. `apps/web` fornece a interface inicial sem reproduzir
matemática no navegador.

## Versões e baseline

- API `0.1.0`; Python `>=3.13,<3.14`; PostgreSQL 16 na validação isolada.
- Distribuição `lvfi-pricing-engine` `1.1.1`; Pricing Engine `1.0.1`.
- Método 1 `1.0.0`; schema canônico do Método 1 `1`.
- APP-011: 103 testes de backend no PostgreSQL isolado com 100% de cobertura;
  frontend com lint, typecheck, testes e build aprovados.
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

Na mesma data, o Product Owner confirmou a correção da fonte XLSM, aceitou a
entrega da `R21-GOV-002` e autorizou o commit local. Push, PR e merge permanecem
sem autorização.

## Limitações vigentes

Autenticação, administração visual de importações, manutenção web de partidas e
estatísticas, amostras generalizadas, Métodos 2 e 3, configurações, workflow
completo, Match Center, PDF, launcher, backup/restauração, odds automáticas,
oportunidades, Value Tracker e deploy remoto não estão concluídos.

O Método 2 permanece sem ID. `LVFI-ENG-005` permanece reservado ao Método 3 e não
está autorizado como task ativa. Os mercados estatísticos adicionais serão
experimentais até calibração.

## Próxima sequência oficial

- **Task em revisão:** `R21-GOV-002`, baseada em
  `7552e73091f7e9f639873b259ebbb2b33ca74ed0`.
- **Próxima task sucessora:** nenhuma; não inferir ID ou autorização.
- **Ação imediata:** após o commit local autorizado, aguardar autorização
  explícita para o push da branch; PR e merge continuam sendo ações separadas.
- **Decisão posterior:** depois da publicação, o Product Owner deverá nomear uma
  única task para a fundação operacional de dados.
