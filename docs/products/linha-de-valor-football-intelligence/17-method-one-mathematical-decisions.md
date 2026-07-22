# Decisões matemáticas aprovadas do Método 1

## 1. Finalidade

Este documento separa regras aprovadas, fatos observados, recomendações
históricas e pendências encerradas. Uma recomendação não se tornou aprovada por
estar registrada aqui, e o comportamento da planilha não substitui decisão
normativa.

## 2. Decisões já aprovadas

### 2.1 Fronteira com o Pricing Engine

**DECISÃO APROVADA:** o Método 1 gera taxas matemáticas normalizadas. O Pricing
Engine `1.0.0` recebe `PoissonRate` do mandante e visitante e calcula
distribuições, mercados, odds justas e linhas.

Consequências:

- o Método 1 não implementa Poisson;
- não escolhe mercados;
- não calcula odds ou linhas;
- não conhece bookmaker, EV, edge, stake ou Kelly;
- não modifica os schemas v1 do engine.

### 2.2 Precisão

**DECISÃO APROVADA — D-MATH-002 a D-MATH-004:** cálculos usam
`binary64/float`, valores não são arredondados internamente, e igualdade
numérica segue a `NumericPolicy`. Identidades, códigos, versões, IDs e ordem
exigem igualdade exata.

### 2.3 Quantidade e confiança

**DECISÃO APROVADA — D-MATH-007 e D-MATH-008:** menos de cinco observações é
insuficiente e não pode ser aprovado ou publicado; de cinco a nove possui baixa
confiança; dez ou mais é o padrão inicial. Quantidades solicitada, encontrada,
válida e excluída e motivos de exclusão são preservados.

### 2.4 Zero e ausência

**DECISÃO APROVADA — D-MATH-009 e D-MATH-010:** zero é observação válida.
Ausência, não aplicável, inválido e pendente de revisão são estados diferentes.
Ausência não entra no denominador e nunca vira zero.

### 2.5 Erros

**DECISÃO APROVADA — D-MATH-011:** erros são tipados. Falha crítica não vira
vazio, zero, `NaN` ou infinito.

### 2.6 Pesos

**DECISÃO APROVADA — D-MATH-014:** pesos são finitos, pertencem a `[0,1]` e
somam `1` dentro da tolerância. Configuração inválida não é normalizada
silenciosamente.

Esta decisão não aprova a fórmula na qual os pesos serão aplicados nem seus
valores globais iniciais.

### 2.7 Multiplicadores

**DECISÃO APROVADA — D-MATH-015:** multiplicadores são positivos e a faixa
inicial é `0,90–1,10`. Exceções exigem configuração versionada, justificativa,
autorização e auditoria.

Esta decisão não aprova como múltiplos fatores serão compostos.

### 2.8 Imutabilidade e versões

**DECISÃO APROVADA — D-MATH-016 e ADR-LVFI-008:** mudança em dados, filtros,
amostra, configuração, fórmula ou versão cria nova revisão. Resultados aprovados
não são reescritos.

## 3. Fatos observados na documentação

- O Método 1 é descrito como combinação de produção própria, concessão do
  adversário e ajustes contextuais.
- A fórmula conceitual documentada é uma soma ponderada.
- O exemplo documental usa produção `1,60`, concessão `1,10` e pesos `0,60` e
  `0,40`; o exemplo não está marcado como configuração padrão aprovada.
- A documentação prevê ajustes como HFA, força do adversário, forma,
  lesões/suspensões, ritmo e must-win.
- Faltas e cartões usam conjunto observado com árbitro no lugar de alguns
  fatores gerais.
- A composição puramente multiplicativa está explicitamente pendente.
- O preset observado é últimos dez jogos do mandante em casa e visitante fora,
  com opção de temporada anterior.
- O produto deve suportar também 5, 15, 20, temporada e período personalizado,
  nos recortes casa, fora e geral.

## 4. Fatos observados no XLSM

A inspeção histórica somente leitura confirmou:

- as séries são ordenadas por data decrescente;
- o relatório reserva dez posições recentes, sem regra explícita de desempate
  para partidas com a mesma data;
- as médias usam `AVERAGE`, que inclui zero numérico e ignora células vazias;
- a produção do mandante e a concessão do visitante são calculadas em séries
  separadas; o mesmo ocorre para o visitante e o mandante;
- a fórmula de base usa soma ponderada;
- o arquivo observado está configurado com pesos `0,5/0,5`;
- os multiplicadores observados são aplicados por produto após a base;
- não existe fórmula formal de pesos de recência;
- `IFERROR(..., "")` aparece ao redor das fórmulas e não será migrado como
  política de erros;
- o legado não preserva IDs, versão dos dados ou estados de disponibilidade por
  observação em seus resultados matemáticos.

Esses itens são evidência histórica, não aprovação.

## 5. Conflitos identificados e reconciliados

### C-M1-001 — Saída do Método 1

- documentação anterior: atribui probabilidades, odds e linhas ao Método 1;
- fronteira mais recente: Método 1 produz somente taxas e explicação;
- tratamento: a instrução mais recente controla a ENG-003; o Pricing Engine
  permanece responsável pelos produtos posteriores.

### C-M1-002 — Pesos exemplificados

- XLSM observado: `0,5/0,5`;
- exemplo textual: `0,6/0,4`;
- regra anterior aprovada: apenas intervalo e soma;
- tratamento final: `D-M1-002` aprova `0.50/0.50` como preset global do MVP; o
  exemplo `0.60/0.40` permanece somente histórico.

### C-M1-003 — Recência

- legado: ordenação e recorte;
- solicitação: pesos de recência configuráveis;
- estado normativo anterior: nenhuma fórmula aprovada;
- tratamento final: `D-M1-003` aprova `uniform/v1` e mantém decaimento fora da
  implementação inicial até calibração e nova aprovação.

### C-M1-004 — Gates de qualidade

- `D-MATH-007`: amostra `1–4` permite cálculo somente para auditoria;
- um `CalculationError(SAMPLE_INSUFFICIENT)` impediria qualquer resultado;
- tratamento final: `D-M1-006` autoriza resultado auditável com `SampleQuality`
  e warning para `1–4`; erro fica reservado a componente vazio ou
  dado/configuração inválidos.

### C-M1-005 — Contrato conceitual versus engine real

- arquitetura antiga descreve engine recebendo amostra e configuração;
- engine `1.0.0` real recebe apenas duas taxas, política e mercados;
- tratamento: Método 1 e engine são compostos pelo chamador, sem ampliar
  `PricingRequest` v1.

### C-M1-006 — Flags de bloqueio

- ADR-LVFI-006 menciona flags separadas para cálculo, aprovação e publicação;
- os tipos públicos atuais de erro/warning não possuem essas flags;
- tratamento final: `SampleQuality` carrega elegibilidade de workflow para os
  modelos, sem alterar os tipos públicos do engine nesta Initiative.

## 6. Decisões específicas aprovadas

### D-M1-001 — Fórmula canônica

Para o mandante:

`base_home = weight_own * mean_home_production + weight_opponent * mean_away_concession`

Para o visitante:

`base_away = weight_own * mean_away_production + weight_opponent * mean_home_concession`

A taxa final é `final_rate = base_rate * product(effective_multipliers)`. Cada
média usa seu próprio denominador de observações `OBSERVED`; a combinação não é
ponderada pela quantidade de partidas.

Exemplo manual com o preset inicial: `mean_home_production = 1.60` e
`mean_away_concession = 1.10` produzem
`base_home = 0.50 * 1.60 + 0.50 * 1.10 = 1.35`. Com multiplicadores efetivos
`1.05` e `0.95`, `final_home = 1.35 * 1.05 * 0.95 = 1.346625`. Se as médias
vierem, respectivamente, de dez e sete observações válidas, o resultado
permanece `1.35`: os denominadores independentes ficam auditáveis, mas não
alteram os pesos aprovados.

### D-M1-002 — Pesos globais iniciais

O preset global do MVP é `0.50` para produção própria e `0.50` para concessão
adversária, para mandante e visitante. Pesos são `binary64` finitos, pertencem a
`[0,1]`, somam `1` dentro da `NumericPolicy`, são versionados e aparecem na
explicação. Configuração inválida não é normalizada silenciosamente.

### D-M1-003 — Recência

O MVP usa `uniform/v1`: toda observação válida possui o mesmo peso. A ordem
canônica é instante da partida decrescente e `match_id` crescente. Políticas
não uniformes permanecem previstas no contrato, desativadas por padrão e fora
da implementação matemática inicial até calibração e aprovação futura.

### D-M1-004 — Multiplicadores

A composição é multiplicativa e usa a lista canônica de multiplicadores
efetivos. Todo valor é positivo e finito; `1.00` é neutro. A resolução aplica
precedência `partida → campeonato → global` e escolhe no máximo um valor por
categoria. Todos os candidatos considerados, escolhidos e descartados são
auditáveis, incluindo fonte e motivo.

A faixa inicial é `0.90–1.10`. Exceções seguem integralmente `D-MATH-015`:
configuração versionada, justificativa, autorização administrativa, auditoria e
aprovação do Product Owner quando mudarem a regra do modelo. A política
explícita determina warning ou erro; não existe clamp, composição aditiva ou
limitação silenciosa.

### D-M1-005 — Escopo estatístico inicial

A ENG-003 implementa somente taxas de gols por participante para primeiro tempo
e tempo regulamentar. Apenas `goals/first_half` e `goals/regulation_time` podem
ser elegíveis para `PoissonRate` nesta Initiative. Escanteios, finalizações,
chutes no gol, cartões e faltas ficam fora da implementação inicial e exigem
decisão matemática específica para qualquer distribuição futura.

### D-M1-006 — Amostras assimétricas e qualidade

Amostras assimétricas são permitidas e cada série usa seu denominador real. A
qualidade geral é a pior das quatro séries e o tamanho não muda os pesos:

- `0`: erro e bloqueio do cálculo;
- `1–4`: resultado auditável com warning grave, sem aprovação ou publicação;
- `5–9`: qualidade parcial, warning e publicação condicionada a permissão e
  justificativa;
- `10+`: qualidade adequada inicial, sem garantia estatística automática.

### D-M1-007 — Estados especiais de partida e observação

Partidas canceladas, anuladas, interrompidas, decididas por W.O. ou por disputa
de pênaltis são excluídas. Prorrogação não entra na taxa; somente o tempo
regulamentar claramente separado e validado pode ser usado. Estado não
classificável com confiança vira `PENDING_REVIEW`, fica fora da amostra e
bloqueia uso automático até revisão.

Os estados preservados são `OBSERVED`, `MISSING`, `NOT_APPLICABLE`, `INVALID`,
`SUSPECT` e `PENDING_REVIEW`. Somente `OBSERVED` entra na média. Zero observado
é válido; ausência nunca é convertida em zero.

## 7. Encerramento das pendências

| Pendência anterior | Decisão aprovada | Estado |
|---|---|---|
| `M1-PEND-001` | `D-M1-001` | Encerrada |
| `M1-PEND-002` | `D-M1-002` | Encerrada |
| `M1-PEND-003` | `D-M1-003` | Encerrada |
| `M1-PEND-004` | `D-M1-004` | Encerrada |
| `M1-PEND-005` | `D-M1-005` | Encerrada |
| `M1-PEND-006` | `D-M1-006` | Encerrada |
| `M1-PEND-007` | `D-M1-007` | Encerrada |

As decisões são coerentes com Company Context, Development Framework,
`D-MATH-001` a `D-MATH-016` e `ADR-LVFI-001` a `ADR-LVFI-010`. Elas não mudam
arquitetura, dependências, schemas ou hashes do Pricing Engine `1.0.0`; nenhum
novo ADR é necessário.

## 8. Decisões que não pertencem à ENG-003

- distribuição do Método 2;
- combinação de frequências do Método 3;
- seleção de fornecedor;
- persistência, APIs e interface;
- exposição de mercados, odds ou oportunidades;
- modelos para estatísticas futuras não aprovadas.

## 9. Estado do gate

As sete decisões `M1-PEND` estão encerradas pelas decisões `D-M1`. O estado é
**GO PARA PLANEJAMENTO DA LVFI-ENG-003-T02**. Esse GO não autoriza implementação
nem início da T02, que depende de plano próprio, aprovação explícita e gates
específicos. O detalhamento está em
[20-method-one-planning-gate.md](20-method-one-planning-gate.md).

## 10. Referências

- [Plano técnico](15-method-one-technical-plan.md)
- [Catálogo de contratos](16-method-one-contract-catalog.md)
- [Estratégia de testes](18-method-one-test-strategy.md)
- [Backlog](19-method-one-implementation-backlog.md)
