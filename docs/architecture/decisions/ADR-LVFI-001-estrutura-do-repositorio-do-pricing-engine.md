# ADR-LVFI-001 — Estrutura do repositório do Pricing Engine

## Status

Aprovada

## Data

2026-07-19

## Responsáveis e aprovadores

- Decisão e aprovação: Product Owner
- Registro: planejamento aprovado da `LVFI-ENG-001` e formalização na `LVFI-ENG-002-T01`

## Contexto

O Pricing Engine integra o monólito modular, mas precisa manter uma fronteira interna explícita, ser testável isoladamente e não antecipar aplicações ainda inexistentes. O Company Context e o R21 Development Framework proíbem estruturas sem uso real e complexidade prematura.

## Problema

Definir onde o pacote residirá e impedir que a fundação do motor seja confundida com a criação antecipada de back-end, front-end ou microsserviço.

## Decisão

- localizar o motor em `packages/pricing-engine/`;
- usar o namespace Python `lvfi_pricing`;
- criar `apps/` apenas quando aplicações reais forem iniciadas;
- não criar microsserviço;
- não criar `apps/web`, `apps/backend` ou equivalentes nesta Sprint;
- manter o pacote como parte versionada do monólito modular, com testes e documentação próprios.

## Motivo

Um pacote interno isolado oferece fronteira clara e validação independente sem introduzir rede, implantação separada ou diretórios de aplicações hipotéticas.

## Alternativas consideradas

- `src/` e `tests/` na raiz: mistura o primeiro pacote com a raiz do repositório e dificulta acomodar aplicações reais no futuro.
- `backend/src/`: pressupõe a existência de um back-end antes da escolha e implementação dessa aplicação.
- pacote isolado em `packages/`: escolhido por expressar a fronteira real sem antecipar processos ou serviços.

## Consequências positivas

- isolamento explícito do núcleo matemático;
- testes e versionamento do pacote sem dependência da aplicação;
- caminho simples para consumo interno futuro;
- aderência ao monólito modular e à evolução incremental.

## Consequências negativas

- exige configuração de build e descoberta de testes dentro de um subdiretório;
- consumidores futuros precisarão declarar de forma explícita a dependência interna;
- a separação física não elimina, por si só, acoplamento indevido.

## Riscos

- transformar `packages/` em depósito de abstrações sem consumidor real;
- tratar o pacote como microsserviço de forma informal;
- criar aplicações vazias para “completar” uma estrutura planejada.

## Relação com D-MATH

A fronteira isolada protege a reprodutibilidade e a imutabilidade exigidas por `D-MATH-001` a `D-MATH-016`, especialmente `D-MATH-016`, ao separar o cálculo de estado externo e de apresentação.

## Relação com decisões anteriores

- monólito modular aprovado em [Arquitetura](../../products/linha-de-valor-football-intelligence/07-architecture.md);
- requisitos `RNF-060` a `RNF-063` em [Requisitos](../../products/linha-de-valor-football-intelligence/05-requirements.md).

## Impacto sobre Sprints futuras

A `LVFI-ENG-002-T02` criará a fundação aprovada nesse local. `LVFI-ENG-003` a `LVFI-ENG-005` consumirão o mesmo pacote para os Métodos 1, 2 e 3. Aplicações futuras deverão depender do pacote, sem mover lógica matemática para seus próprios módulos.
