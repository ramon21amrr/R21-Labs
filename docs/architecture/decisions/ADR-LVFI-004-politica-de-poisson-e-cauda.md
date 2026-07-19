# ADR-LVFI-004 — Política de Poisson e cauda

## Status

Aprovada

## Data

2026-07-19

## Responsáveis e aprovadores

- Decisão e aprovação: Product Owner
- Registro: planejamento aprovado da `LVFI-ENG-001` e formalização na `LVFI-ENG-002-T01`

## Contexto

A matriz legada materializa placares somente de `0` a `6` para cada time e pode omitir massa relevante. `D-MATH-001` e `D-MATH-006` aprovaram cálculo integral ou adaptativo, residual observável e bloqueio para diferença não explicada.

## Problema

Definir uma política concreta para construir distribuições Poisson e impedir que um recorte de matriz usado em auditoria altere os mercados calculados.

## Decisão

- usar suporte adaptativo;
- adotar residual máximo alvo de `1e-14` por distribuição;
- iniciar o suporte em `0` e materializá-lo inicialmente até `10`;
- ampliar o suporte até convergência;
- aplicar limite técnico inicial de segurança de `1.000`;
- retornar erro tipado se a distribuição não convergir antes do limite;
- usar matriz apenas para auditoria ou visualização;
- fazer mercados analíticos independentes de matriz recortada;
- registrar limite usado, soma e massa residual;
- nunca descartar ou normalizar silenciosamente a cauda.

Esta decisão cria divergência deliberada e aprovada em relação à matriz legada `0–6`.

## Motivo

O suporte adaptativo mantém a implementação na biblioteca padrão, torna o erro de truncamento explícito e atende a lambdas distintas sem escolher um recorte fixo que seja simultaneamente caro para casos simples e insuficiente para casos extremos.

## Alternativas consideradas

- manter matriz fixa `0–6`: preserva o legado, mas viola a decisão de não descartar massa.
- matriz fixa maior: reduz o erro em casos comuns, mas continua sem garantia para todo o domínio.
- renormalizar a matriz recortada: oculta a cauda e altera as probabilidades relativas.
- fórmulas exclusivamente fechadas por mercado: úteis onde existirem, mas não substituem uma distribuição auditável comum.
- suporte adaptativo com residual explícito: escolhido por combinar correção, auditabilidade e simplicidade.

## Consequências positivas

- controle verificável da massa residual;
- comportamento proporcional ao lambda;
- mercados não herdam o recorte de visualização;
- divergência do legado fica explícita e testável.

## Consequências negativas

- tempo e memória variam conforme o lambda;
- exige erro e limite para entradas patológicas;
- comparações com o legado precisam distinguir regressão de regra normativa.

## Riscos

- recorrência instável ou underflow em extremos;
- interpretação incorreta do residual conjunto de duas distribuições;
- consumidor usar a matriz auditável como fonte normativa de mercado.

## Relação com D-MATH

Formaliza `D-MATH-001` e `D-MATH-006` e aplica a precisão e ausência de arredondamento de `D-MATH-003` e `D-MATH-004`.

## Relação com decisões anteriores

- seção de cauda em [Modelos de precificação](../../products/linha-de-valor-football-intelligence/04-pricing-models.md);
- baseline e divergência aprovada em [Auditoria dinâmica](../../products/linha-de-valor-football-intelligence/12-dynamic-audit-and-mathematical-baseline.md).

## Impacto sobre Sprints futuras

A `T06` implementará a distribuição; `T07` construirá diferença de gols e matriz auditável; `T08` a `T10` consumirão as distribuições sem depender da matriz. Os Métodos 1 e 2 futuros fornecerão lambdas ao mesmo contrato.
