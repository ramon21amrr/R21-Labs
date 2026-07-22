# Linha de Valor Football Intelligence

## Status do produto

- **DECISÃO APROVADA:** o Linha de Valor Football Intelligence é o primeiro produto da R21 Labs.
- **DECISÃO APROVADA:** o Value Tracker será um produto posterior, integrado ao Linha de Valor, e não faz parte do MVP atual.
- **DECISÃO APROVADA:** esta pasta registra discovery, auditoria, arquitetura e planejamento técnico; a implementação continua limitada pelos gates e planos aprovados de cada Task.
- **FATO OBSERVADO:** os documentos foram elaborados a partir do contexto institucional, do R21 Development Framework e dos materiais originais em `inputs/linha-de-valor-football-intelligence/`.
- **FATO OBSERVADO:** a `LVFI-DISC-002` foi encerrada com auditoria dinâmica, baseline matemática e evidências privadas preservadas.
- **FATO OBSERVADO:** a `LVFI-ENG-001` foi concluída e seu planejamento foi consolidado no plano técnico do Pricing Engine.
- **FATO OBSERVADO:** a `LVFI-ENG-002` foi concluída no Pricing Engine `1.0.0`, com validação final registrada no documento 14.
- **FATO OBSERVADO:** a `LVFI-ENG-003-T01` planeja documentalmente o Método 1, sem implementar código.
- **GATE:** **NO-GO PARA IMPLEMENTAÇÃO MATEMÁTICA DO MÉTODO 1 E PARA INÍCIO DA T02**, enquanto as sete decisões `M1-PEND-001` a `M1-PEND-007` não forem aprovadas explicitamente.

## Propósito

O Linha de Valor Football Intelligence será uma plataforma web para organizar dados de futebol, analisar partidas, calcular probabilidades e odds justas, projetar linhas e produzir relatórios auditáveis. Seu objetivo não é reproduzir a planilha em uma página web, mas transformar células e fórmulas em regras compreensíveis, versionadas, testadas e reproduzíveis.

O produto deverá preservar o conhecimento de Ramon e a subjetividade controlada do Método 1, mantendo separadas as responsabilidades de dados, cálculos, configurações, interface, relatórios, integrações e auditoria.

## Ordem de autoridade

Quando houver dúvida ou conflito, deve ser respeitada esta ordem:

1. [Company Context da R21 Labs](../../company/company-context.md);
2. [R21 Development Framework](../../development-framework/README.md);
3. plano de discovery aprovado;
4. materiais originais do produto;
5. recomendações técnicas identificadas como tal.

**FATO OBSERVADO:** o Company Context vigente define a Linha de Valor Football Intelligence como o primeiro produto oficial da R21 Labs e posiciona o Value Tracker como produto ou módulo posterior do ecossistema.

## Como interpretar os documentos

As afirmações relevantes usam os seguintes estados:

- **FATO OBSERVADO:** informação verificada nos materiais ou no repositório.
- **DECISÃO APROVADA:** definição autorizada pelo Product Owner.
- **HIPÓTESE:** possibilidade ainda não comprovada.
- **RECOMENDAÇÃO:** caminho sugerido, sujeito a aprovação quando necessário.
- **DECISÃO PENDENTE:** escolha que ainda precisa ser formalizada.
- **RISCO:** condição que pode prejudicar o produto ou a confiabilidade dos resultados.
- **LIMITAÇÃO:** verificação que não pôde ser concluída ou restrição conhecida.

## Índice do discovery

1. [Visão do produto](01-product-vision.md) — problema, público, valor, objetivos, jornadas e princípios.
2. [Estado atual e auditoria da planilha](02-current-state-and-workbook-audit.md) — inventário dos materiais, abas, dados, VBA, PDFs, limitações e riscos observados.
3. [Regras de negócio e catálogo de mercados](03-business-rules-and-market-catalog.md) — amostras, linhas, liquidação, cores, workflow e mercados.
4. [Modelos de precificação](04-pricing-models.md) — Métodos 1, 2 e 3, Poisson, versionamento, exemplos e testes.
5. [Requisitos](05-requirements.md) — requisitos funcionais e não funcionais.
6. [Domínio e modelo preliminar de dados](06-domain-and-data-model.md) — entidades, relações, histórico e rastreabilidade.
7. [Arquitetura](07-architecture.md) — monólito modular, componentes, fluxos, segurança e operação.
8. [Fornecedores de dados e odds](08-data-and-odds-providers.md) — critérios, adaptadores, contingência, conciliação e licenciamento.
9. [Experiência do usuário e PDF](09-user-experience-and-pdf.md) — navegação, central da partida, acessibilidade e relatórios.
10. [Integração futura com o Value Tracker](10-value-tracker-integration.md) — fronteiras, contrato, eventos e prevenção de duplicidades.
11. [MVP, roadmap e validação](11-mvp-roadmap-and-validation.md) — escopo aprovado, etapas futuras, migração, testes, riscos e decisões pendentes.
12. [Auditoria dinâmica e baseline matemático](12-dynamic-audit-and-mathematical-baseline.md) — protocolo executado, VBA, macros, defeitos, qualidade, fixtures, equivalência e decisões `D-MATH` aprovadas.
13. [Plano técnico do Pricing Engine](13-pricing-engine-technical-plan.md) — fronteiras, contratos, política numérica, backlog e gate da `LVFI-ENG-002`.
14. [Validação final do Pricing Engine](14-pricing-engine-final-validation.md) — evidências, API pública, versão `1.0.0` e critérios de integração.
15. [Plano técnico do Método 1](15-method-one-technical-plan.md) — função, fronteiras, arquitetura, integração, segurança e desempenho.
16. [Catálogo de contratos do Método 1](16-method-one-contract-catalog.md) — responsabilidades, campos, invariantes, erros, warnings e versões.
17. [Decisões matemáticas do Método 1](17-method-one-mathematical-decisions.md) — regras aprovadas, fatos observados, recomendações, conflitos e pendências.
18. [Estratégia de testes do Método 1](18-method-one-test-strategy.md) — testes unitários, propriedades, regressão, integração, segurança e desempenho.
19. [Backlog do Método 1](19-method-one-implementation-backlog.md) — Tasks, dependências, critérios de aceite, riscos, testes e versões.
20. [Gate de planejamento do Método 1](20-method-one-planning-gate.md) — condições bloqueadoras e decisão `NO-GO`.

## ADRs do Pricing Engine

- [ADR-LVFI-001 — Estrutura do repositório](../../architecture/decisions/ADR-LVFI-001-estrutura-do-repositorio-do-pricing-engine.md)
- [ADR-LVFI-002 — Organização interna](../../architecture/decisions/ADR-LVFI-002-organizacao-interna-do-motor.md)
- [ADR-LVFI-003 — Representação numérica](../../architecture/decisions/ADR-LVFI-003-representacao-numerica.md)
- [ADR-LVFI-004 — Política de Poisson e cauda](../../architecture/decisions/ADR-LVFI-004-politica-de-poisson-e-cauda.md)
- [ADR-LVFI-005 — Handicap asiático](../../architecture/decisions/ADR-LVFI-005-handicap-asiatico.md)
- [ADR-LVFI-006 — Erros e alertas tipados](../../architecture/decisions/ADR-LVFI-006-erros-e-alertas-tipados.md)
- [ADR-LVFI-007 — Serialização e hashes](../../architecture/decisions/ADR-LVFI-007-serializacao-e-hashes.md)
- [ADR-LVFI-008 — Estratégia de versionamento](../../architecture/decisions/ADR-LVFI-008-estrategia-de-versionamento.md)
- [ADR-LVFI-009 — Estratégia de fixtures](../../architecture/decisions/ADR-LVFI-009-estrategia-de-fixtures.md)
- [ADR-LVFI-010 — Ferramentas e dependências](../../architecture/decisions/ADR-LVFI-010-ferramentas-e-dependencias.md)

## Síntese das decisões vigentes

- O MVP começará pelo Brasileirão Série A 2026.
- O XLSM será um oráculo de validação, não um componente da aplicação.
- Os três métodos serão versionados e cada precificação aprovada será imutável.
- As decisões matemáticas `D-MATH-001` a `D-MATH-016` orientam o planejamento do Pricing Engine.
- Cauda probabilística não será descartada nem normalizada silenciosamente; linhas asiáticas serão modeladas em quartos inteiros e liquidadas integralmente.
- O MVP cobrirá resultado, dupla chance, ambas marcam, totais de gols e handicap asiático.
- A arquitetura inicial será um monólito modular, sem microsserviços.
- O sistema começará com um administrador, mas evitará barreiras desnecessárias à comercialização futura.
- Integrações automáticas com futebol, odds e Value Tracker permanecerão fora do MVP.

## Limites desta documentação

- **LIMITAÇÃO:** a baseline reproduz o comportamento observado nos fixtures; não certifica a planilha em todos os cenários.
- **LIMITAÇÃO:** a procedência dos registros históricos não está completa no XLSM.
- **LIMITAÇÃO:** fornecedores não foram selecionados ou contratados; o documento correspondente define critérios e processo de avaliação.
- **LIMITAÇÃO:** o Pricing Engine `1.0.0` está concluído, mas o Método 1 permanece em `NO-GO` até aprovação explícita das decisões matemáticas pendentes; Métodos 2 e 3 e as aplicações permanecem fora do escopo.

O encerramento técnico, as limitações remanescentes e a referência ao arquivo privado estão em [Auditoria dinâmica e baseline matemático](12-dynamic-audit-and-mathematical-baseline.md).
