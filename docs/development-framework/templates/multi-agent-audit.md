# Template — auditoria independente

```text
Audite <TASK-ID ou diff>.

Base/alvo: <refs>
Use: r21-multi-agent-orchestration, r21-repository-navigation,
r21-quality-gates e <skills de domínio necessárias>.

Escopo da auditoria: <arquivos/contratos>
Riscos prioritários: escopo, contratos, secrets, N+1, erros sanitizados,
regressões, segurança e compatibilidade.

Atue read-only por padrão. Faça Graphify-first, confirme achados nos originais e
classifique-os por severidade com arquivo/linha, impacto e evidência reproduzível.
Não repita análise válida nem implemente correções sem autorização. Entregue o
handoff padrão e declare explicitamente se não houver achados.
```
