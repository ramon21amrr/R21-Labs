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

Alembic owns its `alembic_version` control table. The first revision deliberately
creates no football-domain table: that model belongs to the next approved task.
Run `uv run alembic upgrade head` and `uv run alembic downgrade base` to validate
the reversible migration pipeline against PostgreSQL.

## Pricing Engine boundary

The API imports only public symbols from `lvfi_pricing.models.method_one`.
It exposes no pricing endpoint and does not execute `run_method_one` yet. Future
use cases will supply normalized inputs and persist approved versions and hashes.
