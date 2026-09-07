---
name: r21-multi-agent-orchestration
description: Orchestrate approved R21 tasks with the smallest useful agent team, isolated ownership, bounded parallelism, compact handoffs, and controlled integration. Use when delegation or parallel execution can materially reduce elapsed time or repeated context.
---

# R21 multi-agent orchestration

## Boundary

Orchestrate only the approved task. Do not create product scope, infer a missing task, change an authority source, or publish without explicit Product Owner authorization. Prefer one executor when delegation costs more than it saves.

Before decomposition, confirm the baseline, non-`main` branch, scope, authorized environment and applicable gates. Use `r21-repository-navigation` for Graphify-first discovery and confirmation in original files. Load only the domain Skills needed by the selected lanes.

## Pool and activation

The roles are a pool, not a mandatory team:

| Role | Activate for |
| --- | --- |
| 01 Lead / Orchestrator | Every multi-agent task: contract, dependencies, ownership, integration and final evidence |
| 02 Context Scout | Targeted discovery and minimal read-only context when locations or impact are not already authoritative |
| 03 Backend / Data | FastAPI, PostgreSQL, migrations, repositories, services, schemas or persistence; use `lvfi-backend-data` for LVFI |
| 04 Frontend / UX | Next.js, TypeScript, UI, API client, accessibility and frontend gates |
| 05 Domain / Statistics | Models, samples, calculations or Pricing Engine; use `lvfi-pricing-engine` when applicable |
| 06 Test Engineer | Independent or cross-lane tests, fixtures, edge cases and regressions |
| 07 QA / Security Auditor | Independent diff, contract, secret, N+1, error, security and compatibility review |
| 08 Documentation / Governance | Documentation, ADRs, registry, state, YAML, handoff and continuity after implementation stabilizes |
| 09 Release / Integrator | Final checkpoint, staging and Git preparation; publication only through `r21-task-publication` when authorized |

Select the minimum roles that cover the task and independent review. Typical dependency shapes are:

- Localized backend or frontend: `01 -> 02 if needed -> 03 or 04 -> 06 -> 07 -> 09`.
- Full stack: `01 -> 02 -> (03 || 04) -> 06 -> 07 -> 08 if affected -> 09`.
- Mathematics: `01 -> 02 -> 05 -> 06 -> 07 -> 09`.
- Small, low-risk work: keep one executor and add only the review/gates required by risk.

## Plan and ownership

The Lead records before spawning executors:

1. A dependency DAG and success evidence for each lane.
2. Exact, disjoint file ownership using paths or globs; shared files have one owner and other agents propose changes in their handoff.
3. Each lane's input context, branch, worktree, gates and qualitative budget.

Run no more than four executor roles simultaneously by default. Exceed that only
when the lanes are genuinely independent, file ownership does not overlap and the
expected gain justifies the added coordination and token cost. Parallelize only
ready lanes; otherwise sequence them. Read-only discovery may run alongside
implementation when it cannot invalidate ownership.

Each parallel executor that writes gets its own worktree and task branch. It edits only its ownership set, preserves unrelated changes, reviews its diff and reports the resulting state. Never allow simultaneous edits to the same file. The Lead avoids functional edits owned by another lane.

## Handoff and integration

Return only useful deltas in this form:

```text
STATUS:
FEITO:
ARQUIVOS:
CONTRATOS ALTERADOS:
TESTES:
BLOQUEIOS:
PRÓXIMA DEPENDÊNCIA:
```

Do not repeat the roadmap, `AGENTS.md`, task body or institutional rules. The receiver reuses valid evidence and queries Graphify/original files only for missing detail.

The Lead integrates one reviewed lane at a time on the designated integration branch, checks ownership and dependencies, and resolves conflicts from original sources. Use ordinary Git integration only; never force-push, rewrite history, run destructive reset or broad clean, overwrite another lane, or discard an unintegrated worktree. Run focused checks during iteration and `r21-quality-gates` at checkpoints. QA must be independent of the implementation it audits.

Role 09 may prepare and dry-run release evidence at LOW cost. Commit, push, PR and merge require explicit Product Owner authorization and the `r21-task-publication` workflow.

## Context budget

- `LOW`: navigation, simple documentation, status, mechanical release preparation.
- `MEDIUM`: localized implementation, tests, normal backend or frontend work.
- `HIGH`: architecture, schemas, critical migrations, mathematics or complex audit.

Give each agent only its lane's contract, confirmed source paths, dependencies and expected evidence. Prefer Scout handoffs, targeted reads, focused tests and compact outputs. Do not duplicate another agent's valid analysis. Reserve full gates for checkpoints and do not bind budgets to model names.

## Stop

Stop the affected lane and return control to the Lead for conflicting authorities, branch/baseline mismatch, ownership overlap, unresolved dependency, failed required gate, secret exposure, unexpected public contract/schema/frozen-math change, or scope/authorization expansion. The Lead stops the task and asks the Product Owner when the decision is material; do not guess or bypass the blocked lane.

## References

`AGENTS.md`; `docs/development-framework/ai-collaboration.md`; `docs/development-framework/context-and-token-efficiency.md`; `docs/development-framework/workflow.md`; `docs/development-framework/git-github.md`; `r21-repository-navigation`; `r21-quality-gates`; `r21-task-publication`; applicable domain Skills.
