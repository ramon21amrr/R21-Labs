# Workflow de continuidade do LVFI

## Início de task

1. Ler [current-state](lvfi-current-state.md).
2. Validar sintaxe e conteúdo de [project-state.yaml](lvfi-project-state.yaml).
3. Tratar `reference_commit` como a base estável explicitamente aprovada para a
   task ativa; ele não é um apelido para o SHA corrente e não pode ser regravado
   pelo commit ou merge produzido pela própria task.
4. Resolver os valores correntes no runtime com `git rev-parse HEAD`,
   `git rev-parse main` e `git rev-parse origin/main`; então confirmar
   ahead/behind e árvore. Nunca copiar esses SHAs como “atual” no estado ou
   handoff.
5. Confirmar a próxima task oficial; nunca usar inferência.
6. Consultar o [task registry](lvfi-task-registry.md).
7. Usar Graphify-first com orçamento limitado e informar staleness.
8. Abrir os documentos originais indicados pelo grafo/busca.
9. Criar branch própria e checkpoint local.
10. Executar somente o plano aprovado.

## Encerramento de task

1. Validar o escopo com gates proporcionais.
2. Documentar a entrega e evidências.
3. Atualizar todos os artefatos de controle aplicáveis.
4. Obter do Product Owner a próxima task ou decisão; não inferir.
5. Gerar handoff de sessão e handoff único.
6. Publicar somente mediante autorizações separadas.
7. Sincronizar `main` por fast-forward após merge autorizado.
8. Registrar no registry o commit/merge histórico da task, mas manter
   `reference_commit` como sua base aprovada; uma nova base só é definida pela
   ativação explícita de outra task.
9. Resolver novamente `HEAD`, `main` e `origin/main` por Git e confirmar
   ahead/behind `0/0` e working tree limpa.

Use o [checklist](lvfi-task-closure-checklist.md) para distinguir encerramento
técnico, publicação e encerramento institucional.

## Novo chat

1. Anexar `lvfi-session-handoff.md` e `lvfi-project-state.yaml`, ou
   `LVFI-CHAT-HANDOFF.md`.
2. Colar o [bootstrap](lvfi-new-chat-bootstrap.md).
3. Ler `reference_commit` como base estável e resolver o estado corrente com
   `git rev-parse HEAD`, `git rev-parse main` e `git rev-parse origin/main`.
4. Verificar que `last_completed_task`, `next_official_task` e ação imediata
   coincidem entre os arquivos.
5. Continuar somente da ação imediata.

## Economia de contexto

Leia incrementalmente: estado → registry/decisão necessários → Graphify → fonte
original. Não carregue o repositório inteiro, relatórios integrais do grafo ou
documentos não relacionados. Reutilize resultados verificados na mesma task e
produza saídas compactas com links para evidências.
