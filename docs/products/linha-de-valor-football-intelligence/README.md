# Linha de Valor Football Intelligence

## Status do produto

- **DECISÃO APROVADA:** o Linha de Valor Football Intelligence é o primeiro produto da R21 Labs.
- **DECISÃO APROVADA:** o Value Tracker será um produto posterior, integrado ao Linha de Valor, e não faz parte do MVP atual.
- **DECISÃO APROVADA:** esta pasta registra exclusivamente a fase de discovery, auditoria e planejamento. Ela não autoriza desenvolvimento.
- **FATO OBSERVADO:** os documentos foram elaborados a partir do contexto institucional, do R21 Development Framework e dos materiais originais em `inputs/linha-de-valor-football-intelligence/`.

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

**DECISÃO APROVADA:** a afirmação ainda existente no Company Context de que o Value Tracker seria o primeiro produto está superada pela decisão mais recente do Product Owner. Sua correção pertence a uma tarefa institucional separada.

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

## Síntese das decisões vigentes

- O MVP começará pelo Brasileirão Série A 2026.
- O XLSM será um oráculo de validação, não um componente da aplicação.
- Os três métodos serão versionados e cada precificação aprovada será imutável.
- O MVP cobrirá resultado, dupla chance, ambas marcam, totais de gols e handicap asiático.
- A arquitetura inicial será um monólito modular, sem microsserviços.
- O sistema começará com um administrador, mas evitará barreiras desnecessárias à comercialização futura.
- Integrações automáticas com futebol, odds e Value Tracker permanecerão fora do MVP.

## Limites desta documentação

- **LIMITAÇÃO:** macros e botões do XLSM não foram executados; a auditoria disponível é estática.
- **LIMITAÇÃO:** o código VBA completo não foi extraído por indisponibilidade da ferramenta de leitura apropriada.
- **LIMITAÇÃO:** o Word foi lido estruturalmente, mas não foi renderizado integralmente por ausência de LibreOffice no ambiente de inspeção.
- **LIMITAÇÃO:** fornecedores não foram selecionados ou contratados; o documento correspondente define critérios e processo de avaliação.

As ações necessárias para eliminar essas limitações estão detalhadas em [Estado atual e auditoria da planilha](02-current-state-and-workbook-audit.md).
