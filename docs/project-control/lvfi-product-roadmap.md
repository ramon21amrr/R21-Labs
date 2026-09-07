# Roadmap institucional do produto LVFI

## Norte permanente

`dados → modelo → preço → mercado → oportunidade → resultado → melhoria contínua`

O roadmap consolida decisões existentes; não cria autorização de implementação.
Estados usados: **concluído**, **tecnicamente pronto**, **programa aprovado**,
**planejado**, **dependente de decisão**, **fora do MVP** e **futuro**.

## Jornada consolidada

| Marco | Estado | Objetivo e capacidades | Dependências | Critério de saída | Riscos e auditoria |
| --- | --- | --- | --- | --- | --- |
| Discovery e oráculo | Concluído | Auditar a planilha, congelar fixtures, decisões matemáticas e limites | Materiais legados autorizados | `LVFI-DISC-002`, 14 fixtures, 350/350 comparações e 408/408 validações asiáticas registradas | Cobertura do oráculo é limitada; preservar hashes e evidências privadas |
| Pricing Engine | Concluído | Núcleo matemático puro, mercados, contratos, serialização e hashes | `LVFI-ENG-001/002` e ADRs 001–010 | Engine `1.0.1`, distribuição `1.1.1`, schemas v1 e baselines congeladas | Qualquer mudança exige versão, regressão e auditoria própria |
| Método 1 | Concluído | Amostras, contratos, médias, ajustes, integração, serialização e release | Pricing Engine aceito; `D-M1-001–007` | Método 1 `1.0.0`, schema canônico 1 e cobertura integral | Preservar fórmula, catálogo, versões e hashes |
| Fundação da aplicação | Concluído | Arquitetura, FastAPI, PostgreSQL, importação histórica e consultas | ADRs 011–013 | APP-001 a APP-004 integradas | Autenticação, frontend e deploy ainda ausentes |
| Precificação auditável na aplicação | Concluído | Amostras, execução, persistência append-only, histórico, comparação e reprodução | APP-003/004 e Método 1 | APP-005 a APP-009 integradas; reprodução controlada disponível | A API atual não representa workflow completo de aprovação do MVP |
| Interface utilizável inicial | Concluído | Fundação do frontend e tela inicial de precificação | APP-009; R21-GOV-001 integrada e encerrada institucionalmente | `LVFI-APP-010` integrada pelo PR #17, com smoke frontend → API → PostgreSQL real | Não duplicar matemática no frontend; manter DTOs autorizados |
| Camada versionada de precificação de mercados | Concluído, publicado, integrado e encerrado institucionalmente | Camada pós-Método 1 para taxas imutáveis, com versionamento, snapshot, hashes e persistência/auditoria próprios | Método 1 `1.0.0` e Pricing Engine `1.0.1` preservados; PR #20, merge `0d59956283f8efcab4f04e372ffe95cadaab9deb` | `LVFI-ENG-006` integrada sem alterar Método 1, Engine ou sua matemática | Usar somente capacidades existentes do Engine; preparar Handicap Asiático e Totais para comparação futura |
| Entrada de mercado | Concluído, publicado, integrado e encerrado institucionalmente | Entrada manual de referência e comparação entre modelo e mercado | ENG-006 concluída | `LVFI-APP-011`, PR #22 e merge `7ef9e0a7a4146637e3121196c6cc743590ddcc4b` | Não ampliar para oportunidade automática sem decisão |
| Plano mestre e rebaseline | Concluído, publicado, integrado e encerrado institucionalmente | Reconciliar estado, registrar fingerprints e organizar a primeira versão local | APP-011 encerrada e autorização do Product Owner | `R21-GOV-002`, PR #24, merge `7819f3fc1a2c76d196c51584c0027cec65e7a67e` | Não iniciar código nem inferir task sucessora |
| Fundação operacional de dados | Concluído, publicado, integrado e encerrado institucionalmente | Prévia/confirmação de Excel/CSV, cadastro de partida e revisão estatística auditável | R21-GOV-002 integrada | `LVFI-APP-012`, commit `0bec8682912ebfd6c2e597dbda56b6edd34555bd`, PR #26 e merge `88d7ab486f007d946a053adba4a8ab552b78ee35` | Proveniência e revisão auditável preservadas; ausência não equivale a zero |
| MVP interno completo | Programa aprovado; dividido em tasks futuras | Camada estatística, Métodos 2/3, configurações, revisão/aprovação, snapshot, auditoria, Match Center, PDF-resumo e autenticação local | Fundação operacional de dados e autorizações incrementais | Requisitos e jornada ponta a ponta do documento 39 atendidos | Método 2 sem ID; ENG-005 não autorizada; preservar Método 1 |
| MVP utilizável | Planejado | Operação manual pelo administrador no Brasileirão Série A 2026 | MVP interno, dados reconciliados e UX validada | Usuário conclui importar, selecionar, precificar, revisar, aprovar e gerar PDF | Usabilidade, baixa amostra, rastreabilidade e proteção de conhecimento |
| Relatórios ampliados | Planejado/Futuro | PDF-resumo no MVP; PDF analítico após capacidades correspondentes | Snapshot aprovado, storage e tecnologia de PDF decidida | Legibilidade, rastreabilidade, autorização e retenção validadas | Exposição de conhecimento, paginação e armazenamento |
| Deploy e recuperação | Dependente de decisão | Preparar ambiente, backup e restauração antes de uso real | MVP utilizável, ADRs 011–013 e decisões operacionais | Ambiente aprovado e restauração ensaiada | Disponibilidade, custo, segurança e perda de dados |
| Piloto | Planejado | Operação controlada com backup, restauração e jornadas críticas | MVP utilizável, segurança e deploy | Critérios de piloto e cutover aprovados pelo Product Owner | Recuperação, suporte, dados pessoais e operação |
| Operação de mercado ampliada | Fora do MVP | Provedores de odds, snapshots temporais, margem, EV e comparação além da APP-011 | Piloto e decisões de fornecedor/contrato | Observações auditáveis e comparação validada | Licenciamento, reconciliação, atraso e lock-in |
| Oportunidades | Fora do MVP | Elegibilidade e aprovação de oportunidades sem registrar aposta | Operação de mercado | Contrato e decisão operacional aprovados | Não confundir precificação, oportunidade e aposta |
| Value Tracker, resultados e melhoria | Futuro | Registrar apostas/paperbets, resultados, ROI, yield e CLV; retornar desempenho para análise | Contrato versionado, decisão do evento e dados suficientes | Integração auditada; aprendizado gera proposta de versão | Identidade, duplicidade, CLV e alteração automática de modelos |
| Preparação comercial | Futuro | Multiusuário, planos, limites, cobrança, suporte e controles ampliados | Piloto aceito e critérios comerciais definidos | Readiness comercial e operacional aprovada | Segurança, privacidade, regulação e custo |
| Lançamento e evolução | Futuro | Produto comercial, métricas de adoção/retenção e expansão analítica | Preparação comercial aceita | Release e operação autorizadas | Evitar expansão sem evidência e preservar baixo acoplamento |

A `LVFI-ENG-006` e a `LVFI-APP-011` completaram a camada de mercado manual. Elas
não antecipam oportunidades, Value Tracker, piloto ou comercialização.

## Transição institucional vigente

`LVFI-APP-012` é a última task de produto concluída, publicada e integrada pelo
PR #26 no merge `88d7ab486f007d946a053adba4a8ab552b78ee35`. Nenhuma task
sucessora está autorizada.

## Escopo aprovado do MVP

O MVP aprovado permanece o do
[documento 11](../products/linha-de-valor-football-intelligence/11-mvp-roadmap-and-validation.md):
autenticação básica; cadastros e importação manual; histórico e amostras; três
modelos; mercados iniciais; critérios manuais; aprovação e versionamento;
Match Center; PDF-resumo; auditoria. O que já existe não implica que os itens
restantes estejam autorizados como uma única task.

## Fora do MVP e futuro

Coleta automática de dados/odds, EV e oportunidades automáticas, mercados
avançados, PDF completo, colaboração avançada, cobrança e integração operacional
com Value Tracker continuam fora do MVP. Contratos podem preparar o futuro sem
criar telas vazias, serviços ou integrações antecipadas.

## Decisões que ainda condicionam o caminho

- O Método 2 permanece planejado e sem ID por decisão do Product Owner.
- APP-012 está concluída, publicada, integrada e encerrada institucionalmente.
- A primeira versão local, os sete grupos estatísticos, a entrada manual/revisada,
  o PDF programático e o gate mínimo do piloto estão aprovados pela R21-GOV-002.
- O ID da próxima task, o ID do Método 2, a implementação concreta do
  PDF/autenticação/backup e fornecedores futuros exigem decisões nas respectivas
  tasks.

Fontes: [visão](../products/linha-de-valor-football-intelligence/01-product-vision.md),
[requisitos](../products/linha-de-valor-football-intelligence/05-requirements.md),
[UX/PDF](../products/linha-de-valor-football-intelligence/09-user-experience-and-pdf.md),
[Value Tracker](../products/linha-de-valor-football-intelligence/10-value-tracker-integration.md),
[roadmap do MVP](../products/linha-de-valor-football-intelligence/11-mvp-roadmap-and-validation.md)
e [arquitetura da aplicação](../products/linha-de-valor-football-intelligence/27-application-architecture.md).

O plano consolidado e seus gates estão no
[documento 39](../products/linha-de-valor-football-intelligence/39-lvfi-master-plan-rebaseline.md).
Nenhuma task sucessora é inferida.
