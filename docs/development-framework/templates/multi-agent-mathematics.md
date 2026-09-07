# Template — task matemática

```text
Execute <TASK-ID>.

Base: <commit>
Branch/worktree: <branch e caminho>
Use: r21-multi-agent-orchestration, r21-repository-navigation,
r21-quality-gates, lvfi-pricing-engine e <skill de domínio aplicável>.

Objetivo: <resultado aprovado>
Contratos/versões/hashes congelados: <fontes>
Domain ownership: <arquivos/globs autorizados>
Fora do escopo: <limites>
Aceite e baselines numéricos: <critérios>

Lead → Scout → Domain → Tests independentes → QA → Release. Não altere fórmula,
schema, versão, hash, fixture ou tolerância fora do contrato. Confirme cada fato no
original, valide regressões e entregue o handoff padrão. Não publique.
```
