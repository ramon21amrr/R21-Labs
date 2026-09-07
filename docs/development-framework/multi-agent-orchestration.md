# Orquestração multiagente

## Objetivo e princípios

O pool multiagente acelera tasks aprovadas sem ampliar escopo, substituir fontes
autoritativas ou reduzir qualidade. Os nove papéis são capacidades disponíveis,
não uma equipe obrigatória. O Lead ativa apenas o conjunto mínimo que reduz tempo
ou risco de forma verificável.

Antes de delegar, confirme contrato da task, base, branch, ambiente, escopo e gates.
Use `r21-repository-navigation` para navegação Graphify-first e confirme decisões
materiais nos arquivos originais. Reutilize `r21-quality-gates` para validação e
skills de domínio quando aplicáveis. Publicação continua separada e requer pedido
explícito do Product Owner e `r21-task-publication`.

## Arquitetura e papéis

| Papel | Responsabilidade | Ativação típica |
| --- | --- | --- |
| Lead / Orchestrator | interpreta contrato, monta dependências, define ownership, integra e encerra | sempre |
| Context Scout | localiza contratos e dependências, confirma fontes e entrega contexto mínimo | quando há exploração ou impacto |
| Backend / Data | API, PostgreSQL, migrations, repositories, services, schemas e persistência | mudança backend/dados |
| Frontend / UX | Next.js, TypeScript, UI, cliente API, acessibilidade e gates web | mudança frontend |
| Domain / Statistics | estatística, amostras, cálculos, Pricing Engine e contratos matemáticos | somente quando a camada é tocada |
| Test Engineer | testes, fixtures, regressões, edge cases e cobertura | quando testes independentes agregam valor |
| QA / Security Auditor | revisão independente de diff, contratos, secrets, N+1, erros e compatibilidade | checkpoint ou risco relevante |
| Documentation / Governance | docs, ADRs, registry, estado, YAML, handoffs e continuidade | quando o workflow exigir atualização |
| Release / Integrator | checkpoint, gates finais, staging e preparação Git | encerramento; publicação só autorizada |

O Lead evita edição funcional quando há executor proprietário da área. Scout, QA e
Release devem permanecer independentes sempre que essa separação aumentar a
qualidade da evidência.

## Seleção, dependências e paralelismo

1. Desenhe o menor grafo de dependências capaz de cumprir o contrato.
2. Separe descoberta, execução, verificação e integração.
3. Paralelize apenas nós independentes, com entradas estáveis e ownership disjunto.
4. Espere os predecessores antes de iniciar testes, docs ou integração que dependam
   de contratos ainda em mudança.
5. Limite padrão: até quatro executores simultâneos. Ultrapasse somente com áreas
   realmente independentes, zero sobreposição de arquivos e ganho esperado maior
   que custo de coordenação e tokens.

Fluxos mínimos comuns:

- backend simples: Lead → Scout → Backend → Tests → QA → Release;
- frontend: Lead → Scout → Frontend → Tests → QA → Release;
- full-stack: Lead → Scout → Backend + Frontend em paralelo → Tests → QA →
  Governance → Release;
- matemática: Lead → Scout → Domain → Tests → QA → Release.

Uma task localizada e de baixo risco pode permanecer single-agent. Não crie um
agente para repetir análise já válida, observar passivamente ou editar um arquivo
que outro executor já possui.

## Worktrees e ownership

Cada executor paralelo recebe uma worktree e branch próprias, derivadas da mesma
base autorizada, mais uma lista explícita de arquivos ou globs. O Lead registra o
ownership antes de iniciar o paralelismo. Dois agentes nunca editam simultaneamente
o mesmo arquivo; arquivos compartilhados viram dependência serial ou ficam sob um
único integrador.

Exemplos de ownership:

- Backend: `apps/api/**` e migrations explicitamente aplicáveis;
- Frontend: `apps/web/**`;
- Domain: pacote de domínio ou Pricing Engine expressamente autorizado;
- Docs: documentação definida no contrato, preferencialmente após estabilização.

O executor não atravessa seu limite para “ajudar”. Se descobrir mudança externa,
registra-a como bloqueio. A integração usa diff revisado e aplicação ordenada das
unidades coerentes na branch do Lead. Preserve branches/worktrees até confirmar
integração e gates. Nunca use force-push, `reset --hard`, clean amplo, reescrita de
histórico ou remoção que possa perder trabalho.

## Handoff e integração

Use somente o contexto necessário:

```text
STATUS:
FEITO:
ARQUIVOS:
CONTRATOS ALTERADOS:
TESTES:
BLOQUEIOS:
PRÓXIMA DEPENDÊNCIA:
```

Não repita roadmap, `AGENTS.md` ou regras institucionais. O receptor consulta o
grafo e as fontes originais se precisar de detalhe. Um handoff não substitui diff,
teste ou contrato.

O Lead integra na ordem do grafo de dependências, confirma que cada diff respeita
ownership, resolve conflitos pela fonte autoritativa — nunca escolhendo versões às
cegas — e executa testes focados após cada unidade de risco. QA revisa o conjunto
integrado. Governance atualiza continuidade somente quando exigido pelo workflow.
Release executa o checkpoint final e para antes de commit, push, PR ou merge sem
autorização explícita.

## Economia de contexto e esforço

- mantenha regras recorrentes em Skills e passe apenas objetivo, limites e aceite;
- faça Graphify-first com orçamento limitado e abra somente candidatos relevantes;
- peça ao Scout um mapa curto de arquivos, contratos, riscos e incertezas;
- distribua a cada agente apenas o contexto de sua área;
- reutilize handoffs e resultados ainda válidos; não duplique investigação;
- use testes focados na iteração e gates completos nos checkpoints;
- mantenha outputs compactos e registre evidência por caminho, comando e resultado.

Escolha esforço qualitativo conforme risco: **LOW** para navegação, documentação
simples, status e release mecânico; **MEDIUM** para implementação localizada,
testes e trabalho normal de frontend/backend; **HIGH** para arquitetura, schemas,
migrations críticas, matemática ou auditoria complexa. Não fixe modelo: use as
capacidades institucionalmente disponíveis no Codex.

## Troubleshooting e regras de parada

| Sinal | Ação |
| --- | --- |
| Grafo ausente, desatualizado ou inconclusivo | use busca direcionada, informe o fallback e confirme originais |
| Ownership sobreposto | pare os executores afetados; serialize ou redefina dono |
| Contrato mudou durante execução | congele integração e peça decisão ao Lead/Product Owner |
| Executor depende de saída instável | encerre paralelismo nessa aresta e aguarde predecessor |
| Conflito Git | preserve ambos os trabalhos, investigue contrato e integre manualmente |
| Gate falhou | registre primeiro erro e log; corrija no dono apropriado antes de avançar |
| Handoff excessivo ou ambíguo | reduza a fatos, arquivos, testes, bloqueios e próxima dependência |
| Necessidade fora do escopo | não implemente; registre e solicite decisão |
| Publicação não autorizada | pare após diff e gates; apresente a ação humana necessária |

Pare também diante de conflito entre autoridades, fonte crítica não confirmada,
segredo, ambiente não autorizado, mudança funcional não prevista ou risco de perda
de trabalho.

## Exemplos de ativação

Os templates em `templates/multi-agent-*.md` são prompts curtos reutilizáveis:

- `multi-agent-single-agent.md`: mudança localizada sem ganho de paralelismo;
- `multi-agent-backend-frontend.md`: dois executores independentes e integração;
- `multi-agent-mathematics.md`: contratos matemáticos protegidos;
- `multi-agent-audit.md`: revisão independente e read-only por padrão;
- `multi-agent-release.md`: gates e preparação, com publicação explicitamente
  condicionada à autorização.

Eles complementam `r21-multi-agent-orchestration`; regras detalhadas continuam nas
skills especializadas e nas fontes institucionais.

## Validação da R21-DEV-003

Em 2026-09-07, uma simulação controlada aplicou o fluxo Lead → Scout → dois
executores → integração → QA → release dry-run, sem tocar produto. O Scout foi
read-only. Os executores partiram do mesmo commit
`242375ac68236ba56307821afc267d871092423f`, em branches e worktrees separadas:

- Skill: ownership exclusivo de
  `.agents/skills/r21-multi-agent-orchestration/**`;
- documentação: ownership exclusivo do documento e dos cinco templates
  `multi-agent-*`.

Os dois lanes rodaram em paralelo, não editaram arquivos comuns e entregaram o
handoff padrão. No checkpoint imediato de integração sem commit, os sete arquivos
novos corresponderam byte a byte às fontes das worktrees por SHA-256. Depois, o
Lead acrescentou esta seção ao documento principal: a medição final reproduzível
passou a 6/7 hashes coincidentes, com essa única divergência esperada. Não houve
conflito nem retrabalho. As worktrees temporárias foram preservadas até QA e
removidas depois dos gates; branches sintéticas não foram publicadas.

### Benchmark simples

O benchmark usa métricas substitutas, não telemetria de tokens. O tempo sequencial
é a soma conservadora das janelas dos dois lanes; o paralelo é a janela real entre
a criação das worktrees e o último gate local.

| Indicador | Fluxo sequencial/repetitivo | Fluxo multiagente validado | Resultado |
| --- | ---: | ---: | --- |
| Tempo dos dois lanes | 481 s (proxy) | 263 s observados | redução aproximada de 45% |
| Leituras das 10 autoridades comuns | até 20, se repetidas por lane | 10 centralizadas + fallbacks dirigidos | evita até 10 releituras comuns |
| Prompt reutilizável | 9.193 caracteres do contrato completo | 686 caracteres em média nos 5 templates | redução aproximada de 92,5% |
| Conflitos Git | 0 por serialização | 0 com ownership disjunto | sem regressão |
| Retrabalho de integração | não medido | 0; 6/7 hashes finais, com 1 extensão do Lead | integração direta |

Esses números validam a redução operacional apenas para esta fixture documental.
Não provam ganho universal: tasks pequenas devem continuar single-agent, e lanes
com dependência ou arquivos compartilhados devem ser serializados.
