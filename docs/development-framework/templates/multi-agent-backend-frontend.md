# Template — backend e frontend em paralelo

```text
Execute <TASK-ID>.

Base: <commit comum>
Branch/worktree do Lead: <branch e caminho>
Use: r21-multi-agent-orchestration, r21-repository-navigation,
r21-quality-gates, lvfi-backend-data e <skills adicionais autorizadas>.

Objetivo: <resultado full-stack aprovado>
Contrato compartilhado estável: <fonte>
Backend ownership: apps/api/**, <migrations autorizadas>
Frontend ownership: apps/web/**
Fora do escopo: <limites>
Aceite: <critérios verificáveis>

Lead → Scout → Backend + Frontend em worktrees/branches próprias → Tests → QA →
Governance, se exigido → Release. Não paralelize arquivos compartilhados. Integre
na ordem das dependências, rode gates proporcionais e use o handoff padrão.
Não publique nem inicie outra task.
```
