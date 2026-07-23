---
name: lvfi-graph-navigation
description: Usa o grafo local Graphify para localizar contratos, rastrear dependências e impacto, validar na fonte original e decidir quando atualizar.
compatibility: opencode
metadata:
  owner: R21 Labs
  tool: graphifyy
---

# Navegação Graphify no LVFI

Se `graphify-out/graph.json` existir, comece com `graphify query "<pergunta>"`.
Use `graphify explain "<símbolo>"`, `graphify path "<A>" "<B>"` e `graphify
affected "<símbolo>"` para foco, fluxo e impacto. Registre nós/arestas relevantes
e abra os arquivos originais antes de concluir ou editar regra crítica.

O grafo é auxiliar: arestas `INFERRED` exigem confirmação; documentação original
e ADRs prevalecem. Informe quando o grafo estiver ausente ou desatualizado.
Atualize com `graphify update .` após mudança estrutural aprovada, não após ajuste
irrelevante.

A geração inicial segura usa `graphify extract . --code-only`: AST local, sem API.
Não envie docs, PDFs, imagens, inputs proprietários ou segredos a backend
semântico externo sem autorização explícita e inventário prévio.
