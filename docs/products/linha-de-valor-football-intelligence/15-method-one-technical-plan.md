# Plano técnico do Método 1 — médias com contexto

## 1. Identificação e estado

- **Initiative:** `LVFI-ENG-003`
- **Task:** `LVFI-ENG-003-T01`
- **Entrega:** planejamento documental do Método 1
- **Estado:** decisões `D-M1-001` a `D-M1-007` aprovadas; implementação não autorizada sem plano próprio da Task
- **Dependência:** Pricing Engine `1.0.0`, encerrado no commit `7da4b0bc8c980597ae970ef4165b94a649af4b94`
- **Gate detalhado:** [20-method-one-planning-gate.md](20-method-one-planning-gate.md)

Esta Task não implementa código, contratos Python, banco, API, interface, I/O,
integrações externas ou os Métodos 2 e 3.

## 2. Resumo executivo

O Método 1 transformará quatro amostras estatísticas contextualizadas em duas
taxas esperadas: uma para o mandante e outra para o visitante. Cada taxa deverá
ser acompanhada por explicação completa da amostra, médias, pesos, ajustes,
qualidade, versões e hashes que a produziram.

**DECISÃO APROVADA:** o Pricing Engine `1.0.0` continuará recebendo taxas
matemáticas já normalizadas. Poisson, probabilidades, mercados, odds justas e
linhas permanecem responsabilidades exclusivas do engine.

**RECOMENDAÇÃO:** o Método 1 deverá viver no pacote existente, sob
`lvfi_pricing.models`, usando contratos de amostra compartilháveis, sem alterar
o comportamento ou os schemas v1 do Pricing Engine.

**DECISÃO APROVADA:** as sete decisões matemáticas do Método 1 foram
formalizadas como `D-M1-001` a `D-M1-007`. Essa aprovação remove o bloqueio de
produto para planejar a T02, mas não autoriza sua implementação nem seu início.

## 3. Fontes e ordem de autoridade

Este plano foi confrontado, na ordem aplicável, com:

1. Company Context e R21 Development Framework;
2. documentação completa do produto LVFI;
3. decisões `D-MATH-001` a `D-MATH-016`;
4. ADR-LVFI-001 a ADR-LVFI-010;
5. implementação pública e validação final do Pricing Engine `1.0.0`;
6. histórico Git da LVFI-ENG-001 e LVFI-ENG-002;
7. planilha e materiais legados, somente como evidência histórica.

Em caso de divergência, uma decisão explícita e mais recente do Product Owner
prevalece. Evidência do legado não aprova comportamento futuro.

## 4. Fronteira funcional

### 4.1 Responsabilidades do Método 1

- receber observações e amostras já fornecidas em memória;
- validar contratos, qualidade, consistência e configuração;
- calcular médias contextuais de produção e concessão;
- combinar as médias conforme fórmula versionada e aprovada;
- aplicar somente ajustes explicitamente aprovados;
- produzir taxas não negativas, explicação e metadados auditáveis;
- indicar qualidade, warnings e erros tipados;
- produzir conteúdo canônico e hashes próprios;
- permitir conversão explícita para `PoissonRate` somente quando a combinação
  estatística/período/distribuição estiver aprovada.

### 4.2 Fora da fronteira

O Método 1 não deverá:

- buscar, importar, persistir ou corrigir dados;
- conhecer Excel, fornecedores, banco, rede, arquivos ou variáveis de ambiente;
- selecionar partidas em sistemas externos;
- calcular Poisson, probabilidades ou mercados;
- calcular odds, linhas principais, edge, EV, stake ou Kelly;
- conhecer bookmakers, recomendações ou Value Tracker;
- decidir sozinho que uma estatística segue Poisson;
- incorporar regras dos Métodos 2 e 3.

## 5. Entradas matemáticas

Uma execução representa uma estatística, um período e uma partida-alvo. Ela
recebe quatro snapshots independentes:

1. produção do mandante na condição casa;
2. concessão do visitante na condição fora;
3. produção do visitante na condição fora;
4. concessão do mandante na condição casa.

Também são entradas obrigatórias:

- identificador da partida-alvo;
- estatística e unidade canônicas;
- período do jogo;
- participantes e condição de cada snapshot;
- definição e versão dos filtros;
- quantidades solicitada, encontrada, válida e excluída;
- observações e IDs das partidas consideradas e utilizadas;
- versão e hash autorizado dos dados;
- versão da fórmula e schemas;
- configuração resolvida de pesos e ajustes;
- política numérica explícita.

Entradas opcionais:

- data de corte fornecida pelo chamador;
- temporadas adicionais explicitamente selecionadas;
- recorte personalizado;
- política de recência explícita, `uniform/v1` no MVP;
- ajustes contextuais aprovados;
- justificativas e referências de configuração;
- metadados seguros de correlação, fora do hash matemático quando voláteis.

## 6. Representação das observações e amostras

Os contratos completos estão no
[catálogo de contratos](16-method-one-contract-catalog.md). Em síntese:

- estatística, período, participante, condição e estado usam códigos canônicos;
- zero observado é `OBSERVED` com valor `0.0`;
- ausência, não aplicável, inválido, suspeito e pendente de revisão não usam
  zero como sentinela;
- cada observação preserva `match_id`, instante, sujeito, adversário, papel de
  produção ou concessão e versão dos dados;
- snapshots usam tuplas em ordem canônica e registram todas as exclusões;
- o conjunto efetivamente utilizado possui IDs e hash de conteúdo próprios.

## 7. Formação das quatro médias

Para uma série `S` com observações válidas `x_i`, a média uniforme é:

`mean(S) = math.fsum(x_i) / n_valid`

Somente observações `OBSERVED` participam. Zeros participam normalmente.
Ausentes e não aplicáveis são excluídos com motivo. Inválidos, suspeitos e
pendentes seguem a política de qualidade, sem coerção silenciosa.

As médias são:

- `home_production_mean`: valores a favor do mandante em casa;
- `home_concession_mean`: valores contra o mandante em casa;
- `away_production_mean`: valores a favor do visitante fora;
- `away_concession_mean`: valores contra o visitante fora.

Se uma política de recência vier a ser aprovada, a média ponderada será:

`weighted_mean(S) = math.fsum(w_i * x_i) / math.fsum(w_i)`

Os pesos deverão ser finitos e não negativos, e o denominador deverá ser
positivo. A geração dos pesos não poderá ser implícita.

## 8. Combinação de produção e concessão

**FATO OBSERVADO:** o legado calcula uma soma ponderada entre produção própria
e concessão adversária.

**DECISÃO APROVADA — D-M1-001:** adotar a combinação aritmética ponderada:

`home_base = home_own_weight * home_production_mean + home_opponent_weight * away_concession_mean`

`away_base = away_own_weight * away_production_mean + away_opponent_weight * home_concession_mean`

Para cada participante, os dois pesos deverão ser `Weight` `binary64` finitos,
estar em `[0,1]` e somar `1` dentro da `NumericPolicy`. Não haverá normalização
silenciosa.

Cada média usa seu próprio denominador de observações `OBSERVED`. A combinação
não é ponderada novamente pelo número de partidas: o tamanho da amostra afeta
qualidade e warnings, não o significado dos pesos.

**DECISÃO APROVADA — D-M1-002:** o preset global inicial é `0.50/0.50` para
produção própria e concessão adversária, tanto para o mandante quanto para o
visitante. Os pesos e sua origem são versionados e aparecem na explicação.
Outras combinações poderão ser configuradas em versões futuras.

## 9. Ajustes contextuais

**FATO OBSERVADO:** o legado multiplica a média base por fatores contextuais. O
conjunto geral contém HFA, força do adversário, forma, lesões/suspensões, ritmo
e must-win. Faltas e cartões usam árbitro no conjunto observado.

**DECISÃO APROVADA — D-MATH-015:** multiplicadores são positivos; a faixa
inicial é `0,90–1,10`; exceções são versionadas, justificadas e auditadas.

**DECISÃO APROVADA — D-M1-004:** para a lista canônica de ajustes efetivos:

`refined_rate = base_rate * math.prod(multiplier_i)`

O valor neutro é `1.00`. Somente multiplicadores positivos e finitos podem ser
aplicados. Para cada categoria, a configuração resolve no máximo um valor pela
precedência `partida → campeonato → global`; todos os candidatos considerados,
o escolhido e os descartados preservam fonte e motivo na auditoria. A ordem de
aplicação pertence ao catálogo versionado e cada etapa registra valor anterior,
multiplicador e valor posterior.

Valores fora de `0.90–1.10` seguem integralmente `D-MATH-015`: exigem
configuração versionada, justificativa, autorização administrativa, auditoria e
aprovação do Product Owner quando mudarem a regra do modelo. A política
explícita decide entre warning e erro; nenhuma limitação ou composição aditiva
é silenciosa.

## 10. Pesos de recência

**FATO OBSERVADO:** o XLSM ordena jogos por data decrescente e exibe até dez,
mas não aplica pesos formais de recência nem desempata datas iguais.

**DECISÃO APROVADA — D-M1-003:** o MVP usa `uniform/v1`, equivalente a
recência não uniforme desativada. Cada observação `OBSERVED` recebe o mesmo peso
matemático.

Ordem canônica dos snapshots:

1. instante da partida decrescente;
2. `match_id` crescente como desempate estável.

Partidas canceladas, anuladas, interrompidas, decididas por W.O. ou por disputa
de pênaltis são excluídas antes da ponderação. A prorrogação não entra na taxa;
somente o segmento de tempo regulamentar claramente separado e validado pode
ser usado. Estado não classificável com confiança vira `PENDING_REVIEW`, fica
fora da amostra e bloqueia uso automático até revisão.

Uma futura política não uniforme deverá declarar fórmula, parâmetros,
normalização, versão, aplicabilidade e testes. Nenhum decaimento será escolhido
apenas por existir no legado ou por conveniência técnica.

## 11. Quantidade e qualidade da amostra

Conforme `D-MATH-007` e `D-MATH-008`:

- `0` observações válidas em componente obrigatório: média indefinida e erro;
- `1–4`: cálculo somente para auditoria, qualidade insuficiente;
- `5–9`: baixa confiança, warning explícito e publicação condicionada a
  permissão e justificativa;
- `10+`: confiança padrão inicial, sem garantia estatística.

O resultado agregado herda a pior qualidade entre os quatro snapshots.

**DECISÃO APROVADA — D-M1-006:** tamanhos assimétricos são aceitos. Cada média
usa seu denominador real, a diferença de tamanho gera warning e permanece
visível na explicação. A qualidade geral corresponde à pior das quatro séries.

## 12. Dados ausentes, inválidos e zeros

- `OBSERVED(0.0)` entra no numerador e denominador;
- `MISSING` não entra e mantém motivo de ausência;
- `NOT_APPLICABLE` não entra e não é tratado como ausência;
- `INVALID` não entra na média e bloqueia sob a política aplicável;
- `PENDING_REVIEW` não entra na média e bloqueia uso automático;
- `SUSPECT` não entra na média e gera warning até revisão explícita;
- nenhum estado é convertido em zero, vazio ou `NaN`;
- valor observado deve ser finito, compatível com a unidade e não negativo no
  escopo inicial de contagens.

**DECISÃO APROVADA — D-M1-007:** somente `OBSERVED` participa da média.
`OBSERVED(0.0)` continua sendo uma observação válida; ausência nunca é
convertida em zero.

## 13. Duplicidade e sobreposição

Uma observação é única dentro de uma série pela identidade:

`match_id + subject_id + statistic + period + role`

Repetição dessa identidade bloqueia o snapshot. Uma mesma partida pode aparecer
legitimamente em séries diferentes, por exemplo como produção de um time e
concessão do outro. Essa sobreposição será registrada, não removida, porque as
séries representam papéis distintos e não são agrupadas em uma média única.

## 14. Escopo estatístico

**DECISÃO APROVADA — D-M1-005:** o escopo inicial da ENG-003 é:

- estatística: gols por participante;
- períodos: primeiro tempo e tempo regulamentar completo;
- contextos: mandante em casa e visitante fora;
- saída: taxa esperada do mandante e do visitante.

Gols do mandante, gols do visitante e total de gols são mercados derivados
posteriormente pelo Pricing Engine a partir das mesmas taxas.

Contratos comuns poderão representar escanteios, finalizações, chutes no gol,
cartões e faltas no futuro. Essas estatísticas ficam fora da implementação
inicial e não são elegíveis para `PoissonRate` nesta Initiative; qualquer uso
futuro exige decisão matemática específica sobre distribuição, calibração e
catálogo.

## 15. Integração com o Pricing Engine 1.0.0

O fluxo de composição será:

1. calcular `MethodOneResult`;
2. verificar estatística, período, qualidade e elegibilidade de distribuição;
3. criar `PoissonRate` para as taxas refinadas do mandante e visitante;
4. criar `PricingRequest` com os mercados solicitados pelo chamador;
5. executar `run_pricing_engine`;
6. preservar separadamente a explicação do Método 1 e o `PricingResult`;
7. criar um envelope de integração que correlacione ambos pelos hashes.

O Método 1 não escolherá mercados nem chamará o engine internamente. A camada de
composição fará isso de modo explícito. O schema v1 de `PricingRequest`, o
schema canônico v1 e os hashes já congelados do engine não serão alterados.

Primeiro tempo e partida completa exigem execuções separadas porque o contrato
atual do engine recebe um único par de taxas e não carrega período.

## 16. Arquitetura e dependências

Estrutura futura recomendada, não criada nesta Task:

```text
lvfi_pricing/
├── models/
│   ├── samples/
│   └── method_one/
└── serialization/
    └── method_one.py
```

Direção permitida:

```text
core + domain
      ↓
sample contracts
      ↓
Method 1
      ↓
Method 1 serialization

Method 1 result ── caller/composition ──> PoissonRate + PricingRequest
Pricing Engine 1.0.0 ──────────────────> PricingResult
```

Restrições:

- `core`, `domain`, distribuições e mercados não importam Método 1;
- Método 1 não importa mercados, orquestrador ou serialização;
- serialização pode depender dos contratos do Método 1, nunca o inverso;
- futuros Métodos 2 e 3 podem reutilizar contratos de amostra, não regras de
  combinação ou ajustes do Método 1;
- persistência e fornecedores ficam fora do grafo matemático.

## 17. Determinismo, imutabilidade e ausência de I/O

- contratos congelados, `slots`, tuplas e mapas somente leitura;
- ordenação canônica antes de médias, serialização e hash;
- `math.fsum` para somas relevantes;
- nenhuma dependência de relógio, UUID aleatório, `hash()` nativo ou estado
  global mutável;
- timestamps e versões são entradas explícitas;
- nenhuma rede, arquivo, banco, shell, subprocesso, variável de ambiente,
  logging de saída ou execução dinâmica;
- mensagens e contextos de erros não carregam valores privados desnecessários.

## 18. Versionamento, serialização e hashes

Eixos independentes:

- pacote: alvo recomendado `1.1.0` após validação final;
- Método 1: SemVer próprio, inicialmente `1.0.0` após aprovação matemática;
- fórmula: identificador e SemVer próprios;
- configuração: revisão imutável, versão e hash;
- sample schema, request schema, result schema e integration schema: v1;
- dados e snapshots: versão declarada e SHA-256 do conteúdo autorizado;
- resultado: hash canônico separado;
- Pricing Engine: permanece `1.0.0` e schema canônico v1.

Floats serão serializados por `float.hex()`. O hash do Método 1 incluirá fórmula,
configuração resolvida, snapshots, ordem, IDs, pesos, ajustes, política numérica,
taxas e schemas. Horário de execução, duração, host, processo e caminhos locais
ficam fora.

## 19. Decisões aprovadas e rastreabilidade

1. `M1-PEND-001 → D-M1-001`: fórmula canônica de combinação aprovada.
2. `M1-PEND-002 → D-M1-002`: pesos globais iniciais `0.50/0.50` aprovados.
3. `M1-PEND-003 → D-M1-003`: recência uniforme `uniform/v1` aprovada.
4. `M1-PEND-004 → D-M1-004`: composição multiplicativa aprovada.
5. `M1-PEND-005 → D-M1-005`: escopo inicial de gols e elegibilidade para
   Poisson aprovados.
6. `M1-PEND-006 → D-M1-006`: amostras assimétricas aprovadas.
7. `M1-PEND-007 → D-M1-007`: estados especiais de partida aprovados.

As sete pendências estão encerradas. O gate passa a **GO PARA PLANEJAMENTO DA
LVFI-ENG-003-T02**, sem autorizar implementação ou início da T02.

## 20. Segurança e limites

- máximo inicial recomendado de 1.000 observações por snapshot e 4.000 por
  request;
- IDs e códigos devem possuir limites documentados e caracteres seguros;
- nenhuma coleção mutável ou payload arbitrário;
- ajustes limitados ao catálogo versionado;
- fixtures exclusivamente sintéticas ou sanitizadas e minimizadas;
- nenhuma mensagem com nomes, partidas, fontes, caminhos ou dados privados;
- rejeição antecipada de payload excessivo antes de cálculo ou serialização.

## 21. Desempenho

O cálculo deve ser `O(n)` no total de observações e realizar uma passagem por
snapshot, sem recomputar médias ou hashes dentro da mesma execução.

Orçamento inicial recomendado para benchmark sintético em CPython 3.13, processo
único e ambiente documentado:

- quatro snapshots de 20 observações: p95 de até 10 ms;
- quatro snapshots de 1.000 observações: p95 de até 100 ms;
- memória adicional por request máximo: até 10 MiB;
- reportar aquecimento, iterações, mediana, p95 e ambiente.

Esses valores são orçamento de engenharia a validar, não SLA de produto.

## 22. Entregas relacionadas

- [Catálogo de contratos](16-method-one-contract-catalog.md)
- [Decisões matemáticas e pendências](17-method-one-mathematical-decisions.md)
- [Estratégia de testes](18-method-one-test-strategy.md)
- [Backlog de implementação](19-method-one-implementation-backlog.md)
- [Gate de planejamento](20-method-one-planning-gate.md)

## 23. Referências

- [Regras de negócio e catálogo](03-business-rules-and-market-catalog.md)
- [Modelos de precificação](04-pricing-models.md)
- [Requisitos](05-requirements.md)
- [Domínio e modelo de dados](06-domain-and-data-model.md)
- [Arquitetura](07-architecture.md)
- [MVP, roadmap e validação](11-mvp-roadmap-and-validation.md)
- [Baseline matemática](12-dynamic-audit-and-mathematical-baseline.md)
- [Plano técnico do Pricing Engine](13-pricing-engine-technical-plan.md)
- [Validação final do Pricing Engine](14-pricing-engine-final-validation.md)
