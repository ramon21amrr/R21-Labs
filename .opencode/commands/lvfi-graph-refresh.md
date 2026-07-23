---
description: Atualiza o grafo Graphify local após mudança estrutural aprovada
agent: lvfi-builder
subtask: true
---

Carregue `lvfi-graph-navigation`. Verifique `.graphifyignore` e inventarie o
escopo. Se não houver grafo, gere apenas código local com `graphify extract .
--code-only`; se existir e houve mudança estrutural aprovada, use `graphify
update .`. Não habilite backend semântico, não processe `inputs/` e não envie
documentos a API. Informe arquivos analisados, exclusões, duração, tamanhos,
erros e staleness. Não edite produto nem versione `graphify-out/`.
