---
name: lvfi-git-safety
description: Governa branches, commits, push, PR e recuperação segura do LVFI, bloqueando ações destrutivas e trabalho direto em main.
compatibility: opencode
metadata:
  owner: R21 Labs
  authority: docs/development-framework/git-github.md
---

# Segurança Git LVFI

Leia `docs/development-framework/git-github.md` e
`opencode-execution-workflow.md`. Confirme branch e status antes de agir.

Use `feat/<id>-<descricao>`, `fix/<id>`, `docs/<id>` ou `chore/<id>`. Nunca
trabalhe ou faça push direto em `main`; nunca force push, `reset --hard`, `git
clean` amplo ou rebase destrutivo. `git add`, commit, remoção de branch, merge e
push exigem autorização. Como a versão atual do OpenCode não distingue com
segurança um `git push` implícito em branch de um push implícito em `main`, todo
push pelo agente está negado; o executor humano/auditado o realiza.

Recuperação começa por inventário e proposta por caminho. Nada é restaurado ou
apagado sem autorização.
