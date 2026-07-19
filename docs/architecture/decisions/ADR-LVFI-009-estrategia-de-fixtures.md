# ADR-LVFI-009 — Estratégia de fixtures

## Status

Aprovada

## Data

2026-07-19

## Responsáveis e aprovadores

- Decisão e aprovação: Product Owner
- Registro: planejamento aprovado da `LVFI-ENG-001` e formalização na `LVFI-ENG-002-T01`

## Contexto

A regressão precisa aproveitar a cobertura da baseline sem expor partidas, dados, fontes, históricos ou artefatos proprietários. Adiar toda preparação de fixtures até o fim impediria desenvolvimento orientado por testes e revisão antecipada de propriedade intelectual.

## Problema

Definir quais fixtures podem entrar no Git, como relacioná-las à cobertura privada e quando preparar o harness de regressão.

## Decisão

- manter a suíte privada completa fora do Git;
- versionar fixtures sanitizadas e minimizadas;
- versionar fixtures inteiramente sintéticas;
- exigir revisão antes de versionar qualquer fixture;
- remover nomes de times, partidas, datas, fontes, caminhos, IDs e históricos privados;
- usar `JR-01` a `JR-14` apenas como identificadores de cobertura;
- preparar as fixtures e o harness inicial antes dos cálculos principais;
- separar expectativas de regressão legada das regras normativas futuras;
- ampliar a suíte segura durante a Sprint quando necessário.

## Motivo

A estratégia preserva a propriedade intelectual e ainda permite testes locais e em CI. Antecipar a fundação das fixtures revela cedo divergências, lacunas de contrato e riscos de vazamento.

## Alternativas consideradas

- copiar a suíte privada completa para o Git: oferece cobertura imediata, mas viola confidencialidade e minimização.
- não manter fixtures no repositório: protege dados, porém reduz reprodutibilidade de CI e revisão.
- preparar fixtures somente no final: atrasa TDD e detecção de divergências.
- somente dados sintéticos: seguros, mas podem não representar todos os riscos descobertos na baseline.
- combinação de sintéticos e sanitizados minimizados: escolhida por equilibrar segurança e cobertura.

## Consequências positivas

- CI pode validar comportamento sem acesso ao arquivo privado;
- revisão de propriedade intelectual ocorre antes dos cálculos;
- regressão e regra normativa ficam distinguíveis;
- novos casos podem ser minimizados progressivamente.

## Consequências negativas

- sanitização e minimização exigem trabalho e revisão;
- parte da regressão completa continuará fora do CI público;
- dados sintéticos podem deixar de reproduzir interações relevantes.

## Riscos

- reidentificação por combinação de valores ou metadados;
- sanitização alterar o comportamento que deveria cobrir;
- expectativa legada truncada ser tratada como regra futura;
- referência `JR` ser acompanhada de detalhes privados desnecessários.

## Relação com D-MATH

As fixtures verificam especialmente `D-MATH-001`, `D-MATH-002`, `D-MATH-005` a `D-MATH-013` e `D-MATH-016`, sem copiar os valores privados que originaram a baseline.

## Relação com decisões anteriores

- cobertura `JR-01` a `JR-14` em [MVP, roadmap e validação](../../products/linha-de-valor-football-intelligence/11-mvp-roadmap-and-validation.md);
- métricas agregadas e limites em [Auditoria dinâmica](../../products/linha-de-valor-football-intelligence/12-dynamic-audit-and-mathematical-baseline.md).

## Impacto sobre Sprints futuras

A `T05` passa a ocorrer antes de `T06` e cria o harness mínimo. Todas as Tasks matemáticas deverão adicionar ou adaptar casos seguros. `LVFI-ENG-003` a `005` usarão o mesmo processo para fixtures específicas dos modelos.
