---
name: r21-repository-navigation
description: Locate R21 code safely with Graphify first, then confirm original sources.
---

# R21 repository navigation

## Use when

A task needs architecture, impact, ownership or file location.

## Do not use when

The user supplied the exact authoritative file and no impact analysis is needed.

## Inputs

Question, task scope, and current graph status.

## Steps

1. Read the task and the smallest applicable authority source.
2. If `graphify-out/graph.json` exists and is current, run `scripts/development/context-query.ps1` with the default budget. Use DFS only for a specific path.
3. Open only returned candidate files; confirm facts in the source files.
4. If the graph is absent, stale or inconclusive, use a targeted `rg` search and state why.

## Success

Names relevant authoritative files, distinguishes extracted from inferred relations, and keeps output compact.

## Stop

Stop for conflicting authorities, sensitive paths, or a material decision unsupported by source files.

## References

`AGENTS.md`; `docs/development-framework/context-and-token-efficiency.md`.

## Minimal output

Question, graph/search method, source files confirmed, and uncertainty.