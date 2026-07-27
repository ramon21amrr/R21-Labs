# LVFI API

Backend foundation for the Linha de Valor Football Intelligence modular monolith.

## Local execution

Use CPython 3.13 and install the locked environment:

```powershell
cd apps/api
uv sync --all-groups --locked
Copy-Item .env.example .env
uv run alembic upgrade head
uv run uvicorn lvfi_api.main:create_app --factory --host 127.0.0.1 --port 8000
```

`LVFI_DATABASE_URL` must use PostgreSQL with the `postgresql+asyncpg` dialect.
The example values are local development values only; replace them through your
environment and never commit `.env`.

## Operational endpoints

- `GET /health` proves the HTTP process is running and has no database dependency.
- `GET /ready` probes PostgreSQL and returns HTTP 503 when the database is unavailable.

Every response includes `X-Request-ID`. A caller-provided value is propagated when
it is safe to log; otherwise a UUID is generated.

## Migrations

Alembic owns its `alembic_version` control table. Revision `20260724_01` establishes
the foundation; `20260727_02` adds the controlled historical-import model. Run
`uv run alembic upgrade head` and `uv run alembic downgrade 20260724_01` to validate
the APP-003 rollback path against disposable PostgreSQL.

## Pricing Engine boundary

The API imports only public symbols from `lvfi_pricing.models.method_one`.
It exposes no pricing endpoint and does not execute `run_method_one` yet. Future
use cases will supply normalized inputs and persist approved versions and hashes.

## Historical query API

The read-only API exposes `/competitions`, `/seasons`, `/teams` and `/matches` (including canonical match statistics). List endpoints use bounded offset pagination; match filters are exact and documented in the OpenAPI. See [historical match query API](../../docs/products/linha-de-valor-football-intelligence/31-historical-match-query-api.md).