---
description: Executa baseline LVFI, hashes e cenário 10×10 sem editar
agent: lvfi-reviewer
subtask: true
---

Confirme branch e árvore esperadas. Localize o venv externo autorizado sem criar
ou instalar dependências. Em `packages/pricing-engine`, execute a suíte
institucional configurada em `pyproject.toml`; confirme contagem vigente, 100% de
statements e branches, hashes de regressão e cenário 10×10. Confirme também
`python -m pip check` e integridade de `requirements-dev.lock`. Pare no primeiro
desvio, preserve toda expectativa e não edite arquivos.
