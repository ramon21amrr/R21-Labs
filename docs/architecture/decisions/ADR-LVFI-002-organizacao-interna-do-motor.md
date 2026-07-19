# ADR-LVFI-002 — Organização interna do motor

## Status

Aprovada

## Data

2026-07-19

## Responsáveis e aprovadores

- Decisão e aprovação: Product Owner
- Registro: planejamento aprovado da `LVFI-ENG-001` e formalização na `LVFI-ENG-002-T01`

## Contexto

O motor reúne tipos de domínio, distribuições, regras de mercado, futuros modelos, coordenação e serialização. Essas capacidades evoluem em ritmos diferentes e precisam permanecer testáveis sem uma classe central que acumule todas as responsabilidades.

## Problema

Definir limites internos e uma direção de dependências que impeçam ciclos, acoplamento entre modelos e mercados e concentração de lógica na orquestração.

## Decisão

- separar tipos, validações, distribuições, mercados, modelos, orquestração e serialização;
- usar objetos de domínio preferencialmente imutáveis;
- manter um orquestrador fino, sem fórmulas próprias;
- impedir que mercados conheçam modelos;
- impedir que modelos conheçam mercados;
- manter tipos fundamentais independentes das demais áreas;
- evitar uma classe central monolítica.

## Motivo

As fronteiras permitem validar matemática, liquidação e contratos isoladamente. A orquestração compõe capacidades estáveis, enquanto modelos futuros produzem entradas matemáticas sem dominar regras de mercado.

## Alternativas consideradas

- uma classe `PricingEngine` monolítica: simplifica a primeira chamada, mas mistura validação, cálculo, mercados, estado e serialização.
- módulos organizados por Sprint: espelham o cronograma, não as responsabilidades duradouras.
- módulos por mercado com Poisson e tipos duplicados: reduz compartilhamento explícito e aumenta risco de divergência.
- capacidades separadas com orquestrador fino: escolhida por preservar coesão e direção de dependências.

## Consequências positivas

- testes menores e mais claros;
- menor risco de ciclos e efeitos colaterais;
- modelos e mercados podem evoluir separadamente;
- contratos e serialização ficam auditáveis.

## Consequências negativas

- mais módulos e interfaces internas desde a fundação;
- exige disciplina para não criar camadas sem comportamento real;
- algumas operações atravessarão vários tipos imutáveis.

## Riscos

- fragmentação excessiva em arquivos pequenos sem coesão;
- lógica duplicada entre orquestração e módulos especializados;
- dependências indiretas contornarem a separação entre modelos e mercados.

## Relação com D-MATH

Implementa limites adequados para a cauda (`D-MATH-001`), precisão (`D-MATH-003`), erros (`D-MATH-011`), handicap (`D-MATH-012`) e imutabilidade das precificações (`D-MATH-016`).

## Relação com decisões anteriores

- módulos conceituais de Pricing em [Arquitetura](../../products/linha-de-valor-football-intelligence/07-architecture.md);
- linguagem de domínio em [Domínio e modelo de dados](../../products/linha-de-valor-football-intelligence/06-domain-and-data-model.md).

## Impacto sobre Sprints futuras

A ordem `T03` a `T12` seguirá essas fronteiras. Os Métodos 1, 2 e 3, nas `LVFI-ENG-003` a `005`, serão adicionados na área de modelos sem fazer mercados dependerem deles e sem transformar o orquestrador em classe monolítica.
