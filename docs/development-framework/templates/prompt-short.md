# Prompt curto de task

```text
Execute <TASK-ID>.

Branch: <branch>
Base: <commit>
Use explicitamente: <$skills>

Objetivo: <objetivo específico>
Escopo permitido: <arquivos ou comportamento>
Escopo proibido: <limites relevantes>
Critérios exclusivos: <aceites desta task>
Resultado final: <evidências e estado Git>
Não iniciar próxima task.
```

Exemplos: documentação usa `r21-repository-navigation,r21-quality-gates`; backend
acrescenta `lvfi-backend-data`; migration usa as mesmas duas; Pricing Engine usa
`lvfi-pricing-engine`; correção isolada usa apenas a Skill de navegação necessária;
publicação acrescenta explicitamente `r21-task-publication`.