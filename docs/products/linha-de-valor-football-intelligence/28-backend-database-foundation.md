# Fundação do backend e banco — LVFI-APP-002

## Objetivo

Esta task cria a base executável da API do Linha de Valor Football Intelligence: um monólito modular FastAPI com configuração tipada, PostgreSQL assíncrono, migrations, observabilidade e uma fronteira explícita para o Pricing Engine. Não cria entidades de futebol, importação histórica, jobs, autenticação, interface ou endpoint de precificação.

## Arquitetura implementada

O backend fica em `apps/api`, separado em `presentation` (HTTP, middleware e erros), `config` (ambiente tipado), `infrastructure` (PostgreSQL, logs e fronteira do motor), `persistence` (metadata), `domain` (exceções), `alembic` (migrations) e `tests`. Isso atende ao monólito modular do documento 27 e ADRs 011–013. O worker permanece um ponto de extensão sem código vazio, fila ou scheduler.

## Tecnologias e configuração

A base usa CPython 3.13, FastAPI, Uvicorn, SQLAlchemy assíncrono, asyncpg, Alembic e Pydantic Settings, com lock reproduzível em `apps/api/uv.lock`. Copie `apps/api/.env.example` para ambiente local não versionado. A URL obrigatória é PostgreSQL com `postgresql+asyncpg`; valores ausentes ou inválidos falham antes da API iniciar. O exemplo só tem valores locais, sem segredos.

## Banco e migrations

`Database` controla engine, pool, sessão, commit, rollback e encerramento. `GET /ready` executa uma consulta de disponibilidade; falhas retornam 503 sem detalhes internos. A metadata centraliza convenções de nomes.

A revisão `20260724_01` inicia somente a linhagem Alembic. A tabela técnica `alembic_version` é criada e controlada pela ferramenta, portanto não foi criada tabela redundante. Nenhuma entidade de futebol foi antecipada.

Para uso local com PostgreSQL disponível:

```powershell
cd apps/api
uv sync --all-groups --locked
uv run alembic upgrade head
uv run uvicorn lvfi_api.main:create_app --factory
```

PostgreSQL 16 foi validado em servidor real local com role e banco descartáveis. O upgrade até `head`, o downgrade até `base`, o novo upgrade, a readiness, as sessões, o commit e o rollback foram aprovados. No downgrade, a revisão aplicada é removida e permanece somente a tabela técnica vazia controlada pelo Alembic; não há estruturas de domínio nesta task. Os recursos descartáveis e as credenciais temporárias foram removidos ao final.

## Operação

- `GET /health` confirma o processo HTTP, sem acessar o banco.
- `GET /ready` confirma PostgreSQL.
- A documentação OpenAPI está em `/docs`.

Toda requisição propaga `X-Request-ID` quando seguro ou gera UUID. Logs JSON incluem timestamp, nível, logger, ambiente, correlação, método, caminho, duração, status e erro sanitizado. Erros de persistência retornam envelope 503 estável; exceções inesperadas retornam 500 sem stack trace para o cliente.

## Fronteira com Pricing Engine

`infrastructure/pricing_engine.py` importa exclusivamente a fachada pública `lvfi_pricing.models.method_one`. Ele só verifica que `run_method_one` e o schema canônico público estão disponíveis; não executa o método nem expõe rota. Persistência de versões, schemas e hashes pertence à task posterior aprovada.

`packages/pricing-engine` não foi modificado pela APP-002: Pricing Engine 1.0.1, distribuição 1.1.1, Método 1 1.0.0, schema canônico 1 e runtime stdlib-only permanecem preservados.

## Qualidade e limites

A suíte do backend contém 21 testes e exige 100% de statements e branches para o código próprio. Ela cobre configuração, health, readiness disponível/indisponível, correlation ID, erros sanitizados, sessão, commit, rollback, metadata, migration SQL, imports públicos e smoke fora do source tree.

Não foram implementados worker, modelo de futebol, importação histórica, pricing HTTP, autenticação, odds, oportunidades ou Value Tracker.

## Próxima etapa recomendada

**LVFI-APP-003 — Modelagem e importação controlada da base histórica.**