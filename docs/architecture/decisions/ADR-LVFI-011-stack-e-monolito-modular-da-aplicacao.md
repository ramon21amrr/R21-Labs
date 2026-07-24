# ADR-LVFI-011 — Stack e monólito modular da aplicação

## Status

Aprovada

## Contexto

O LVFI precisa evoluir do núcleo Python já concluído para dados, workflow, interface e operação, mantendo baixo custo e evitando complexidade prematura.

## Decisão

Adotar monólito modular com frontend Next.js/TypeScript, backend e camada de aplicação Python, API FastAPI, PostgreSQL como persistência principal, worker Python para jobs e armazenamento de objetos compatível com S3. A implantação inicial usará serviços gerenciados de baixo custo, sem fornecedor estruturalmente obrigatório. Web, API e worker serão processos coordenados; não serão microsserviços.

## Alternativas consideradas

Django ofereceria administração e ORM maduros, mas FastAPI é mais proporcional ao primeiro foco em API e integração com o pacote Python. Backend TypeScript duplicaria a fronteira matemática. Microsserviços e broker distribuído acrescentariam deploy e falhas de rede sem escala independente demonstrada.

## Consequências positivas

Compatibilidade direta com o Pricing Engine, tipagem na interface, transações relacionais, operação simples e evolução gradual.

## Riscos e consequências negativas

Processos coordenados exigem disciplina de release; PostgreSQL e S3-compatível ainda exigem decisões operacionais de backup, retenção e custo. Versões de frameworks, provedor de nuvem, cache e broker permanecem futuras.

## Limitações

Este ADR não cria aplicação, schema, migration, infraestrutura, autenticação ou dependência.

## Referências

- [Arquitetura da aplicação](../../products/linha-de-valor-football-intelligence/27-application-architecture.md)
- [Arquitetura de discovery](../../products/linha-de-valor-football-intelligence/07-architecture.md)
- [Company Context](../../company/company-context.md)