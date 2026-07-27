---
name: lvfi-backend-data
description: Work on LVFI FastAPI, PostgreSQL, SQLAlchemy, Alembic and historical-data provenance.
---

# LVFI backend and data

## Use when

Changing `apps/api`, migrations, importers, provenance or database tests.

## Do not use when

A task is documentation-only, Pricing Engine-only, or has no backend/data change.

## Inputs

Approved scope, migration contract, source-data constraints and authorized environment.

## Steps

1. Locate affected paths with `r21-repository-navigation` and confirm contracts.
2. Preserve migration reversibility, provenance and disposable-resource cleanup.
3. Run the `api` profile and migration-specific tests.

## Success

Contracts, migrations and resource cleanup are verified without exposing source data.

## Stop

Stop for schema/public-contract change outside scope, missing rollback plan or proprietary-data risk.

## References

`apps/api/README.md`; product documentation; `r21-quality-gates`.

## Minimal output

Affected contract, migration plan, gates and data-safety result.