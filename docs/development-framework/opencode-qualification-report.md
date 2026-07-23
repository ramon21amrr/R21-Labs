# R21-OPS-001 — relatório de configuração e qualificação

Data da execução: 2026-07-23. Escopo exclusivo: tooling, governança e
qualificação somente leitura. T09, Pricing Engine, matemática, contratos,
schemas, versões e hashes permaneceram fora do escopo.

## 1. Baseline inicial

- Repositório: `C:\Users\ramon\OneDrive\Documentos\Projetos\R21-Labs`.
- Branch: `main`; árvore inicialmente limpa.
- `HEAD` e `origin/main`: `c45bfd801afd812313e35e42f5b1e6fab0676c71`.
- Commit vigente: `feat(models): add method one orchestration [LVFI-ENG-003-T08]`.
- Distribuição: `1.1.0a9`; Método 1: `1.0.0a4`.
- Baseline: 519 testes aprovados; 3042 statements e 1022 branches em 100%.
- Blob do `requirements-dev.lock`: `3d6089e195956f6c2924d4e14eb4522c83be6ec9`, idêntico ao `HEAD`.
- T08 concluída; T09 não iniciada.

## 2. Ambiente e inventário

- Windows: registro `Windows 10 Home Single Language`, versão `25H2`, build
  `26200.8894`, `EditionID CoreSingleLanguage`.
- PowerShell: 7.6.4 Core; Git: 2.55.0.windows.2; GitHub CLI: 2.96.0.
- Node.js: 24.18.0; npm: 11.16.0; Python global: 3.13.14.
- Codex: pacote Desktop `OpenAI.Codex_26.715.10079.0`; a execução direta da CLI
  foi bloqueada pela política local.
- Disco C: 452,55 GiB totais e 173,84 GiB livres no inventário.
- Execution Policy: `LocalMachine=RemoteSigned`; demais escopos indefinidos.
- `SecurityHealthService` estava ativo. `WinDefend` e `WdNisSvc` apareceram
  parados; `Get-MpComputerStatus` foi negado, portanto o estado completo do
  antivírus não pôde ser atestado.
- Nenhuma variável de ambiente relacionada a Z.AI, GLM ou OpenCode foi
  encontrada; valores de variáveis nunca foram lidos.

## 3. Backup e configurações preexistentes

Antes da alteração foi criado o backup externo
`C:\tmp\r21-ops-001-backup-20260723-143348`. Foram preservados `.agents` e
`.gitignore`. Não existiam `AGENTS.md`, `opencode.json`, `.opencode`,
`.graphifyignore`, `graphify-out` ou configuração relevante local/global do
OpenCode/Graphify. O armazenamento de credenciais não foi lido nem copiado.

## 4. Fontes oficiais e versões

Foram consultadas exclusivamente fontes primárias: documentação OpenCode
(atualizada em 20–22/07/2026), documentação Z.AI do GLM Coding Plan, repositório
e política de segurança do Graphify-Labs e manual oficial do Codex para
`AGENTS.md`/skills.

- OpenCode CLI `1.18.4`, instalado por npm oficial com versão exata
  (`opencode-ai@1.18.4`). A CLI reproduzível foi escolhida para automação no
  Windows; executável, versão, ajuda e inicialização foram validados.
- uv `0.11.30`, instalado pelo catálogo oficial WinGet `astral-sh.uv`; era a
  versão publicada no catálogo no momento, embora upstream já anunciasse
  0.11.31.
- Graphify oficial `graphifyy==0.9.25`, instalado por `uv tool` em ambiente
  isolado, fora do venv do Pricing Engine.

Referências: `https://opencode.ai/docs/`,
`https://docs.z.ai/scenario-example/develop-tools/opencode`,
`https://docs.z.ai/devpack/quick-start`,
`https://github.com/Graphify-Labs/graphify`,
`https://graphify.com/security`,
`https://learn.chatgpt.com/docs/agent-configuration/agents-md` e
`https://learn.chatgpt.com/docs/build-skills`.

## 5. OpenCode e GLM

A configuração usa somente formatos aceitos pelo OpenCode 1.18.4:

- provedor habilitado: `zai-coding-plan`;
- endpoint: `https://api.z.ai/api/coding/paas/v4`;
- principal: `zai-coding-plan/glm-5.2`;
- rotina: `zai-coding-plan/glm-4.7`;
- compartilhamento desativado, atualização automática desativada e sem fallback
  silencioso.

O login foi concluído pelo Product Owner por `opencode providers login`; a
credencial fica no armazenamento próprio do OpenCode e não foi exibida. O
provedor reportou uma credencial e o catálogo listou GLM-4.5-Air, GLM-4.7,
GLM-5-Turbo, GLM-5.1, GLM-5.2 e GLM-5V-Turbo.

Com autorização explícita do Product Owner, foram feitas duas sondas externas
sem ferramentas, leitura de arquivos ou fallback: `GLM-5.2 OK` pelo provedor
`zai-coding-plan`/modelo `glm-5.2` e `GLM-4.7 OK` pelo mesmo provedor/modelo
`glm-4.7`. Foram transmitidos somente o prompt estático de qualificação e as
instruções institucionais `AGENTS.md` e do agente necessárias ao OpenCode; não
foram transmitidos código do produto, documentos internos do LVFI, inputs,
credenciais, tokens, chaves, conteúdo de clientes ou dados sensíveis. A primeira
tentativa solicitou `lvfi-reviewer`, mas o CLI 1.18.4 informou que subagentes não
podem ser o agente primário do comando e usou `lvfi-builder`; a seleção final de
modelo continuou explicitamente em GLM-5.2. A segunda usou `lvfi-builder`
explicitamente com GLM-4.7.

## 6. Governança criada

- `AGENTS.md` institucional conciso, com hierarquia documental, invariantes,
  paradas, segurança, gates e Graphify como índice auxiliar.
- Cinco agentes: `lvfi-builder`, `lvfi-routine-builder`, `lvfi-reviewer`,
  `lvfi-recovery` e `lvfi-release-auditor`.
- Oito comandos: `/lvfi-status`, `/lvfi-baseline`, `/lvfi-gates`,
  `/lvfi-diff-review`, `/lvfi-recover`, `/lvfi-release-check`, `/lvfi-report` e
  `/lvfi-graph-refresh`.
- Oito skills institucionais mais a skill oficial do Graphify.
- Workflow Git documentado: branch de tarefa, gates, commit autorizado, push de
  branch por humano/executor auditado, PR/CI, auditoria e merge autorizado.
- Matriz do Codex documentada com auditoria obrigatória para matemática,
  contrato/schema, serialização/hash, banco, segurança, integração crítica,
  release, piloto, pré-comercialização e fechamento do Método 1.

## 7. Permissões

Leitura interna é permitida, exceto ambiente, credenciais e chaves. Builders
podem editar; reviewer e release auditor não; recovery pede confirmação. Rede e
acesso externo pedem confirmação. Inspeção Git e gates conhecidos são
permitidos; add/commit/merge pedem confirmação.

Como padrões de comando do OpenCode 1.18.4 não distinguem de forma segura um
push implícito de branch de um push implícito para `main`, todo `git push` pelo
agente foi negado. Push autorizado fica fora do agente. Force push, reset hard,
clean amplo, rebase de main, instalação global e acesso a credencial foram
negados. A matriz simulada de dez casos passou, sem executar ação destrutiva.

## 8. Graphify e privacidade

A primeira extração foi local e determinística:
`graphify extract . --code-only --max-workers 1`, seguida por
`graphify cluster-only . --no-label`. Não houve chamada de LLM.

- 93 arquivos de código analisados; 82 documentos não-code ignorados; 5 itens
  não classificados.
- 984 nós, 4080 arestas e 29 comunidades.
- Extração: 30,22 s; clustering: 11,41 s.
- `graph.json`: 2.493.305 bytes; `graph.html`: 1.819.526 bytes;
  `GRAPH_REPORT.md`: 11.285 bytes; `manifest.json`: 20.818 bytes.
- Total de `graphify-out`: 7.170.365 bytes; grafo completo, relatório, cache e
  visualização são regeneráveis e ignorados pelo Git.
- `.graphifyignore` exclui VCS, venvs, caches, builds, outputs, `inputs/`,
  backups, temporários, logs, ambientes, credenciais, segredos e chaves.

A atualização incremental não foi executada porque poderia incluir Markdown
alterado em etapa semântica. Como não houve alteração de código, o grafo
code-only inicial continua válido para o produto congelado. Documentos
institucionais não saíram da máquina.

## 9. Consultas e comparação com fontes

- `MethodOneRequest → MethodOneFinalResult`: caminho de um salto, relação
  inferida `uses`.
- `orchestration.py`: o grafo localizou contratos, base rates, samples,
  multipliers, pricing, averages, `run_method_one` e a resolução de
  multiplicadores.
- T09: o grafo code-only localizou código de fixtures/regressão, mas não os
  documentos, limitação esperada do modo privado.

As respostas foram comparadas diretamente com
`contracts.py:479`, `orchestration.py:102`, `orchestration.py:153`, o backlog do
Método 1 (seção T09, linhas 383–414) e a estratégia de testes (M1-FX-001 a
M1-FX-014). As fontes confirmam T08 aceita, revisão de propriedade intelectual e
plano específico como dependências, fixtures sanitizadas e regressão normativa
separada da histórica.

## 10. Qualificação e gates

- Configuração resolvida: cinco agentes, oito comandos, plugin Graphify carregado
  uma vez, GLM-5.2 principal e GLM-4.7 econômico.
- Skills carregadas: oito institucionais, Graphify oficial e skill interna de
  customização do OpenCode.
- JSON: válido; frontmatter: cinco agentes, oito comandos e nove skills válidos.
- Pytest final: código de saída 0, `519 passed in 123.94s`.
- Cobertura: 3042/3042 statements e 1022/1022 branches, 100%.
- Ruff lint: aprovado; mypy strict: aprovado em 88 arquivos; compileall de
  `src` e `tests`: aprovado; pip check: aprovado.
- Hash 10×10 preservado:
  `11bdfc2a7addcf241a248f2a6bdfa888e7d4a6aa639095a809f59a11bba5d670`.
- Wheel, instalação limpa e release smoke: não aplicáveis e deliberadamente não
  executados pela proibição de construir nova versão.

Exceção documentada e preexistente, aceita pelo Product Owner: `ruff format`
`--check .` reprova exclusivamente três testes rastreados
por uma única linha em branco adicional no EOF. Os arquivos são idênticos ao
HEAD e não foram tocados por esta tarefa:

- `tests/integration/test_package_metadata.py`;
- `tests/unit/models/method_one/test_base_rates.py`;
- `tests/unit/models/method_one/test_multipliers.py`.

Corrigi-los modificaria o Pricing Engine, proibido pelo escopo. Portanto o gate
de formatação permanece como exceção a ser decidida pelo Product Owner; não foi
mascarado nem contornado.

## 11. Segurança, diff e status

Nenhum arquivo do produto foi modificado. `requirements-dev.lock`, matemática,
contratos, schemas, versões e hashes permanecem intactos. Nenhuma credencial foi
lida, impressa, copiada ou adicionada ao repositório. O grafo, caches, venvs,
binários e logs não serão versionados.

A busca por padrões de segredo passou sem achados; `git diff --check` passou
para os 41 arquivos de configuração/documentação; JSON e frontmatter passaram;
e a inicialização diagnóstica local do OpenCode concluiu com o plugin Graphify.
Os dois JSON criados/alterados por R21-OPS-001 passam em `ruff format --check`; Markdown, padrões de ignore e o plugin JavaScript estão fora dos formatos suportados por esse formatter e foram verificados por `git diff --check`, parse de JSON e carregamento do OpenCode.
O commit único autorizado pode ser criado após a revisão final.

## 12. Gate para migrar T09

T09 não foi iniciada e não está autorizada. A migração futura ao OpenCode exige:
qualificação externa do GLM concluída; decisão explícita sobre o gate Ruff;
configuração desta tarefa versionada; branch própria de T09; plano específico
aprovado; T08 aceita; revisão de propriedade intelectual; baseline limpa;
fixtures M1-FX-001–014 sanitizadas; e auditoria do Codex no fechamento do Método
1.