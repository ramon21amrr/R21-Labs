# Catálogo de contratos do Método 1

## 1. Finalidade

Este catálogo define os contratos conceituais da futura implementação do Método
1. Nenhuma dataclass, enum ou API Python é criada nesta Task.

Os nomes são recomendados, não assinaturas já implementadas. Alterações de nome
que preservem responsabilidade e invariantes não mudam a decisão matemática.

## 2. Princípios comuns

Todos os contratos deverão:

- ser imutáveis e comparáveis por conteúdo;
- usar apenas biblioteca padrão no runtime;
- rejeitar números não finitos;
- expor coleções como tuplas ordenadas e mapas somente leitura;
- possuir schema e versão explícitos quando serializáveis;
- separar dado de negócio de metadado operacional volátil;
- evitar textos livres como códigos de automação;
- preservar zero e ausência como estados diferentes;
- não executar I/O ou consultar estado externo.

## 3. Códigos fundamentais

### 3.1 `StatisticCode`

Responsabilidade: identificar a contagem analisada sem confundi-la com mercado
ou distribuição.

Códigos mapeados:

- `goals`;
- `corners`;
- `shots`;
- `shots_on_target`;
- `cards`;
- `fouls`.

**DECISÃO APROVADA — D-M1-005:** somente `goals`, nos períodos `first_half` e
`regulation_time`, integra o escopo inicial e pode ser elegível para Poisson.
A existência dos demais códigos no contrato compartilhável não autoriza sua
implementação, distribuição ou mercado nesta Initiative.

### 3.2 `MatchPeriodCode`

- `first_half`;
- `regulation_time`.

Períodos futuros exigem definição explícita. Prorrogação e pênaltis não são
inferidos como parte de `regulation_time`.

### 3.3 `ParticipantRole`

- `home`;
- `away`.

### 3.4 `VenueCondition`

- `home`;
- `away`;
- `overall`.

O contexto recomendado do primeiro escopo usa `home` para o mandante e `away`
para o visitante. `overall` pertence à infraestrutura de filtros, não ao preset
inicial.

### 3.5 `ObservationRole`

- `production`: valor a favor do participante analisado;
- `concession`: valor concedido pelo participante analisado.

### 3.6 `ObservationState`

- `observed`;
- `missing`;
- `not_applicable`;
- `invalid`;
- `suspect`;
- `pending_review`.

Somente `observed` participa de médias. `observed` com valor `0.0` é válido;
nenhum outro estado pode ser convertido em zero ou entrar no denominador.

## 4. `ObservationValue`

Responsabilidade: representar valor e estado sem sentinelas ambíguas.

Campos conceituais:

- `state: ObservationState`;
- `value: float | None`;
- `unit_code: str`;
- `quality_reason_code: str | None`;
- `source_version: str`;
- `schema_version: int`.

Invariantes:

- `observed` exige `float` finito e não negativo no escopo de contagens;
- `observed` aceita `0.0`;
- estados não observados não podem fornecer valor utilizável;
- ausência não é representada por zero, string vazia ou `NaN`;
- unidade deve ser compatível com `StatisticCode`;
- motivo usa código seguro e versionado, não mensagem livre como regra.

## 5. `MatchObservation`

Responsabilidade: ligar uma observação à identidade e ao contexto da partida.

Campos conceituais:

- `match_id: str`;
- `occurred_at: datetime` com timezone;
- `subject_id: str`;
- `opponent_id: str`;
- `subject_role: ParticipantRole`;
- `venue_condition: VenueCondition`;
- `observation_role: ObservationRole`;
- `statistic: StatisticCode`;
- `period: MatchPeriodCode`;
- `value: ObservationValue`;
- `data_version: str`;
- `observation_schema_version: int`.

Invariantes:

- sujeito e adversário são distintos;
- instante possui timezone e é entrada explícita;
- papel e condição são coerentes com a série;
- estatística, período e unidade são compatíveis;
- identidade canônica é
  `match_id + subject_id + statistic + period + observation_role`;
- nenhum identificador depende de posição em lista ou linha de arquivo.

## 6. `SampleWindow`

Responsabilidade: expressar a janela sem reduzir tudo a “últimos 10”.

Variantes:

- `last_n`, com `n` em `5`, `10`, `15` ou `20` no catálogo inicial;
- `full_season`;
- `custom_period`, com início e fim;
- extensões futuras somente por versão de schema.

Campos:

- `kind`;
- `requested_count: int | None`;
- `starts_at: datetime | None`;
- `ends_at: datetime | None`;
- `season_ids: tuple[str, ...]`;
- `include_previous_season: bool`;
- `version: str`.

Invariantes:

- campos aplicáveis dependem de `kind`;
- `last_n` exige quantidade positiva aprovada;
- período personalizado possui início menor ou igual ao fim;
- datas posteriores ao corte da análise não entram na amostra.

## 7. `SampleDefinition`

Responsabilidade: declarar filtros e intenção da amostra.

Campos:

- `sample_id: str`;
- `competition_ids: tuple[str, ...]`;
- `season_ids: tuple[str, ...]`;
- `subject_id: str`;
- `venue_condition: VenueCondition`;
- `statistic: StatisticCode`;
- `period: MatchPeriodCode`;
- `window: SampleWindow`;
- `cutoff_at: datetime`;
- `included_match_states: tuple[str, ...]`;
- `excluded_competition_types: tuple[str, ...]`;
- `filter_schema_version: int`;
- `definition_hash: str`.

Invariantes:

- filtros e tuplas possuem ordem canônica;
- `cutoff_at` é obrigatório e possui timezone;
- condição, estatística e período não podem divergir das observações;
- hash cobre somente conteúdo determinístico.

**DECISÃO APROVADA — D-M1-007:** cancelada, anulada, interrompida, W.O. e
disputa por pênaltis são estados inelegíveis. Prorrogação não pertence a
`regulation_time`; somente o segmento regulamentar claramente separado e
validado pode ser usado. Estado não classificável vira `pending_review`, é
excluído e bloqueia uso automático até revisão.

## 8. `SampleExclusion`

Responsabilidade: explicar por que uma partida considerada não foi usada.

Campos:

- `match_id: str`;
- `reason_code: str`;
- `observation_state: ObservationState | None`;
- `match_state: str | None`;
- `field: str | None`;
- `blocks_calculation: bool`;
- `blocks_automatic_use: bool`;

Motivos mínimos:

- fora do filtro;
- posterior ao corte;
- estado da partida não elegível;
- estatística ausente;
- não aplicável;
- inválida;
- suspeita;
- pendente de revisão;
- duplicada;
- incompatibilidade de estatística, período, participante ou versão.

## 9. `SampleSnapshot`

Responsabilidade: congelar a amostra efetivamente apresentada ao cálculo.

Campos:

- `definition: SampleDefinition`;
- `requested_count: int | None`;
- `found_count: int`;
- `valid_count: int`;
- `excluded_count: int`;
- `considered_match_ids: tuple[str, ...]`;
- `used_match_ids: tuple[str, ...]`;
- `observations: tuple[MatchObservation, ...]`;
- `exclusions: tuple[SampleExclusion, ...]`;
- `data_version: str`;
- `sample_schema_version: int`;
- `sample_hash: str`.

Invariantes:

- `found_count = len(considered_match_ids)`;
- `valid_count = len(observations) = len(used_match_ids)`;
- `excluded_count = len(exclusions)` para exclusões materiais do snapshot;
- IDs utilizados são únicos dentro da identidade da série;
- observações seguem `occurred_at DESC, match_id ASC`;
- nenhum ID utilizado pertence simultaneamente às exclusões;
- hash inclui definição, ordem, observações, exclusões e versão dos dados.

## 10. `SampleConfidence` e `SampleQuality`

### `SampleConfidence`

- `empty`;
- `insufficient` para `1–4`;
- `low` para `5–9`;
- `standard` para `10+`.

### `SampleQuality`

Campos:

- `confidence: SampleConfidence`;
- `requested_count`;
- `found_count`;
- `valid_count`;
- `excluded_count`;
- `missing_count`;
- `invalid_count`;
- `suspect_count`;
- `pending_review_count`;
- `calculation_allowed: bool`;
- `approval_allowed: bool`;
- `publication_allowed: bool`;
- `reason_codes: tuple[str, ...]`.

Regras:

- vazio impede cálculo;
- `1–4` permite somente resultado auditável e impede aprovação/publicação;
- `5–9` sinaliza baixa confiança e condiciona aprovação/publicação externa;
- `10+` é padrão inicial, não certificado estatístico;
- a qualidade agregada do Método 1 é a pior das quatro séries.

**DECISÃO APROVADA — D-M1-006:** uma série obrigatória vazia bloqueia o
cálculo. Séries com `1–4` observações permitem resultado auditável com warning
grave, mas bloqueiam aprovação e publicação. Séries com `5–9` mantêm warning e
publicação condicionada a permissão e justificativa. Tamanhos assimétricos são
permitidos, preservam denominadores independentes e geram warning; quantidade
de jogos não altera os pesos de combinação.

Esses campos pertencem aos contratos compartilháveis e não alteram
`CalculationError` ou `CalculationWarning` do engine `1.0.0`.

## 11. `RecencyWeightPolicy`

Responsabilidade: declarar de modo versionado se e como a ordem temporal afeta
uma média.

Campos conceituais:

- `code: str`;
- `version: str`;
- `parameters: mapping[str, safe scalar]`;
- `normalization_rule: str`;
- `tie_break_rule: str`;
- `policy_hash: str`.

**DECISÃO APROVADA — D-M1-003:** política inicial:

- `uniform/v1`;
- peso bruto `1.0` para cada observação válida;
- normalização matemática pelo denominador real da média;
- ordem canônica por instante decrescente e ID crescente;
- partidas inelegíveis excluídas antes da atribuição.

Recência não uniforme permanece prevista no contrato, desativada por padrão e
fora da implementação matemática inicial. Nenhuma política de decaimento será
aceita sem fórmula, calibração e decisão explícitas.

## 12. `MethodOneWeights`

Responsabilidade: combinar produção própria e concessão adversária por
participante.

Campos:

- `own_production: Weight`;
- `opponent_concession: Weight`;
- `version: str`;
- `source_scope: global | competition | match`;
- `configuration_hash: str`.

Invariantes:

- ambos finitos em `[0,1]`;
- soma igual a `1` dentro da `NumericPolicy`;
- nenhuma normalização automática;
- pesos de mandante e visitante podem ser configurados separadamente;
- nenhuma ponderação implícita por quantidade de jogos.

**DECISÕES APROVADAS — D-M1-001 e D-M1-002:** a fórmula combina produção
própria e concessão adversária sem ponderação adicional por tamanho de amostra.
O preset global inicial é `0.50/0.50` para mandante e visitante; valores,
origem, versão e hash aparecem na explicação auditável.

## 13. `ContextAdjustment`

Responsabilidade: representar um multiplicador aplicável e auditável.

Campos:

- `code: str`;
- `category_code: str`;
- `multiplier: Multiplier`;
- `applies_to: home | away`;
- `statistic_codes: tuple[StatisticCode, ...]`;
- `period_codes: tuple[MatchPeriodCode, ...]`;
- `order: int`;
- `source_scope: global | competition | match`;
- `justification_code: str | None`;
- `configuration_version: str`;
- `configuration_hash: str`.

Invariantes:

- código pertence ao catálogo da versão de fórmula;
- multiplicador é positivo;
- fora de `0,90–1,10` exige metadados de exceção aprovados;
- códigos e ordens não se repetem para o mesmo participante;
- ajuste não aplicável bloqueia configuração em vez de ser ignorado.

### 13.1 Resolução dos ajustes

**DECISÃO APROVADA — D-M1-004:** a resolução usa precedência
`match → competition → global` e escolhe no máximo um multiplicador efetivo por
categoria. A configuração e a explicação preservam, para cada candidato, fonte,
valor, versão, condição de escolhido ou descartado e motivo da decisão. Somente
os escolhidos compõem a lista ordenada efetiva.

O produto dos multiplicadores efetivos é aplicado à taxa base. `1.00` é neutro;
zero, negativos e não finitos são inválidos. Valores fora de `0.90–1.10` seguem
integralmente `D-MATH-015` e produzem warning ou erro conforme política
explícita, sem clamp ou composição aditiva silenciosa.

## 14. `MethodOneConfiguration`

Responsabilidade: congelar a configuração resolvida após precedência.

Campos:

- `configuration_id`;
- `configuration_version`;
- `formula_version`;
- `home_weights: MethodOneWeights`;
- `away_weights: MethodOneWeights`;
- `recency_policy: RecencyWeightPolicy`;
- `adjustments: tuple[ContextAdjustment, ...]`;
- `adjustment_resolution_trace` com candidatos escolhidos e descartados;
- `numeric_policy: NumericPolicy`;
- `resolved_sources: tuple[global | competition | match, ...]`;
- `replaces_configuration_id: str | None`;
- `configuration_hash`;
- `configuration_schema_version`.

Invariantes:

- a precedência já chega resolvida ao runtime puro;
- configuração não lê repositório externo;
- conteúdo e hash são imutáveis;
- toda fórmula ou política referenciada é suportada explicitamente.

## 15. `MethodOneRequest`

Responsabilidade: reunir exatamente uma execução estatística e temporal.

Campos:

- `target_match_id`;
- `home_participant_id`;
- `away_participant_id`;
- `statistic`;
- `period`;
- `home_production_sample`;
- `away_concession_sample`;
- `away_production_sample`;
- `home_concession_sample`;
- `configuration`;
- `data_version`;
- `method_version`;
- `request_schema_version`.

Invariantes:

- os quatro snapshots possuem estatística, período e versões compatíveis;
- participantes, papéis e condições correspondem ao nome do campo;
- nenhuma observação ocorre depois do corte;
- request possui no máximo 4.000 observações e 1.000 por snapshot;
- configuração e versões são suportadas;
- IDs da partida-alvo e participantes são distintos e válidos.

## 16. `ContextualAverage`

Responsabilidade: preservar uma média e sua evidência.

Campos:

- `sample_id`;
- `role: ObservationRole`;
- `participant_id`;
- `venue_condition`;
- `statistic`;
- `period`;
- `value: float`;
- `numerator: float`;
- `denominator: float`;
- `valid_count: int`;
- `used_match_ids`;
- `effective_weights: tuple[float, ...]`;
- `recency_policy_version`;
- `sample_quality`;
- `average_schema_version`.

Invariantes:

- valor, numerador e denominador são finitos;
- denominador é positivo;
- IDs e pesos correspondem um a um às observações utilizadas;
- média uniforme e ponderada usam `math.fsum`;
- arredondamento não ocorre no contrato.

## 17. `CombinationTerm` e `AdjustmentStep`

### `CombinationTerm`

- média contextual de origem;
- peso aplicado;
- contribuição `mean * weight`;
- papel de produção ou concessão;
- versão da fórmula.

### `AdjustmentStep`

- código do ajuste;
- valor antes;
- multiplicador;
- valor depois;
- ordem;
- versão e hash da configuração;
- justificativa segura quando aplicável.

Ambos preservam valores brutos e não recalculam a partir de valores exibidos.

## 18. `ParticipantRateExplanation`

Responsabilidade: explicar uma taxa de um participante.

Campos:

- `participant_id`;
- `production_average`;
- `opponent_concession_average`;
- `combination_terms`;
- `base_rate`;
- `adjustment_steps`;
- `refined_rate`;
- `quality`;
- `warnings`;
- `formula_version`.

Invariantes:

- contribuições somam a taxa base dentro da política numérica;
- etapas formam cadeia contínua entre base e refinada;
- taxa refinada é finita e não negativa;
- explicação contém toda evidência necessária sem buscar estado externo.

## 19. `MethodOneRateExplanation`

Responsabilidade: reunir explicações do mandante e visitante.

Campos:

- `home: ParticipantRateExplanation`;
- `away: ParticipantRateExplanation`;
- `overlapping_match_ids: tuple[str, ...]`;
- `resolved_configuration_summary`;
- `adjustment_resolution_trace`;
- `sample_hashes`;
- `explanation_schema_version`.

Sobreposição entre séries é visível e não significa, isoladamente, erro.

## 20. `MethodOneMetadata`

Campos:

- package target/version;
- method version;
- formula version;
- request, result, explanation e canonical schema versions;
- configuration version e hash;
- data version;
- quatro sample IDs e hashes;
- numeric policy;
- statistic e period;
- deterministic flag;
- warnings count;
- result hash.

Horário de execução, duração, host e correlação operacional não integram a
identidade matemática.

## 21. `MethodOneResult`

Responsabilidade: saída única do Método 1.

Campos:

- `request` ou identidade canônica equivalente;
- `home_rate: float`;
- `away_rate: float`;
- `quality: SampleQuality`;
- `explanation: MethodOneRateExplanation`;
- `metadata: MethodOneMetadata`;
- `warnings: tuple[CalculationWarning, ...]`;
- `errors: tuple[CalculationError, ...]`, vazio em resultado bem-sucedido.

Contrato de retorno recomendado:

`MethodOneResult | CalculationError`

Uma amostra `1–4` pode produzir `MethodOneResult` auditável com warning e gates
negativos. Amostra vazia ou configuração inválida retorna `CalculationError`.

## 22. `DistributionEligibility`

Responsabilidade: impedir que toda taxa matemática seja tratada como lambda.

Campos:

- `statistic`;
- `period`;
- `distribution_code`;
- `policy_version`;
- `eligible: bool`;
- `reason_code`;
- `approval_reference`.

Somente `eligible=true` permite criar `PoissonRate`. A decisão pertence à
configuração aprovada, não à magnitude da taxa.

Na ENG-003, somente `goals/first_half` e `goals/regulation_time` podem ter
`eligible=true`. Qualquer outra combinação retorna `MODEL_NOT_APPLICABLE` e não
é convertida em `PoissonRate`.

## 23. `MethodOnePricingEnvelope`

Responsabilidade: correlacionar Método 1 e Pricing Engine sem alterar os
contratos existentes.

Campos:

- `method_one_result_hash`;
- `pricing_result_hash`;
- `engine_version`;
- `method_version`;
- `integration_schema_version`;
- `statistic`;
- `period`;
- `home_rate_hex`;
- `away_rate_hex`;
- `envelope_hash`.

O envelope é criado pela camada de composição. O Método 1 não seleciona mercados
nem executa `run_pricing_engine`.

## 24. Erros bloqueadores

Usar os códigos existentes quando semanticamente adequados:

- `SAMPLE_EMPTY`;
- `MISSING_STATISTIC` quando impede todas as observações de um componente;
- `INVALID_STATISTIC`;
- `INCONSISTENT_DATA`;
- `INVALID_NUMBER`;
- `INVALID_WEIGHT`;
- `WEIGHTS_SUM_INVALID`;
- `INVALID_MULTIPLIER`;
- `CONFIGURATION_ERROR`;
- `MODEL_NOT_APPLICABLE`;
- `SCHEMA_VERSION_UNSUPPORTED`;
- `SERIALIZATION_ERROR`.

Erros adicionais só poderão ser incluídos se possuírem semântica nova e plano
compatível com a API pública do pacote.

Bloqueiam cálculo:

- componente obrigatório vazio;
- duplicidade dentro da mesma série;
- valor observado inválido ou não finito;
- observação pendente ou inválida sob política bloqueadora;
- incompatibilidade de participante, papel, estatística, período ou versão;
- pesos ou multiplicadores inválidos;
- fórmula, recência ou schema não suportados;
- payload acima do limite;
- taxa final negativa ou não finita.

## 25. Warnings mínimos

- `SAMPLE_INSUFFICIENT` para `1–4`;
- `SAMPLE_INSUFFICIENT` com contexto de baixa confiança para `5–9`;
- quantidade encontrada menor que a solicitada;
- tamanhos assimétricos;
- uso de temporada anterior;
- recorte personalizado;
- observações ausentes, não aplicáveis ou suspeitas excluídas;
- sobreposição de IDs entre séries;
- exceção aprovada de multiplicador fora da faixa padrão;
- política de recência não uniforme, quando futuramente aprovada.

Warnings usam contexto agregado seguro e não enumeram dados privados em
mensagens.

## 26. Contratos compartilháveis e exclusivos

Reutilizáveis por Métodos 2 e 3:

- códigos de estatística, período, participante, condição e qualidade;
- `ObservationValue`, `MatchObservation`;
- janela, definição, exclusão, snapshot e qualidade da amostra;
- política de recência;
- identidade, ordenação, versionamento e hashing de amostras.

Exclusivos do Método 1:

- pesos de produção/concessão;
- ajustes contextuais;
- configuração e request do Método 1;
- termos de combinação e passos de ajuste;
- explicação, resultado e metadados do Método 1;
- elegibilidade e envelope de integração específicos da taxa do Método 1.

Não devem ser compartilhados prematuramente:

- fórmula de força relativa do Método 2;
- eventos, numeradores e frequências do Método 3;
- regras de mercado e distribuição do Pricing Engine.

## 27. Relacionamentos

```text
SampleDefinition ──> SampleSnapshot ──> ContextualAverage
MatchObservation ──┘

MethodOneConfiguration ─┐
4 × SampleSnapshot ─────┼─> MethodOneRequest
                        └─> MethodOneResult
                              ├─> MethodOneRateExplanation
                              └─> MethodOneMetadata

MethodOneResult + DistributionEligibility
    ── caller ──> PoissonRate + PricingRequest
    ── engine ──> PricingResult
    ── composition ──> MethodOnePricingEnvelope
```

## 28. Versionamento recomendado

- sample schema v1;
- configuration schema v1;
- Method 1 request/result/explanation schema v1;
- canonical Method 1 schema v1;
- integration envelope schema v1;
- formula version incorpora `D-M1-001` e `D-M1-004`;
- method version `1.0.0` somente após gate matemático;
- pacote alvo `1.1.0` na validação final da ENG-003.

## 29. Referências

- [Plano técnico](15-method-one-technical-plan.md)
- [Decisões matemáticas](17-method-one-mathematical-decisions.md)
- [Estratégia de testes](18-method-one-test-strategy.md)
- [Backlog](19-method-one-implementation-backlog.md)
- [Gate](20-method-one-planning-gate.md)
