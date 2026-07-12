# Convenções de Git e GitHub

## Branch principal

`main` representa o estado estável e revisado do repositório. Push direto para `main` não faz parte do fluxo normal.

## Branches de trabalho

Branches devem ser curtas, relacionadas a uma Task e usar nomes descritivos:

- `feature/<task-id>-<descricao>` para funcionalidades.
- `fix/<task-id>-<descricao>` para correções.
- `docs/<task-id>-<descricao>` para documentação.
- `chore/<task-id>-<descricao>` para manutenção aprovada.

Branches adicionais só devem existir quando uma necessidade real justificar.

## Commits

Cada commit deve representar uma alteração coerente, referenciar a Task e evitar mudanças não relacionadas.

Formato recomendado:

```text
tipo(escopo): descrição [TASK-ID]
```

Exemplos:

```text
docs(framework): define fluxo de aprovação [R21-001]
feat(tracker): adiciona cadastro de aposta [VT-014]
fix(tracker): corrige cálculo de retorno [VT-027]
```

## Quando fazer commit

- Após concluir e validar uma unidade coerente.
- Antes de iniciar uma parte independente do trabalho.
- Quando o conteúdo do commit puder ser compreendido isoladamente.
- Nunca incluir segredos, arquivos locais ou alterações fora do escopo.

## Quando fazer push

- Depois que os commits relevantes estiverem validados.
- Para disponibilizar uma branch válida para revisão ou preservação remota.
- Nunca reescrever histórico compartilhado sem autorização.

## Pull Request e integração

- Cada Pull Request deve estar relacionado a uma Task aprovada.
- O conteúdo deve atender aos critérios de aceitação e à definição de pronto.
- As verificações aplicáveis devem passar antes da integração.
- A revisão deve ocorrer antes de chegar à `main`.
- A preferência inicial é por squash merge, mantendo um registro simples por Task.
- A branch deve ser excluída após integração, quando não for mais necessária.

## Relação entre os registros

Uma Task define o trabalho; uma branch o isola; os commits registram unidades coerentes; o Pull Request reúne a entrega para revisão; a integração incorpora o resultado aprovado à `main`.
