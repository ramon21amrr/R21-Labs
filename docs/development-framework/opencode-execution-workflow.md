# Fluxo de execução com OpenCode

## Finalidade e autoridade

Este fluxo operacionaliza o R21 Development Framework no OpenCode. Não altera
produto, arquitetura, matemática ou autoridade humana. Em conflito, prevalecem a
tarefa aprovada, `company-context.md`, os documentos do Framework, a documentação
do produto e os ADRs, nessa ordem de especialização.

## Papéis e modelos

| Agente | Uso | Edição | Modelo |
|---|---|---:|---|
| `lvfi-builder` | implementação crítica aprovada | sim | GLM-5.2 somente se `/models` confirmar disponibilidade no plano |
| `lvfi-routine-builder` | docs, testes simples e ajustes pequenos | sim | GLM-4.7 após confirmação no plano |
| `lvfi-reviewer` | escopo, diff, riscos e testes | não | GLM-5.2 |
| `lvfi-recovery` | inventário e proposta de recuperação | somente após aprovação | GLM-4.7 |
| `lvfi-release-auditor` | readiness de release | não | GLM-5.2 |

Não há fallback silencioso. Se o modelo exigido não existir, o agente lista as
opções efetivamente disponíveis e para para decisão do Product Owner. O endpoint
do GLM Coding Plan é `https://api.z.ai/api/coding/paas/v4`; a credencial é
armazenada pelo `opencode providers login`, nunca no repositório.

## Fluxo Git e execução

```text
main estável
  -> branch curta da tarefa
  -> baseline somente leitura
  -> implementação OpenCode no escopo
  -> gates locais
  -> revisão do diff
  -> commit autorizado na branch
  -> push da branch por executor humano/auditado
  -> PR e CI
  -> auditoria conforme criticidade
  -> merge autorizado pelo Product Owner
```

Use `feat/<identificador>`, `fix/<identificador>`, `docs/<identificador>` ou
`chore/<identificador>`. Exemplo:
`feat/lvfi-eng-003-t09-method-one-serialization`. Não trabalhe nem faça push
para `main`.

1. Leia `AGENTS.md`, a tarefa e as fontes autoritativas.
2. Execute `/lvfi-status` e `/lvfi-baseline`; falha interrompe a tarefa.
3. Consulte Graphify para localização/impacto e abra as fontes originais.
4. Implemente apenas o escopo aprovado em branch própria.
5. Execute `/lvfi-gates` e `/lvfi-diff-review`.
6. Gere `/lvfi-report`; commit exige autorização/comando específico.
7. Push, PR e merge são ações separadas e dependem do Product Owner.

## Permissões e segurança

Leitura dentro do repositório é permitida, exceto arquivos de ambiente,
credenciais, chaves e o `auth.json` do OpenCode. Builders podem editar; reviewer
e release auditor não. Recovery pede aprovação. Shell desconhecido, rede e
acesso externo pedem aprovação. O OpenCode `1.18.4` não aceita regras de rede
por URL em `webfetch`; por isso toda chamada de rede usa `ask`, inclusive para
endpoints oficiais. Comandos Git de inspeção e gates conhecidos são
permitidos. Add, commit, merge e remoção segura de branch pedem aprovação.

A permissão do OpenCode `1.18.4` usa padrões de comando e não consegue validar a
branch corrente ao avaliar um `git push` implícito. Para garantir que push direto
em `main` seja impossível, a alternativa mais restritiva foi aplicada: todo
`git push` pelo agente é negado. O push autorizado de uma branch é executado por
humano ou executor auditado fora do agente. Force push, `reset --hard`, `git
clean` amplo, rebase de `main`, instalação global e leitura de credencial são
proibidos. Não use `--auto`.

## Graphify

Graphify é navegação auxiliar. Primeiro use query/path/explain; confirme regra
crítica no arquivo original. Código é extraído localmente por AST. A primeira
indexação usa `--code-only`, respeita `.gitignore` e `.graphifyignore` e não envia
conteúdo. Docs, PDFs e imagens só entram na etapa semântica externa após
inventário e autorização explícita; `inputs/` e segredos nunca entram.

`graphify-out/` é regenerável, local e ignorado pelo Git. Atualize com
`/lvfi-graph-refresh` após mudança estrutural aprovada, não após alteração
irrelevante. Informe staleness quando o grafo não refletir o HEAD.

## Auditoria, recuperação e Product Owner

Use a matriz em `codex-audit-matrix.md`. Para recuperação, invoque
`/lvfi-recover`: o primeiro resultado é sempre inventário/proposta, nunca
restauração. O Product Owner aprova escopo, mudança material, modelo alternativo,
commit, push, PR/merge, release e qualquer envio semântico de documentação
proprietária a serviço externo.
