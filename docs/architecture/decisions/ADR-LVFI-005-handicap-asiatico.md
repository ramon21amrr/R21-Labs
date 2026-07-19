# ADR-LVFI-005 — Handicap asiático

## Status

Aprovada

## Data

2026-07-19

## Responsáveis e aprovadores

- Decisão e aprovação: Product Owner
- Registro: planejamento aprovado da `LVFI-ENG-001` e formalização na `LVFI-ENG-002-T01`

## Contexto

O handicap asiático possui linhas inteiras, meias e de quarto, com efeitos financeiros diferentes. A baseline validou a decomposição canônica em 408 casos agregados, e `D-MATH-003`, `D-MATH-005` e `D-MATH-012` fixaram a representação, liquidação e linha principal.

## Problema

Evitar regras informais por linha, preservar liquidações parciais e definir uma seleção determinística da linha principal.

## Decisão

- representar linhas como inteiros de quartos;
- decompor linhas de quarto nas duas linhas adjacentes;
- dividir a stake igualmente entre os componentes;
- preservar vitória integral, meia vitória, reembolso, meia derrota e derrota integral;
- calcular a odd justa a partir de vitórias e perdas equivalentes;
- excluir pushes do preço, mantendo-os no resultado auditável;
- escolher a linha principal cuja odd justa estiver mais próxima de `2,00`;
- em empate, escolher a linha mais próxima de zero e depois aplicar ordem simétrica canônica;
- preservar todas as linhas calculadas.

## Motivo

A decomposição elimina tabelas especiais ambíguas e deriva todos os estados a partir da mesma regra. A seleção por distância de `2,00` expressa equilíbrio de preço, e os desempates tornam o resultado reproduzível e simétrico.

## Alternativas consideradas

- tabela manual por linha e margem: extensa, difícil de revisar e propensa a divergência entre lados.
- aproximar linhas de quarto como meias linhas: perde meia vitória, meia derrota e reembolso parcial.
- calcular odd como inverso da probabilidade de vitória: trata incorretamente perdas parciais e pushes.
- retornar apenas a linha principal: elimina evidência necessária à auditoria.
- decomposição canônica e equivalentes: escolhida por corresponder à regra aprovada.

## Consequências positivas

- uma única semântica cobre todas as linhas;
- simetria verificável entre mandante e visitante;
- odds incorporam liquidação integral e parcial;
- resultado mantém explicação por componente.

## Consequências negativas

- contratos precisam carregar mais estados e probabilidades;
- a odd pode ser indefinida quando não há vitória equivalente;
- o desempate canônico precisa ser versionado e testado.

## Riscos

- erro de sinal ao mudar a perspectiva da seleção;
- decomposição incorreta de linha negativa;
- excluir push também da auditoria;
- arredondar odds antes de selecionar a linha principal.

## Relação com D-MATH

Implementa diretamente `D-MATH-003`, `D-MATH-005` e `D-MATH-012`; usa as tolerâncias de `D-MATH-002` e preserva valores brutos conforme `D-MATH-004`.

## Relação com decisões anteriores

- catálogo e fórmula de odd justa em [Regras de negócio](../../products/linha-de-valor-football-intelligence/03-business-rules-and-market-catalog.md);
- resultados agregados da baseline em [Auditoria dinâmica](../../products/linha-de-valor-football-intelligence/12-dynamic-audit-and-mathematical-baseline.md).

## Impacto sobre Sprints futuras

A `T09` implementará liquidação, a `T10` precificação e linha principal e a `T11` integrará os resultados ao contrato. Métodos futuros usarão essa capacidade sem reimplementar regras asiáticas.
