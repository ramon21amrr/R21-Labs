# Eficiência de contexto e tokens do Codex

## Objetivo

Reduzir exploração repetitiva sem reduzir fontes autoritativas, gates ou rastreabilidade.
O grafo é um mapa local: nunca substitui documentos, contratos, ADRs, código ou
testes.

Auditoria inicial: `AGENTS.md` tinha 2.373 caracteres e 306 palavras; após a
redução controlada, tem 1.423 caracteres e 200 palavras (950 caracteres, 40,0%).
Não há telemetria confiável de tokens nesta sessão.

## Arquitetura e segurança

Graphify `0.9.25` é instalado isoladamente por `uv tool`; não é dependência de
produção. A `.graphifyignore` exclui inputs, workbooks, CSVs, segredos, bancos,
caches, binários e artefatos locais. O fluxo permitido é AST-only, local, sem API,
MCP, watch, visualização, URLs, PDFs ou enriquecimento semântico remoto.

`graphify-out/` continua ignorado e não é versionado: contém metadados locais,
usa caminhos de instalação não portáveis em integrações e seu benefício não supera
o risco/tamanho para novos worktrees. Cada worktree o recria com:

```powershell
scripts/development/bootstrap-graphify.ps1 -CheckOnly
$graphify = Join-Path ((uv tool dir).Trim()) 'graphifyy\Scripts\graphify.exe'
& $graphify extract . --code-only --no-cluster
& $graphify cluster-only . --no-viz --no-label
```

Atualize uma mudança estrutural com `graphify update .`; execute novamente
`cluster-only` para renovar o relatório. Antes de confiar no resultado, faça
varredura de caminhos absolutos, credenciais, `connection.json`, `.xlsm` e dados
proprietários. Se houver ocorrência material, descarte o grafo, ajuste o ignore e
reconstrua.

## Codex e hooks

A integração ativa é a orientação Graphify-first curta no `AGENTS.md` e a Skill
`r21-repository-navigation`. O instalador do Graphify para Codex foi rejeitado:
a variante limitada ao projeto cria `.codex/hooks.json` e inclui caminho absoluto
do executável; isso não é portátil e não é versionado. Não houve configuração
global do Codex.

Hooks Git foram testados somente em repositório sintético. Eles instalam
post-commit/post-checkout e iniciam reconstrução breve em segundo plano; não são
instalados no repositório R21 para evitar efeitos colaterais e processos extras.
A atualização é manual, local e explícita.

## Skills e scripts

As cinco Skills em `.agents/skills/` roteiam navegação, qualidade, publicação
explícita, backend/dados e Pricing Engine. As descrições negativas impedem carregar
backend ou Pricing Engine em tarefas documentais e impedem publicação implícita.

- `context-query.ps1`: consulta limitada a 800–5.000 tokens (padrão 1.200).
- `task-baseline.ps1`: estado Git, áreas alteradas e perfis recomendados.
- `run-quality-gates.ps1`: perfis `docs`, `api`, `pricing` e `full`; logs completos
  ficam em `.r21-artifacts/quality/`.
- `task-state.ps1`: inicia, atualiza, mostra e encerra checkpoint local validado
  contra branch e HEAD.
- `bootstrap-graphify.ps1`: verifica/instala somente a versão testada no ambiente
  isolado de `uv`.

Publicação não é automatizada: o checklist versionado exige ação explícita e evita
push ou merge involuntário.

A geração e atualização incremental validadas em R21-DEV-001 produziram 2.637 nós, 6.100 relações,
`graph.json` de 4.324.735 bytes, relatório de 46.677 bytes e manifesto de 48.656
bytes. A inspeção não encontrou caminhos pessoais, `C:\tmp`, arquivos de inputs,
workbooks, credenciais ou valores reais de `DATABASE_URL`; quatro referências ao
nome da variável foram classificadas como não sensíveis.

## Prompt curto

Use [o template](templates/prompt-short.md). As regras institucionais permanecem
no `AGENTS.md`; os procedimentos sob demanda permanecem nas Skills. O texto
completo da R21-DEV-001 tem 29.581 caracteres, enquanto o template básico tem
655 (redução de 28.926 caracteres, 97,8%). Essa é apenas uma comparação de
caracteres, não uma medição de tokens.

## Benchmark e limitações

Tokens exatos não estão disponíveis; foram usadas métricas substitutas. As saídas
completas estão em `.r21-artifacts/benchmark/` e cada resultado foi confirmado nos
arquivos de origem indicados pelo grafo ou pelo fallback.

| Pergunta | Convencional (caracteres / ms) | Otimizado (caracteres / ms) | Resultado |
| --- | ---: | ---: | --- |
| API, health, sessão e migrations | 14.000 / 138 | 4.377 / 2.388 | fontes de código localizadas; menos contexto, maior latência |
| versões, hashes e cenário 10×10 | 256.405 / 288 | 4.236 / 2.078 | fontes de código localizadas; menos contexto, maior latência |
| histórico, importador e proveniência | 116.710 / 147 | 120.926 / 1.528 | fallback de documentação necessário; não há economia |

A conclusão é deliberadamente limitada: use Graphify para navegação estrutural de
código e consulta com orçamento; para documentação histórica, use busca direcionada
e confirme a fonte original. O grafo não é adotado como substituto de busca quando
o resultado for pior ou incompleto.

## Operação

Inicie uma task com o prompt curto, Skills explícitas, baseline e checkpoint local.
Retome com `task-state.ps1 -Action show`; estado divergente de branch/HEAD é
recusado. Para publicar, acrescente explicitamente `r21-task-publication` e siga o
checklist manual após todos os gates. Reavalie esta solução quando a versão do
Graphify, o Codex, a estrutura do repositório ou os requisitos de segurança
mudarem.