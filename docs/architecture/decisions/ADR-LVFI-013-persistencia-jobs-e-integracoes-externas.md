# ADR-LVFI-013 — Persistência, jobs e isolamento de fornecedores

## Status

Aprovada

## Contexto

Importações, relatórios, tarefas agendadas e fornecedores futuros precisam ser rastreáveis sem acoplar o domínio ou o Pricing Engine a payloads externos.

## Decisão

PostgreSQL será a fonte transacional de entidades, versões, auditoria e jobs. Arquivos importados e PDFs ficarão em armazenamento S3-compatível, referenciados por hash e metadados no banco. Jobs serão inicialmente persistidos no PostgreSQL e executados por worker Python, com correlação, chave de idempotência e tentativas limitadas, fora do fluxo HTTP quando demorados. Fornecedores de futebol e odds serão isolados por adaptadores que preservam dados brutos, normalizam, validam e conciliam antes da persistência. A integração futura com Value Tracker usará contrato/outbox versionado e idempotente.

## Alternativas consideradas

Fila distribuída e sincronização direta no domínio foram rejeitadas por custo e acoplamento prematuros. Persistir apenas dados normalizados perderia procedência; armazenar arquivos grandes no banco dificultaria operação.

## Consequências positivas

Transações e auditoria claras, separação entre bruto e normalizado, reprocessamento seguro, portabilidade de fornecedores e evolução assíncrona gradual.

## Riscos e consequências negativas

A fila inicial compartilha capacidade com o banco e exigirá métricas; retenção, deduplicação física, backup/restauração, PDF e broker precisarão de decisões nas Tasks de implementação.

## Limitações

Este ADR não cria tabelas, migrations, jobs, adaptadores, integração externa ou infraestrutura.

## Referências

- [Arquitetura da aplicação](../../products/linha-de-valor-football-intelligence/27-application-architecture.md)
- [Domínio e modelo de dados](../../products/linha-de-valor-football-intelligence/06-domain-and-data-model.md)
- [Fornecedores de dados e odds](../../products/linha-de-valor-football-intelligence/08-data-and-odds-providers.md)
- [Integração futura com Value Tracker](../../products/linha-de-valor-football-intelligence/10-value-tracker-integration.md)