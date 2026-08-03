# Mapa de marcos do LVFI

Este mapa separa capacidade entregue de trabalho apenas planejado. A ordem vem
dos documentos originais e da decisão do Product Owner na R21-GOV-001.

| Ordem | Marco | Estado | Evidência principal | Dependência/saída |
| ---: | --- | --- | --- | --- |
| 1 | Discovery e baseline matemática | Concluído | [Documento 12](../products/linha-de-valor-football-intelligence/12-dynamic-audit-and-mathematical-baseline.md) | Oráculo e decisões matemáticas congelados |
| 2 | Pricing Engine | Concluído | [Documento 14](../products/linha-de-valor-football-intelligence/14-pricing-engine-final-validation.md) | Núcleo matemático auditável disponível |
| 3 | Método 1 | Concluído | [Documento 26](../products/linha-de-valor-football-intelligence/26-method-one-final-validation.md) | Método 1 `1.0.0` e schema 1 disponíveis |
| 4 | Estabilidade numérica de totais | Concluído | [Documento 29](../products/linha-de-valor-football-intelligence/29-lvfi-eng-004-total-market-numerical-stability.md), PR #4 | Engine `1.0.1` e distribuição `1.1.1` |
| 5 | Arquitetura da aplicação | Concluído | [Documento 27](../products/linha-de-valor-football-intelligence/27-application-architecture.md), APP-001 | Stack e fronteiras aprovadas |
| 6 | Backend e PostgreSQL | Concluído | [Documento 28](../products/linha-de-valor-football-intelligence/28-backend-database-foundation.md), APP-002 | API, migrations e observabilidade |
| 7 | Partidas e amostras | Concluído | [Documentos 30–32](../products/linha-de-valor-football-intelligence/30-historical-data-model-and-import.md) | Dados históricos, consultas e amostras determinísticas |
| 8 | Execução do Método 1 | Concluído | [Documento 33](../products/linha-de-valor-football-intelligence/33-method-one-application-execution.md), APP-006 | Execução não persistente validada |
| 9 | Execução persistida e auditável | Concluído | [Documento 34](../products/linha-de-valor-football-intelligence/34-auditable-pricing-executions.md), APP-007 | Snapshot de execução append-only |
| 10 | Histórico e comparação | Concluído | [Documento 35](../products/linha-de-valor-football-intelligence/35-pricing-execution-history-and-comparison.md), APP-008 | Leitura filtrável e comparação compatível |
| 11 | Reprodução controlada | Concluído | [Documento 36](../products/linha-de-valor-football-intelligence/36-controlled-pricing-execution-reproduction.md), APP-009 | Reprodução append-only e diferenças auditáveis |
| 12 | Frontend e tela inicial de precificação | Próximo/aprovado | Decisão do Product Owner; `LVFI-APP-010` | Executar somente após integração da R21-GOV-001 |
| 13 | Entrada de mercado e comparação modelo versus mercado | Planejado | Decisão do Product Owner; `LVFI-APP-011` | Depende da APP-010 e plano próprio |
| 14 | Métodos restantes e workflow completo do MVP | Dependente de decisão | [Requisitos](../products/linha-de-valor-football-intelligence/05-requirements.md) | Método 2 sem ID; tasks próprias para Método 3, aprovação e snapshot |
| 15 | Autenticação e segurança de uso | Planejado no MVP | RF-001–004 e RNF-010–014 | Papéis, sessão e proteção server-side validados |
| 16 | Relatórios | Planejado no MVP/futuro | [UX e PDF](../products/linha-de-valor-football-intelligence/09-user-experience-and-pdf.md) | PDF-resumo primeiro; analítico somente depois |
| 17 | Deploy e recuperação | Dependente de decisão | ADRs 011–013 e RNF-030–032 | Ambiente, backup e restauração ensaiados |
| 18 | Piloto | Planejado | Critérios do documento 11 | MVP utilizável e aceite operacional |
| 19 | Oportunidades | Fora do MVP | [Roadmap](../products/linha-de-valor-football-intelligence/11-mvp-roadmap-and-validation.md) | Mercado auditável e decisão de elegibilidade |
| 20 | Value Tracker, resultados e desempenho | Futuro | [Integração futura](../products/linha-de-valor-football-intelligence/10-value-tracker-integration.md) | Contratos, identidade, evento e CLV decididos |
| 21 | Preparação comercial e lançamento | Futuro | Etapa 4 do documento 11 | Piloto aceito, segurança, suporte, planos e cobrança decididos |

A APP-011 permanece na ordem 13 por decisão explícita do Product Owner, mas não
antecipa oportunidades, Value Tracker, piloto ou comercialização.

O identificador `LVFI-ENG-004` pertence exclusivamente à correção numérica já
publicada. A reserva histórica desse ID para o Método 2 foi revogada; nenhum novo
ID foi criado para o Método 2.
