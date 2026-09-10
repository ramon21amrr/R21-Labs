# Template — task single-agent

```text
Execute <TASK-ID>.

Base: <commit>
Branch/worktree: <branch e caminho>
Use: r21-multi-agent-orchestration, r21-repository-navigation,
r21-quality-gates e <skill de domínio, se aplicável>.

Objetivo: <resultado aprovado>
Ownership exclusivo: <arquivos/globs>
Fora do escopo: <limites>
Aceite: <critérios verificáveis>

A Base é a referência estável aprovada, não o HEAD produzido pela task. Resolva
HEAD, main e origin/main em runtime com `git rev-parse`; não hardcode o SHA
corrente em handoffs/estado nem substitua a Base pelo próprio merge.

Trabalhe como Lead + executor porque não há ganho líquido de paralelismo.
Faça Graphify-first, confirme originais, rode gates proporcionais e entregue o
handoff padrão. Não publique nem inicie outra task.
```
