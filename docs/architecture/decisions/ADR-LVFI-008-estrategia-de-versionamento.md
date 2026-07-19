# ADR-LVFI-008 — Estratégia de versionamento

## Status

Aprovada

## Data

2026-07-19

## Responsáveis e aprovadores

- Decisão e aprovação: Product Owner
- Registro: planejamento aprovado da `LVFI-ENG-001` e formalização na `LVFI-ENG-002-T01`

## Contexto

Pacote, matemática, catálogo e contratos podem mudar de forma independente. Além disso, configurações, dados, amostras e precificações precisam preservar identidade e histórico para reproduzir resultados aprovados.

## Problema

Evitar um único número de versão ambíguo e impedir que alterações posteriores reescrevam a interpretação de cálculos históricos.

## Decisão

- usar SemVer separado para pacote, modelo, catálogo e schemas;
- manter configuração imutável com revisão e hash;
- identificar dados e amostras por IDs estáveis e hashes de conteúdo autorizado;
- manter revisão de precificação monotônica;
- criar nova versão de modelo para qualquer alteração matemática;
- não alterar versão matemática por mudanças exclusivamente visuais;
- vincular cada resultado às versões efetivamente usadas;
- preservar versões substituídas necessárias à auditoria.

## Motivo

Eixos separados deixam claro o que mudou e reduzem releases artificiais de toda a solução. Imutabilidade e revisão monotônica preservam a cadeia de evidências sem impedir evolução.

## Alternativas consideradas

- uma versão única para tudo: simples, porém não identifica a origem real de uma mudança.
- data ou hash como única versão: identifica artefato, mas não comunica compatibilidade.
- editar configuração vigente: reduz registros, mas destrói reprodutibilidade histórica.
- SemVer por contrato mais revisão/hash por conteúdo: escolhida por separar compatibilidade e identidade.

## Consequências positivas

- impacto de mudanças fica rastreável;
- snapshots apontam para dependências precisas;
- evolução visual não contamina a versão matemática;
- configurações e precificações aprovadas permanecem auditáveis.

## Consequências negativas

- mais versões precisam ser registradas em cada resultado;
- exige política de compatibilidade e retenção;
- releases coordenados devem declarar combinações suportadas.

## Riscos

- incrementar apenas o pacote quando a matemática também mudou;
- reutilizar versão de configuração para conteúdo diferente;
- apagar versão antiga ainda referenciada;
- confundir hash de conteúdo com versão de compatibilidade.

## Relação com D-MATH

Sustenta todas as decisões `D-MATH-001` a `D-MATH-016`; é diretamente vinculada à identidade exata de `D-MATH-002`, às regras versionadas de `D-MATH-014` e `D-MATH-015` e à imutabilidade de `D-MATH-016`.

## Relação com decisões anteriores

- versionamento de modelos em [Modelos de precificação](../../products/linha-de-valor-football-intelligence/04-pricing-models.md);
- entidades `ModelVersion`, `ConfigurationVersion` e `PricingSnapshot` em [Domínio e modelo de dados](../../products/linha-de-valor-football-intelligence/06-domain-and-data-model.md).

## Impacto sobre Sprints futuras

A `T04` definirá tipos de versão e revisão, a `T11` os incluirá nos contratos e a `T12` no hash. `LVFI-ENG-003` a `005` versionarão cada método independentemente, e integrações futuras deverão preservar as versões recebidas.
