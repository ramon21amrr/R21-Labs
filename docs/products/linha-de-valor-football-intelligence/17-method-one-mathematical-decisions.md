# Decisões matemáticas e pendências do Método 1

## 1. Finalidade

Este documento separa regras aprovadas, fatos observados, recomendações e
decisões pendentes. Uma recomendação não se torna aprovada por estar registrada
aqui, e o comportamento da planilha não substitui decisão normativa.

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

## 5. Conflitos identificados

### C-M1-001 — Saída do Método 1

- documentação anterior: atribui probabilidades, odds e linhas ao Método 1;
- fronteira mais recente: Método 1 produz somente taxas e explicação;
- tratamento: a instrução mais recente controla a ENG-003; o Pricing Engine
  permanece responsável pelos produtos posteriores.

### C-M1-002 — Pesos exemplificados

- XLSM observado: `0,5/0,5`;
- exemplo textual: `0,6/0,4`;
- regra aprovada: apenas intervalo e soma;
- tratamento: nenhum valor será chamado de padrão até `M1-PEND-002`.

### C-M1-003 — Recência

- legado: ordenação e recorte;
- solicitação: pesos de recência configuráveis;
- estado normativo: nenhuma fórmula aprovada;
- tratamento: recomendar política uniforme no MVP e manter decaimento fora do
  escopo até decisão.

### C-M1-004 — Gates de qualidade

- `D-MATH-007`: amostra `1–4` permite cálculo somente para auditoria;
- um `CalculationError(SAMPLE_INSUFFICIENT)` impediria qualquer resultado;
- tratamento recomendado: retornar resultado auditável com `SampleQuality` e
  warning; reservar erro para componente vazio ou dado/configuração inválidos.

### C-M1-005 — Contrato conceitual versus engine real

- arquitetura antiga descreve engine recebendo amostra e configuração;
- engine `1.0.0` real recebe apenas duas taxas, política e mercados;
- tratamento: Método 1 e engine são compostos pelo chamador, sem ampliar
  `PricingRequest` v1.

### C-M1-006 — Flags de bloqueio

- ADR-LVFI-006 menciona flags separadas para cálculo, aprovação e publicação;
- os tipos públicos atuais de erro/warning não possuem essas flags;
- tratamento recomendado: `SampleQuality` carrega elegibilidade de workflow
  para os modelos, sem alterar os tipos públicos do engine nesta Initiative.

## 6. Recomendações técnicas

### R-M1-001 — Média de cada série

Usar média aritmética uniforme das observações válidas no MVP:

`mean = math.fsum(values) / valid_count`

Motivo: corresponde à semântica documentada e observada sem introduzir
decaimento não aprovado.

### R-M1-002 — Combinação

Usar média aritmética ponderada de produção e concessão, com um par de pesos por
participante. Não ponderar novamente pelo número de jogos.

Motivo: mantém significado explícito dos pesos e evita que assimetria altere a
configuração de negócio de forma implícita.

### R-M1-003 — Pesos iniciais

Exigir configuração global explícita. Se o Product Owner desejar um preset
neutro, recomendar `0,5/0,5`. Não promover o exemplo `0,6/0,4` a padrão.

### R-M1-004 — Recência

Usar `uniform/v1` no MVP. A ordem canônica continua registrada para auditoria e
hash. Qualquer política não uniforme deverá ser calibrada e aprovada em versão
posterior.

### R-M1-005 — Ajustes

Se aprovada, aplicar lista ordenada de multiplicadores por produto, preservando
cada etapa. Rejeitar ajustes desconhecidos, duplicados ou não aplicáveis.

### R-M1-006 — Assimetria

Aceitar amostras assimétricas, manter denominadores separados e emitir warning.
A qualidade agregada corresponde à pior série.

### R-M1-007 — Escopo inicial

Começar por gols de primeiro tempo e tempo regulamentar. Mapear as demais
contagens, mas não convertê-las em `PoissonRate` sem aprovação de distribuição.

### R-M1-008 — Estados de partida

Começar conservadoramente com partidas encerradas no tempo regulamentar e
estatística compatível com o período. Excluir canceladas. Não inferir política
para W.O., anulação, interrupção, prorrogação ou pênaltis.

## 7. Decisões pendentes bloqueadoras

### M1-PEND-001 — Fórmula canônica de combinação

- **Alternativa A — recomendada:** média aritmética ponderada.
- **Alternativa B:** média geométrica ponderada.
- **Alternativa C:** outra função explicitamente especificada.
- **Impacto:** define todas as taxas e regressões do Método 1.
- **Decisão necessária:** Product Owner deve aprovar fórmula e versão inicial.

### M1-PEND-002 — Pesos globais iniciais

- **Alternativa A — recomendada:** `0,5/0,5` como preset neutro explícito.
- **Alternativa B:** `0,6/0,4`, conforme exemplo textual.
- **Alternativa C:** nenhuma configuração padrão; valor global obrigatório por
  implantação.
- **Impacto:** altera a influência relativa de produção e concessão.
- **Decisão necessária:** valores para mandante e visitante e possibilidade de
  variação por estatística.

### M1-PEND-003 — Recência no MVP

- **Alternativa A — recomendada:** uniformidade; recência desativada.
- **Alternativa B:** política não uniforme a especificar e calibrar.
- **Impacto:** altera todas as médias e exige novos parâmetros e testes.
- **Decisão necessária:** aprovar `uniform/v1` ou fornecer fórmula completa.

### M1-PEND-004 — Composição dos multiplicadores

- **Alternativa A — recomendada:** produto ordenado, com explicação por etapa.
- **Alternativa B:** composição aditiva em torno de `1.0`.
- **Alternativa C:** regra específica por estatística.
- **Impacto:** controla extremos, interação e interpretação dos ajustes.
- **Decisão necessária:** fórmula, catálogo por estatística e política de
  exceção conjunta.

### M1-PEND-005 — Escopo e elegibilidade para Poisson

- **Alternativa A — recomendada:** gols de primeiro tempo e tempo regulamentar;
  Poisson autorizado somente para esses códigos/períodos na versão inicial.
- **Alternativa B:** somente gols da partida completa.
- **Alternativa C:** incluir outras estatísticas após estudo de distribuição.
- **Impacto:** define API inicial, fixtures e integração com o engine.
- **Decisão necessária:** catálogo inicial e referência de aprovação da
  distribuição.

### M1-PEND-006 — Amostras assimétricas

- **Alternativa A — recomendada:** aceitar, preservar denominadores e avisar.
- **Alternativa B:** exigir tamanhos iguais, reduzindo a maior amostra.
- **Alternativa C:** bloquear qualquer assimetria.
- **Impacto:** afeta disponibilidade de cálculo e uso de dados válidos.
- **Decisão necessária:** comportamento e limiar de warning.

### M1-PEND-007 — Estados especiais de partida

- **Alternativa A — recomendada:** incluir apenas encerradas no tempo
  regulamentar; excluir canceladas; bloquear os demais estados até política
  específica.
- **Alternativa B:** regras por estatística/mercado.
- **Impacto:** composição da amostra, período e comparabilidade histórica.
- **Decisão necessária:** anuladas, interrompidas, W.O., prorrogação e pênaltis.

## 8. Decisões que não pertencem à ENG-003

- distribuição do Método 2;
- combinação de frequências do Método 3;
- seleção de fornecedor;
- persistência, APIs e interface;
- exposição de mercados, odds ou oportunidades;
- modelos para estatísticas futuras não aprovadas.

## 9. Estado do gate

As sete decisões `M1-PEND` estão abertas. Portanto, o estado é **NO-GO para
implementação matemática do Método 1**. O detalhamento está em
[20-method-one-planning-gate.md](20-method-one-planning-gate.md).

## 10. Referências

- [Plano técnico](15-method-one-technical-plan.md)
- [Catálogo de contratos](16-method-one-contract-catalog.md)
- [Estratégia de testes](18-method-one-test-strategy.md)
- [Backlog](19-method-one-implementation-backlog.md)
