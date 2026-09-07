# Template — release e publicação condicionada

```text
Prepare o encerramento de <TASK-ID>.

Base/branch: <refs>
Use: r21-multi-agent-orchestration, r21-quality-gates e
r21-task-publication somente se houver autorização explícita abaixo.

Escopo integrado: <arquivos/unidades>
Handoffs: <referências compactas>
Gates finais: <perfil>
Autorização de commit/push/PR/merge: <nenhuma ou ação exata autorizada>

Confirme ownership, diff e continuidade; faça secret scan e gates finais. Sem
autorização, pare após o dry-run e informe uma única ação humana necessária. Com
autorização, execute somente a ação publicada no campo acima, sem force-push,
reset destrutivo, clean amplo ou publicação direta em main. Não inicie outra task.
```
