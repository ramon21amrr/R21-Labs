---
name: r21-task-publication
description: Explicit-only checklist for safe R21 commit, push, PR and merge.
---

# R21 task publication

## Use when

The Product Owner explicitly requests commit, push, PR or merge.

## Do not use when

Implementing, reviewing, testing or drafting a task. Never infer publication intent.

## Inputs

Approved task, branch, base commit, gate evidence and publication authorization.

## Steps

1. Confirm a non-main branch, clean tree, authorized parent and completed gates.
2. Review the scoped diff and secrets scan.
3. Follow `docs/development-framework/templates/publication-checklist.md` one action at a time.
4. Stop on ambiguous PR state, failed checks, conflict, force-push request or direct-main request.

## Success

An authorized, reviewable PR and only the requested Git action.

## Stop

Stop before any publication action without explicit authorization.

## References

`docs/development-framework/git-github.md`; `opencode-execution-workflow.md`.

## Minimal output

Branch, commit, PR/check status, merge state, one required human action if blocked.