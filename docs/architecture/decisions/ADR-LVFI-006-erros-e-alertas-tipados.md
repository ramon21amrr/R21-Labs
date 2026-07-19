# ADR-LVFI-006 — Erros e alertas tipados

## Status

Aprovada

## Data

2026-07-19

## Responsáveis e aprovadores

- Decisão e aprovação: Product Owner
- Registro: planejamento aprovado da `LVFI-ENG-001` e formalização na `LVFI-ENG-002-T01`

## Contexto

O legado converte diversas falhas em vazio e pode coagir vazios para zero. O produto precisa distinguir falha de cálculo, baixa confiança e condições que bloqueiam cálculo, aprovação ou publicação.

## Problema

Definir um contrato estável para falhas e alertas sem expor exceções internas como protocolo de domínio nem permitir sentinelas numéricas inválidas.

## Decisão

- adotar `CalculationError` e `CalculationWarning`;
- definir `ErrorCode` estável e versionado;
- manter flags separadas para bloqueio de cálculo, aprovação e publicação;
- nunca converter falha crítica em vazio, zero, `NaN` ou infinito;
- permitir exceções internas para erros de programação, sem torná-las contrato final do domínio;
- incluir contexto seguro suficiente para localizar campo ou etapa, sem dados privados desnecessários.

## Motivo

Objetos tipados permitem que o chamador trate o domínio de forma explícita e que a mesma condição possua impacto diferente no cálculo, aprovação e publicação. Exceções continuam reservadas a invariantes rompidos e erros de programação.

## Alternativas consideradas

- lançar exceção para toda condição: mistura fluxo de domínio com falhas inesperadas.
- retornar `None`, zero ou lista vazia: perde causa e pode produzir preço enganoso.
- retornar strings livres: dificulta compatibilidade, tradução e automação.
- usar apenas nível “erro/aviso”: não representa gates distintos.
- tipos, códigos e flags separados: escolhida por tornar o workflow explícito.

## Consequências positivas

- falhas são auditáveis e testáveis;
- consumidores não dependem do texto da mensagem;
- gates de cálculo, aprovação e publicação ficam independentes;
- valores inválidos não contaminam resultados.

## Consequências negativas

- exige catálogo e compatibilidade de códigos;
- contratos ficam mais extensos;
- novos casos precisam de classificação consciente.

## Riscos

- proliferação de códigos equivalentes;
- mensagem revelar entradas ou contexto proprietário;
- captura excessiva converter erro de programação em erro de domínio;
- consumidor ignorar flags bloqueadoras.

## Relação com D-MATH

Formaliza `D-MATH-011` e dá suporte aos bloqueios e alertas de `D-MATH-006`, `D-MATH-007`, `D-MATH-010`, `D-MATH-014` e `D-MATH-015`.

## Relação com decisões anteriores

- requisitos `RF-065`, `RF-077` e estados de amostra em [Requisitos](../../products/linha-de-valor-football-intelligence/05-requirements.md);
- defeitos de erro silencioso em [Auditoria dinâmica](../../products/linha-de-valor-football-intelligence/12-dynamic-audit-and-mathematical-baseline.md).

## Impacto sobre Sprints futuras

A `T03` definirá a base e o catálogo inicial, e todas as Tasks posteriores os reutilizarão. Os Métodos 1, 2 e 3 adicionarão códigos específicos sem alterar a semântica das flags existentes.
