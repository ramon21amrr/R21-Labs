---
name: r21-quality-gates
description: Select and run compact R21 validation profiles with complete local logs.
---

# R21 quality gates

## Use when

A task needs validation before review, commit or publication.

## Do not use when

Only locating files or planning a task.

## Inputs

Changed areas and the intended phase: iteration, pre-commit or publication.

## Steps

1. Run `scripts/development/task-baseline.ps1 -AsJson`.
2. Choose `docs`, `api`, `pricing`, or `full`; do not select Pricing Engine gates for documentation-only changes.
3. Use `run-quality-gates.ps1`; it stores full logs in ignored `.r21-artifacts/quality/` and prints a compact result.
4. Report profile, outcome, log path and first failure when present.

## Success

All applicable gates pass; failures remain visible and reproducible.

## Stop

Stop when baseline fails, an authorized environment is absent, or a required gate fails.

## References

`docs/development-framework/quality.md`; `scripts/development/run-quality-gates.ps1`.

## Minimal output

Profile, pass/fail, duration, log path, first failure.