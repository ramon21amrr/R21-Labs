---
description: Audita readiness de release LVFI em modo somente leitura
agent: lvfi-release-auditor
subtask: true
---

Carregue `lvfi-release-gates` e a documentação de release aplicável. Audite
versões, changelog/documentação, dependências, lockfile, suíte e cobertura,
Ruff, mypy, compileall, wheel/metadata, instalação limpa, pip check, smoke,
hashes, segurança e rastreabilidade. Só construa artefatos quando a tarefa de
release autorizar; caso contrário, marque essa parte como não executada. Não
edite nem substitua auditoria obrigatória do Codex.
