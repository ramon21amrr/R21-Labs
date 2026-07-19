# ADR-LVFI-003 — Representação numérica

## Status

Aprovada

## Data

2026-07-19

## Responsáveis e aprovadores

- Decisão e aprovação: Product Owner
- Registro: planejamento aprovado da `LVFI-ENG-001` e formalização na `LVFI-ENG-002-T01`

## Contexto

O motor precisa reproduzir cálculos com precisão suficiente, representar linhas asiáticas sem ambiguidade decimal e tornar erros numéricos observáveis. As decisões matemáticas já aprovaram `binary64/double`, tolerâncias explícitas e arredondamento somente na apresentação.

## Problema

Escolher representações e regras operacionais que preservem determinismo, evitem estados não finitos e não escondam desvios por arredondamento, clamp ou normalização.

## Decisão

- usar `binary64/float` nos cálculos;
- representar linhas asiáticas como números inteiros de quartos;
- usar `math.fsum` em somas numericamente relevantes;
- rejeitar valores não finitos nas fronteiras;
- proibir normalização, clamp ou correção silenciosa;
- arredondar somente na camada de apresentação;
- não usar `Decimal` no núcleo inicial.

## Motivo

`float` corresponde à precisão já aprovada e possui suporte direto na biblioteca padrão. Quartos inteiros tornam exatas a identidade, ordenação e decomposição das linhas. Regras explícitas de soma e validação tornam desvios auditáveis.

## Alternativas consideradas

- `Decimal` em todo o núcleo: melhora controle decimal, mas não corresponde à baseline `binary64`, aumenta custo e exige política adicional de contexto.
- racionais exatos: úteis para linhas, mas inadequados como representação geral das funções probabilísticas.
- floats também para linhas: simples na superfície, porém introduz comparação aproximada onde a identidade deve ser exata.
- `float` para matemática e inteiros de quartos para linhas: escolhida por corresponder às decisões vigentes.

## Consequências positivas

- alinhamento com `D-MATH-003` e com a baseline;
- linhas, componentes e catálogo comparados por igualdade exata;
- soma relevante mais estável com `math.fsum`;
- falhas numéricas permanecem explícitas.

## Consequências negativas

- resultados decimais não são exatos em base 10;
- serialização canônica precisa preservar a representação binária;
- consumidores não podem inferir precisão a partir do valor exibido.

## Riscos

- comparação direta inadequada entre resultados probabilísticos;
- arredondamento acidental antes do fim do cálculo;
- vazamento de `NaN` ou infinito a partir de divisões e entradas inválidas.

## Relação com D-MATH

Formaliza `D-MATH-002`, `D-MATH-003`, `D-MATH-004` e `D-MATH-006`; sustenta as validações de pesos e multiplicadores de `D-MATH-014` e `D-MATH-015`.

## Relação com decisões anteriores

- política numérica em [Modelos de precificação](../../products/linha-de-valor-football-intelligence/04-pricing-models.md);
- requisitos `RNF-002`, `RNF-003`, `RNF-005` e `RNF-006` em [Requisitos](../../products/linha-de-valor-football-intelligence/05-requirements.md).

## Impacto sobre Sprints futuras

A `T03` centralizará validação e tolerâncias; `T04` criará os value objects; `T06` a `T10` aplicarão a política aos cálculos; `T12` serializará floats por `float.hex()`. Camadas futuras de apresentação poderão avaliar `Decimal` sem alterar o núcleo.
