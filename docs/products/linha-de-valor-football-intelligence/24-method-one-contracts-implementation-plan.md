# Plano de implementação dos contratos base do Método 1

## 1. Identificação

- **Initiative:** LVFI-ENG-003
- **Task:** LVFI-ENG-003-T02-C02
- **Entrega:** plano documental predecessor da futura implementação dos contratos base de observação e amostra.
- **Estado:** planejamento técnico; não autoriza implementação nem alteração de código.
- **Rastreabilidade:** [15 — Plano técnico](15-method-one-technical-plan.md), [16 — Catálogo de contratos](16-method-one-contract-catalog.md), [17 — Decisões matemáticas](17-method-one-mathematical-decisions.md), [18 — Estratégia de testes](18-method-one-test-strategy.md), [19 — Backlog](19-method-one-implementation-backlog.md), [20 — Gate](20-method-one-planning-gate.md), [21 — Decisão do catálogo operacional](21-market-operational-catalog-decision.md), [22 — Plano do catálogo operacional](22-operational-catalog-implementation-plan.md) e [23 — Design do catálogo operacional](23-operational-catalog-implementation-design.md).

O Pricing Engine 1.0.0 permanece congelado. Este documento não aprova mudança de
pacote, schema, hash, contrato público ou versão.

## 2. Objetivo

Planejar a fundação compartilhável que representará observações de partidas,
amostras contextuais, exclusões e qualidade de dados do Método 1. Os contratos
futuros receberão dados já fornecidos em memória e preservarão identidade,
estado, ordem e evidência de auditoria.

O plano aplica D-M1-001 a D-M1-007, D-MATH-001 a D-MATH-016 e os ADRs vigentes.
Zero observado é válido; ausência nunca será convertida em zero; qualidade,
erros e publicação permanecerão explícitos e auditáveis.

## 3. Escopo e fronteira

A futura implementação da T02 fica limitada a contratos reutilizáveis sob
lvfi_pricing.models.samples. Eles serão puros, imutáveis e independentes de
estado externo.

Ficam fora do escopo: médias, recência, fórmula, pesos, multiplicadores,
Poisson, distribuições, mercados, odds, linhas, liquidação, Pricing Engine,
request/configuração/resultado do Método 1, serialização, hashing, I/O, banco,
rede, arquivos, ambiente, relógio, fornecedores e regras dos Métodos 2 e 3.

## 4. Arquitetura proposta

### 4.1 Fronteira futura

**RECOMENDAÇÃO:** lvfi_pricing.models.samples será a única fachada pública dos
contratos compartilhados. A fachada exporá somente tipos estáveis; módulos
internos não serão API de consumidores.

| Módulo futuro | Responsabilidade | Dependências permitidas |
|---|---|---|
| codes | enums e códigos canônicos | biblioteca padrão |
| observations | identidade, valor e observação individual | codes |
| series | filtros, definição e série contextual | codes, observations |
| exclusions | exclusões e motivos auditáveis | codes, observations |
| quality | contagens, classificação e gates | codes, exclusions |
| __init__ | fachada pública explícita | módulos internos |

A separação evita módulos monolíticos e ciclos, conforme
[ADR-LVFI-002](../../architecture/decisions/ADR-LVFI-002-organizacao-interna-do-motor.md).
Nenhum módulo importará engine, markets, distributions ou serialization.

### 4.2 Padrões obrigatórios

A implementação futura usará frozen dataclasses com slots, enums, tuplas e
tipos explícitos. Coleções públicas serão tuplas canonicalizadas. Validações
puras rejeitarão tipo incorreto, booleano usado como número, NaN, infinito e
estados incompatíveis. Instantes e versões serão entradas explícitas e datetime
exigirá timezone. Não haverá arredondamento, clamp ou normalização silenciosa,
conforme [ADR-LVFI-003](../../architecture/decisions/ADR-LVFI-003-representacao-numerica.md).

## 5. Contratos planejados

### 5.1 Códigos canônicos

Os seguintes códigos serão enums estáveis, com valores canônicos em minúsculas
para futura serialização:

- StatisticCode: goals, corners, shots, shots_on_target, cards e fouls;
- MatchPeriodCode: first_half e regulation_time;
- ParticipantRole: home e away;
- VenueCondition: home, away e overall;
- ObservationRole: production e concession;
- ObservationState: observed, missing, not_applicable, invalid, suspect e
  pending_review;
- MatchState, SampleWindowKind e SampleExclusionReason para partidas, janelas e
  motivos sem textos livres.

A existência de código não amplia o escopo matemático aprovado. Valor publicado
não será renomeado ou reutilizado; inclusão futura exigirá revisão de schema e
compatibilidade, conforme
[ADR-LVFI-008](../../architecture/decisions/ADR-LVFI-008-estrategia-de-versionamento.md).

### 5.2 Observação individual

MatchIdentity representará match_id, occurred_at timezone-aware e estado da
partida. ObservationValue representará valor, unidade compatível, estado e motivo
de qualidade codificado. MatchObservation ligará ambos a subject_id, opponent_id,
papel do participante, condição, papel da observação, estatística, período,
data_version e schema_version.

A identidade canônica será match_id + subject_id + statistic + period +
observation_role; posição em lista, arquivo ou fonte não a integra. Sujeito e
adversário serão distintos e IDs não poderão ser vazios.

Somente observed aceitará valor numérico finito e não negativo no escopo de
contagens, inclusive 0.0. Estados não observados exigirão valor ausente e não
serão convertidos em zero. Negativo, NaN, infinito, booleano, timestamp sem
timezone ou combinação inválida de estado e valor falharão explicitamente.

### 5.3 Série contextual

SampleFilter, SampleDefinition e SampleSnapshot representarão participante,
estatística, período, papel, condição, janela, corte temporal, filtros, versões
de dados e schema. A janela inicial representará last_n de 5, 10, 15 ou 20,
temporada completa e período personalizado; overall será suportado pela
infraestrutura, mas não pelo preset inicial.

As quatro séries futuras usarão a mesma estrutura:

1. produção do mandante em casa;
2. concessão do mandante em casa;
3. produção do visitante fora;
4. concessão do visitante fora.

Snapshots exporão observações usadas, exclusões, IDs considerados/usados e
contagens solicitada, encontrada, válida e excluída. A ordem canônica será
occurred_at decrescente e match_id crescente; duplicidade da identidade na
mesma série será inválida. Filtros e contagens deverão ser reconciliáveis sem
consulta externa.

### 5.4 Exclusões auditáveis

SampleExclusion preservará identidade da partida, motivo canônico, estado de
observação quando existente, campo relacionado e flags independentes de bloqueio
de cálculo e uso automático. Motivos mínimos incluem fora do filtro, posterior
ao corte, duplicidade, incompatibilidade, ausência, não aplicável, inválida,
suspeita e pendente de revisão.

Canceladas, anuladas, interrompidas, W.O. e pênaltis serão excluídos.
Prorrogação não integra regulation_time; somente segmento regulamentar separado
e validado poderá ser considerado. Estado não classificável será pending_review,
ficará fora da série e bloqueará uso automático. Nenhuma exclusão será
silenciosa.

### 5.5 Qualidade da amostra

SampleCounts, SampleQualityLevel e SampleQuality preservarão contagens,
classificação, códigos de motivo, warnings e flags independentes de cálculo,
aprovação e publicação.

| Observações válidas | Classificação | Efeito planejado |
|---:|---|---|
| 0 | empty | bloqueia cálculo; erro tipado |
| 1–4 | insufficient | permite apenas resultado auditável; bloqueia aprovação e publicação |
| 5–9 | low | emite warning; publicação depende de permissão e justificativa |
| 10+ | standard | patamar inicial, sem certificação estatística automática |

Cada série preservará denominador próprio. A agregação futura usará a pior
qualidade das quatro séries, mas essa agregação e qualquer cálculo estão fora da
T02. A classificação seguirá
[ADR-LVFI-006](../../architecture/decisions/ADR-LVFI-006-erros-e-alertas-tipados.md)
sem alterar os tipos públicos do engine.

## 6. Invariantes, validações e versionamento

- Contratos são comparáveis por conteúdo e imutáveis após construção.
- Tuplas de códigos, temporadas e IDs serão canonicalizadas, ordenadas e sem
  duplicidade quando a ordem não for semântica.
- found_count, valid_count, excluded_count, IDs e membros do snapshot deverão
  reconciliar exatamente; partida usada não poderá aparecer na mesma série como
  excluída.
- Versões de dado e schema serão obrigatórias, explícitas e estáveis. Mudança
  incompatível criará versão nova, sem reinterpretar snapshots existentes.
- A T02 não criará hash nem payload canônico. Serialização futura seguirá
  [ADR-LVFI-007](../../architecture/decisions/ADR-LVFI-007-serializacao-e-hashes.md):
  enums por código, timestamps em UTC, ausência como null, ordem semântica
  preservada e metadados voláteis fora da identidade matemática.

## 7. Estratégia de testes futura

Os testes serão criados somente em Task aprovada.

- **Unitários:** criação válida e inválida; zero observado; seis estados;
  timezone; coerência de valor/unidade/estatística/período; ordem; duplicidade;
  cortes; estados especiais; contagens; qualidade; exclusões e imutabilidade.
- **Property-based:** canonicalização independente da permutação de filtros;
  ordem determinística em datas empatadas; identidade única; invariantes de
  contagens; estados não observados fora do denominador; ausência de mutação
  observável e determinismo.
- **Regressão:** somente fixtures sintéticas e, quando revisadas, sanitizadas e
  minimizadas, sem dados reidentificáveis, conforme
  [ADR-LVFI-009](../../architecture/decisions/ADR-LVFI-009-estrategia-de-fixtures.md).

Os gates planejados incluem suíte completa, cobertura configurada, Ruff, mypy
strict, compileall, build, instalação limpa e pip check, usando
[ADR-LVFI-010](../../architecture/decisions/ADR-LVFI-010-ferramentas-e-dependencias.md).

## 8. Riscos e controles

| Risco | Controle planejado |
|---|---|
| Abstração compartilhada prematura | Limitar T02 a observação e amostra. |
| Acoplamento a mercados ou engine | Proibir imports dessas camadas e testar dependências. |
| Zero confundido com ausência | Validar estado e valor conjuntamente. |
| Exclusão silenciosa | Preservar motivo, identidade, estado e flags. |
| Hash futuro instável | Canonicalizar códigos e ordenar observações explicitamente. |
| Schema reutilizado | Versionar contratos e reter revisões referenciadas. |
| Mistura de Métodos 2 e 3 | Não incluir fórmulas, distribuição ou contratos de outros métodos. |
| Dados privados em regressão | Usar somente fixtures sintéticas ou sanitizadas revisadas. |

## 9. Sequência de implementação futura

1. **T03:** request, configuração, pesos, ajustes, explicações, resultado e
   elegibilidade do Método 1, sem cálculo.
2. **T04:** validação dos quatro snapshots e médias contextuais uniformes.
3. **T05:** combinação de produção e concessão conforme D-M1-001, D-M1-002 e
   D-M1-006.
4. **T06:** ajustes, qualidade agregada, erros e warnings.
5. **T07:** integração controlada com o Pricing Engine, sem o Método 1 chamá-lo.
6. **T08:** serialização e hashing versionados do Método 1.
7. **T09:** fixtures seguras e regressão consolidada.
8. **T10:** validação final, compatibilidade e decisão de release.

Cada Task exigirá plano aprovado, testes e gate próprio. Nenhuma etapa posterior
é autorizada por este documento.

## 10. Critérios de aceite futuros da T02

- contratos representam identidade, estados, filtros, exclusões, contagens e
  versões sem I/O ou dependência externa;
- zero observado e ausência permanecem distintos;
- snapshots são imutáveis, determinísticos, auditáveis e reconciliáveis;
- seis estados e exclusões especiais têm comportamento explícito;
- qualidade segue quatro faixas e mantém gates separados;
- não é implementada regra matemática do Método 1, 2 ou 3;
- engine 1.0.0, seus schemas, bytes e hashes permanecem compatíveis;
- testes, Ruff, mypy e suíte completa são aprovados no ambiente da Task.

## 11. Validação desta entrega documental

A entrega foi planejada contra os documentos 15–23, Company Context, R21
Development Framework, ADRs e D-MATH-001–016. A execução documental validará
links relativos, git diff --check, escopo do diff e ausência de alteração em
código, testes, dependências, package, schemas ou artefatos temporários.

## 12. Gate

Este plano não autoriza implementação. A autorização depende do aceite explícito
do Product Owner e de execução posterior em modo apropriado, dentro do escopo
aprovado. Alterações locais pré-existentes em packages/pricing-engine e
models/samples permanecem fora desta entrega e não são validadas, absorvidas ou
modificadas por ela.

PLANO PENDENTE DE APROVAÇÃO

A implementação dependerá de:

1. aprovação explícita do Product Owner;
2. execução em modo apropriado;
3. validação dos contratos e invariantes;
4. testes regressivos completos;
5. gate final da T02.
