# Mapa de marcos do LVFI

Este mapa separa capacidade entregue de trabalho apenas planejado. A ordem vem
dos documentos originais e das decisões do Product Owner em R21-GOV-001 e
R21-GOV-002.

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
| 12 | Frontend e tela inicial de precificação | Concluído | `LVFI-APP-010`, PR #17, ADR-014 e smoke integrado | Interface inicial disponível |
| 13 | Camada versionada de precificação de mercados | Concluído, publicado, integrado e encerrado institucionalmente | `LVFI-ENG-006`; feature `5cd76cebc5b5bfc25f804f53fe7f315c03fc209d`; PR #20; merge `0d59956283f8efcab4f04e372ffe95cadaab9deb` | Método 1 `1.0.0` e Engine `1.0.1` preservados |
| 14 | Entrada de mercado e comparação modelo versus mercado | Concluído, publicado, integrado e encerrado institucionalmente | `LVFI-APP-011`; feature `8dac389`; PR #22; merge `7ef9e0a7a4146637e3121196c6cc743590ddcc4b` | Referência externa manual e comparação auditável disponíveis |
| 15 | Plano mestre e rebaseline | Concluído, publicado, integrado e encerrado institucionalmente | `R21-GOV-002`; PR #24; merge `7819f3fc1a2c76d196c51584c0027cec65e7a67e`; [Documento 39](../products/linha-de-valor-football-intelligence/39-lvfi-master-plan-rebaseline.md) | Estado reconciliado; próxima task ainda exige ID e autorização |
| 16 | Fundação operacional de dados | Concluído, publicado, integrado e encerrado institucionalmente | `LVFI-APP-012`; commit `0bec8682912ebfd6c2e597dbda56b6edd34555bd`; PR #26; merge `88d7ab486f007d946a053adba4a8ab552b78ee35` | Importação revisada e manutenção web de partidas/estatísticas |
| 17 | Camada estatística e métodos restantes | Camada estatística e Métodos 2/3 concluídos, publicados e integrados | [Requisitos](../products/linha-de-valor-football-intelligence/05-requirements.md) e Documento 39 | `LVFI-APP-013`, `LVFI-ENG-005` e `LVFI-ENG-007` concluídas; preservar Método 1 |
| 18 | Configuração, aprovação e snapshots | Configuração e workflow concluídos, publicados, integrados e encerrados institucionalmente | `LVFI-APP-014`, PR #40/merge `8fd593430cdf246932a2225e9f96d38916b05778`; `LVFI-APP-015`, PR #42/merge `f44ad48309980aac89a0c3fda351ec3ac42e8f99` | Configuração versionada, análise aprovada imutável e snapshot reprodutível disponíveis |
| 19 | Match Center e autenticação local | Concluídos, publicados, integrados e encerrados institucionalmente | `LVFI-APP-016`, PR #44/merge `c2d67e5c6c9f4ab273628f9b67ab26d5ea7f40f5`; `LVFI-APP-017`, PR #46/merge `32c2cbd267deea449f9c572fbdc85f56d442b4b0` | Jornada por partida e proteção server-side local disponíveis; preservar `LVFI_EXTERNAL_HTTPS=true` para HTTPS com rewrite interno |
| 20 | PDF-resumo e operação local | Programa aprovado; sem task autorizada | [UX e PDF](../products/linha-de-valor-football-intelligence/09-user-experience-and-pdf.md) e Documento 39 | PDF legível; launcher; backup e restauração ensaiados |
| 21 | Piloto e corte | Programa aprovado; sem task autorizada | Documento 39 e critérios do documento 11 | 20 análises em cinco competições e aceite operacional |
| 22 | Oportunidades | Fora do MVP | [Roadmap](../products/linha-de-valor-football-intelligence/11-mvp-roadmap-and-validation.md) | Mercado auditável e decisão de elegibilidade |
| 23 | Value Tracker, resultados e desempenho | Futuro | [Integração futura](../products/linha-de-valor-football-intelligence/10-value-tracker-integration.md) | Contratos, identidade, evento e CLV decididos |
| 24 | Preparação comercial e lançamento | Futuro | Etapa 4 do documento 11 | Piloto aceito, segurança, suporte, planos e cobrança decididos |

A APP-015 concluiu a parte de configuração, aprovação e snapshots da ordem 18.
A R21-GOV-002 organiza as capacidades 16–21, mas não antecipa oportunidades,
Value Tracker ou comercialização e não autoriza uma task sucessora.

O identificador `LVFI-ENG-004` pertence exclusivamente à correção numérica já
publicada. A reserva histórica desse ID para o Método 2 foi revogada; nenhum novo
ID foi criado para o Método 2.

O próximo passo é o Product Owner nomear e autorizar uma única task posterior.
Nenhum identificador ou escopo sucessor é inferido.
