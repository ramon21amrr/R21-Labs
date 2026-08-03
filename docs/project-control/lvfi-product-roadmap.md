# Roadmap institucional do produto LVFI

## Norte permanente

`dados → modelo → preço → mercado → oportunidade → resultado → melhoria contínua`

O roadmap consolida decisões existentes; não cria autorização de implementação.
Estados usados: **concluído**, **aprovado**, **planejado**, **dependente de
decisão**, **fora do MVP** e **futuro**.

## Jornada consolidada

| Marco | Estado | Objetivo e capacidades | Dependências | Critério de saída | Riscos e auditoria |
| --- | --- | --- | --- | --- | --- |
| Discovery e oráculo | Concluído | Auditar a planilha, congelar fixtures, decisões matemáticas e limites | Materiais legados autorizados | `LVFI-DISC-002`, 14 fixtures, 350/350 comparações e 408/408 validações asiáticas registradas | Cobertura do oráculo é limitada; preservar hashes e evidências privadas |
| Pricing Engine | Concluído | Núcleo matemático puro, mercados, contratos, serialização e hashes | `LVFI-ENG-001/002` e ADRs 001–010 | Engine `1.0.1`, distribuição `1.1.1`, schemas v1 e baselines congeladas | Qualquer mudança exige versão, regressão e auditoria própria |
| Método 1 | Concluído | Amostras, contratos, médias, ajustes, integração, serialização e release | Pricing Engine aceito; `D-M1-001–007` | Método 1 `1.0.0`, schema canônico 1 e cobertura integral | Preservar fórmula, catálogo, versões e hashes |
| Fundação da aplicação | Concluído | Arquitetura, FastAPI, PostgreSQL, importação histórica e consultas | ADRs 011–013 | APP-001 a APP-004 integradas | Autenticação, frontend e deploy ainda ausentes |
| Precificação auditável na aplicação | Concluído | Amostras, execução, persistência append-only, histórico, comparação e reprodução | APP-003/004 e Método 1 | APP-005 a APP-009 integradas; reprodução controlada disponível | A API atual não representa workflow completo de aprovação do MVP |
| Interface utilizável inicial | Aprovado | Fundação do frontend e tela inicial de precificação | APP-009 e integração da R21-GOV-001 | Critérios próprios da `LVFI-APP-010`, gates e encerramento institucional | Não duplicar matemática no frontend; manter DTOs autorizados |
| Entrada de mercado | Planejado | Entrada de odds/mercado e comparação entre modelo e mercado | APP-010; detalhamento e aprovação próprios | `LVFI-APP-011` aceita | Não ampliar para oportunidade automática sem decisão; não detalhada nesta governança |
| MVP interno completo | Dependente de decisão | Completar Método 2, Método 3, configurações, revisão/aprovação, snapshot, auditoria, Match Center, PDF-resumo e autenticação básica | APP-010/011 quando aplicáveis; tasks ainda não aprovadas | Requisitos MVP e jornada ponta a ponta do documento 11 atendidos | Método 2 está deliberadamente sem ID; não inferir ordem ou task |
| MVP utilizável | Planejado | Operação manual pelo administrador no Brasileirão Série A 2026 | MVP interno, dados reconciliados e UX validada | Usuário conclui importar, selecionar, precificar, revisar, aprovar e gerar PDF | Usabilidade, baixa amostra, rastreabilidade e proteção de conhecimento |
| Relatórios ampliados | Planejado/Futuro | PDF-resumo no MVP; PDF analítico após capacidades correspondentes | Snapshot aprovado, storage e tecnologia de PDF decidida | Legibilidade, rastreabilidade, autorização e retenção validadas | Exposição de conhecimento, paginação e armazenamento |
| Deploy e recuperação | Dependente de decisão | Preparar ambiente, backup e restauração antes de uso real | MVP utilizável, ADRs 011–013 e decisões operacionais | Ambiente aprovado e restauração ensaiada | Disponibilidade, custo, segurança e perda de dados |
| Piloto | Planejado | Operação controlada com backup, restauração e jornadas críticas | MVP utilizável, segurança e deploy | Critérios de piloto e cutover aprovados pelo Product Owner | Recuperação, suporte, dados pessoais e operação |
| Operação de mercado ampliada | Fora do MVP | Provedores de odds, snapshots temporais, margem, EV e comparação além da APP-011 | Piloto e decisões de fornecedor/contrato | Observações auditáveis e comparação validada | Licenciamento, reconciliação, atraso e lock-in |
| Oportunidades | Fora do MVP | Elegibilidade e aprovação de oportunidades sem registrar aposta | Operação de mercado | Contrato e decisão operacional aprovados | Não confundir precificação, oportunidade e aposta |
| Value Tracker, resultados e melhoria | Futuro | Registrar apostas/paperbets, resultados, ROI, yield e CLV; retornar desempenho para análise | Contrato versionado, decisão do evento e dados suficientes | Integração auditada; aprendizado gera proposta de versão | Identidade, duplicidade, CLV e alteração automática de modelos |
| Preparação comercial | Futuro | Multiusuário, planos, limites, cobrança, suporte e controles ampliados | Piloto aceito e critérios comerciais definidos | Readiness comercial e operacional aprovada | Segurança, privacidade, regulação e custo |
| Lançamento e evolução | Futuro | Produto comercial, métricas de adoção/retenção e expansão analítica | Preparação comercial aceita | Release e operação autorizadas | Evitar expansão sem evidência e preservar baixo acoplamento |

A APP-011 permanece imediatamente após a APP-010 por decisão explícita do Product
Owner. Ela é uma exceção planejada à sequência macro anterior do documento 11 e
não antecipa oportunidades, Value Tracker, piloto ou comercialização.

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
- A APP-011 está planejada, mas não foi detalhada nesta task.
- Tecnologia/escopo do PDF, retenção, backup/recuperação, autenticação, deploy,
  fornecedor de dados/odds, evento do Value Tracker, CLV e critérios do piloto
  exigem decisões próprias nas etapas aplicáveis.

Fontes: [visão](../products/linha-de-valor-football-intelligence/01-product-vision.md),
[requisitos](../products/linha-de-valor-football-intelligence/05-requirements.md),
[UX/PDF](../products/linha-de-valor-football-intelligence/09-user-experience-and-pdf.md),
[Value Tracker](../products/linha-de-valor-football-intelligence/10-value-tracker-integration.md),
[roadmap do MVP](../products/linha-de-valor-football-intelligence/11-mvp-roadmap-and-validation.md)
e [arquitetura da aplicação](../products/linha-de-valor-football-intelligence/27-application-architecture.md).
