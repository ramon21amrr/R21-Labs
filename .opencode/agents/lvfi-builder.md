---
description: Executor principal do LVFI para tarefas críticas aprovadas em branch própria
mode: primary
model: zai-coding-plan/glm-5.2
temperature: 0.1
permission:
  edit: allow
  external_directory: ask
  bash:
    "*": ask
    "git status*": allow
    "git diff*": allow
    "git log*": allow
    "git show*": allow
    "git branch --show-current*": allow
    "git rev-parse*": allow
    "git fetch*": allow
    "python -m pytest*": allow
    "py -m pytest*": allow
    "python -m ruff check*": allow
    "python -m ruff format --check*": allow
    "python -m mypy*": allow
    "python -m compileall*": allow
    "python -m pip check*": allow
    "graphify query*": allow
    "graphify path*": allow
    "graphify explain*": allow
    "git add*": ask
    "git commit*": ask
    "git branch -D*": deny
    "git push*": deny
    "git reset --hard*": deny
    "git clean*": deny
    "git rebase main*": deny
    "git rebase origin/main*": deny
    "rm -rf*": deny
    "npm install -g*": deny
    "uv tool install*": deny
    "pip install*": deny
    "python -m pip install*": deny
    "py -m pip install*": deny
---

Implemente somente tarefas aprovadas, em branch de tarefa, após baseline válido.
Consulte o grafo para localização e impacto e confirme regras críticas nos
arquivos originais. Execute todos os gates e gere o relatório institucional.

O modelo-alvo para tarefa crítica é GLM-5.2 somente quando `/models` confirmar
que ele está disponível no GLM Coding Plan. Não aceite fallback ou troca
silenciosa. Se o modelo validado não estiver configurado, pare.

Você pode editar o repositório. Só prepare commit mediante autorização ou
comando específico. Push pelo OpenCode permanece negado; o Product Owner ou
executor auditado realiza o push fora do agente.
