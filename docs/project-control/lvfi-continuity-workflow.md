# Workflow de continuidade do LVFI

## Início de task

1. Ler [current-state](lvfi-current-state.md).
2. Validar sintaxe e conteúdo de [project-state.yaml](lvfi-project-state.yaml).
3. Confirmar `reference_commit`, `HEAD`, `origin/main`, ahead/behind e árvore.
4. Confirmar a próxima task oficial; nunca usar inferência.
5. Consultar o [task registry](lvfi-task-registry.md).
6. Usar Graphify-first com orçamento limitado e informar staleness.
7. Abrir os documentos originais indicados pelo grafo/busca.
8. Criar branch própria e checkpoint local.
9. Executar somente o plano aprovado.

## Encerramento de task

1. Validar o escopo com gates proporcionais.
2. Documentar a entrega e evidências.
3. Atualizar todos os artefatos de controle aplicáveis.
4. Obter do Product Owner a próxima task ou decisão; não inferir.
5. Gerar handoff de sessão e handoff único.
6. Publicar somente mediante autorizações separadas.
7. Sincronizar `main` por fast-forward após merge autorizado.
8. Confirmar ahead/behind `0/0` e working tree limpa.

Use o [checklist](lvfi-task-closure-checklist.md) para distinguir encerramento
técnico, publicação e encerramento institucional.

## Novo chat

1. Anexar `lvfi-session-handoff.md` e `lvfi-project-state.yaml`, ou
   `LVFI-CHAT-HANDOFF.md`.
2. Colar o [bootstrap](lvfi-new-chat-bootstrap.md).
3. Confirmar `reference_commit` no Git.
4. Verificar que `last_completed_task`, `next_official_task` e ação imediata
   coincidem entre os arquivos.
5. Continuar somente da ação imediata.

## Economia de contexto

Leia incrementalmente: estado → registry/decisão necessários → Graphify → fonte
original. Não carregue o repositório inteiro, relatórios integrais do grafo ou
documentos não relacionados. Reutilize resultados verificados na mesma task e
produza saídas compactas com links para evidências.
