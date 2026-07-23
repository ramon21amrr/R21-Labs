# R21 Labs — orientação permanente para agentes

## Ordem de autoridade e leitura

Siga, nesta ordem: instrução explícita mais recente do Product Owner; documento
da tarefa atual; `docs/company/company-context.md`;
`docs/development-framework/`; documentação do produto afetado; ADRs
aplicáveis; código e testes vigentes. Em conflito ou ambiguidade material, pare,
registre as fontes conflitantes e solicite decisão.

Antes de trabalhar:

1. consulte o Graphify para localização e impacto quando
   `graphify-out/graph.json` existir;
2. abra diretamente os arquivos autoritativos antes de alterar regra crítica;
3. confirme branch própria da tarefa, baseline, escopo, venv autorizado e gates;
4. leia a documentação específica da tarefa e do produto afetado.

O grafo é um índice auxiliar, nunca substitui a fonte original. Atualize-o apenas
após mudanças estruturais aprovadas e informe quando estiver ausente ou
desatualizado.

## Invariantes

Preserve matemática congelada, contratos públicos, schemas, hashes, fixtures,
testes, cobertura e política de versões. Use evolução pequena, verificável e
reversível. Não diminua testes ou cobertura e não altere expectativas ou hashes
para esconder divergência.

Todo trabalho de produto usa branch própria, venv autorizado, gates completos e
relatório final padronizado. Commit, push, PR, merge e release exigem as
autorizações definidas em `docs/development-framework/opencode-execution-workflow.md`.

## Paradas obrigatórias

Pare quando faltar decisão de produto, houver contradição documental, o baseline
falhar, surgir arquivo inesperado, a tarefa exigir matemática congelada, contrato
público ou schema fora do escopo, ou houver necessidade de alterar `main`
diretamente.

Nunca trabalhe diretamente em `main`, faça push ou merge para `main`, use
`git reset --hard`, use `git clean` amplo, reescreva histórico, leia/edite
segredos, instale dependências globais, modifique `requirements-dev.lock` sem
escopo explícito, ou habilite auto-approve irrestrito.

## Verificação e entrega

Use as skills institucionais sob `.opencode/skills/` e os comandos `/lvfi-*`.
Antes da entrega, revise escopo e diff, procure segredos, execute
`git diff --check`, rode os gates aplicáveis e produza o relatório institucional.
O Codex audita os marcos classificados como obrigatórios em
`docs/development-framework/codex-audit-matrix.md`.
