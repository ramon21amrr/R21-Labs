---
name: lvfi-release-gates
description: Executa e interpreta os gates LVFI de pytest, cobertura, Ruff, mypy, compileall, pip check, wheel, instalação limpa, smoke e hashes.
compatibility: opencode
metadata:
  owner: R21 Labs
  package: packages/pricing-engine
---

# Gates de release LVFI

No venv autorizado e em `packages/pricing-engine`, execute sem alterar
expectativas: `python -m pytest`; `python -m ruff check .`; `python -m ruff
format --check .`; `python -m mypy`; `python -m compileall -q src tests`; e
`python -m pip check`.

Para release explicitamente autorizada, acrescente build de wheel, inspeção de
metadata, instalação `--no-deps` em venv limpo, `pip check`, smoke de importação
e regressões de hashes. Não construa wheel em tarefa que proíba versionamento ou
release. Exija 100% de statements e branches e confirme cenário 10×10 pelos
testes vigentes.
