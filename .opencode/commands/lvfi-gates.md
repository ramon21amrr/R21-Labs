---
description: Executa gates padronizados LVFI e resume evidências
agent: lvfi-release-auditor
subtask: true
---

Carregue `lvfi-release-gates`. No venv autorizado, execute pytest/cobertura,
Ruff check, Ruff format check, mypy strict, compileall e pip check. Confirme
hashes e cenário 10×10 pelos testes originais. Não construa wheel se a tarefa
não autorizar release/versionamento. Resuma comando, resultado, duração e
qualquer gate não aplicável; não altere expectativas.
