# ADR-LVFI-012 — Fronteira da aplicação com o Pricing Engine

## Status

Aprovada

## Contexto

O Pricing Engine `1.0.0` e o Método 1 `1.0.0` são pacotes Python puros, determinísticos e auditáveis, com schemas e hashes canônicos aprovados.

## Decisão

A API e o worker chamarão `run_method_one` localmente, usando contratos imutáveis formados a partir de dados normalizados, amostras materializadas e configuração resolvida. A aplicação resolve casos de uso, autorização e persistência; o motor não conhece HTTP, banco, fornecedores, PDF, usuários ou interface. O backend e o frontend não duplicarão regras matemáticas. Cada execução persistirá versões, schemas, amostra, configuração e hashes de entrada, configuração e resultado, separando-os dos metadados operacionais. A web receberá somente DTOs autorizados.

## Alternativas consideradas

Um serviço HTTP interno ou subprocesso isolaria o pacote, mas adicionaria rede, operação e falhas sem necessidade atual. Reimplementar cálculos no backend ou frontend reduziria consistência e auditabilidade.

## Consequências positivas

Fonte única de verdade matemática, determinismo preservado, menor superfície de exposição proprietária e evolução de Métodos futuros por contratos versionados.

## Riscos e consequências negativas

A aplicação precisa acompanhar compatibilidade das versões do pacote e tratar explicitamente erros, warnings e blockers. Alterações matemáticas, de schema ou hash continuam exigindo decisões próprias.

## Limitações

Este ADR não altera o Pricing Engine, o Método 1, seus hashes, schemas ou matemática.

## Referências

- [Arquitetura da aplicação](../../products/linha-de-valor-football-intelligence/27-application-architecture.md)
- [Validação final do Método 1](../../products/linha-de-valor-football-intelligence/26-method-one-final-validation.md)
- [ADR-LVFI-007 — Serialização e hashes](ADR-LVFI-007-serializacao-e-hashes.md)