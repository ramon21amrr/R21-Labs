# Modelos de precificação

## 1. Contrato comum dos modelos

Os Métodos 1, 2 e 3 são formas diferentes de estimar probabilidades. Todos deverão receber entradas explícitas e produzir um resultado auditável.

Cada execução deve registrar:

- partida e mercado;
- método e versão;
- versão da configuração;
- filtros e IDs da amostra;
- versão dos dados;
- estatísticas intermediárias;
- parâmetros e ajustes;
- probabilidades, odds justas e linhas;
- massa residual ou erro numérico;
- data, horário e responsável;
- estado do workflow.

**DECISÃO APROVADA:** alterar um método não modifica precificações históricas. Uma mudança gera nova versão.

## 2. Regras comuns de dados

### 2.1 Vazios e ausência

- Estatística ausente não é convertida em zero.
- Partida sem a estatística necessária não entra na média ou frequência daquele mercado.
- Se nenhum jogo válido existir, o modelo retorna “dados insuficientes”, não probabilidade zero.

### 2.2 Zeros

- Zero observado participa normalmente de médias e frequências.
- Zero sem prova de observação deve ser classificado como dado de qualidade duvidosa.

### 2.3 Erros

**RECOMENDAÇÃO:** não reproduzir `IFERROR` como tratamento universal. Erros deverão possuir código e explicação, por exemplo: amostra vazia, média da liga igual a zero, parâmetro fora do limite ou distribuição não convergente.

### 2.4 Quantidade mínima

**DECISÃO PENDENTE:** a quantidade mínima ainda não foi aprovada.

**RECOMENDAÇÃO inicial:**

- menos de 5 observações válidas: não publicar probabilidade;
- de 5 a 9: calcular apenas para análise, com aviso de baixa confiança;
- 10 ou mais: faixa operacional padrão inicial;
- sempre mostrar `n` efetivo por time e estatística.

Esses limites deverão ser calibrados por mercado; não constituem evidência de validade estatística.

## 3. Método 1 — médias com contexto

### 3.1 Objetivo

Combinar produção própria, concessão do adversário e conhecimento contextual de Ramon em uma expectativa ajustada para o evento.

### 3.2 Dados de entrada

- média a favor do time analisado;
- média cedida pelo adversário;
- condição de mandante ou visitante;
- período e mercado;
- pesos da produção e da concessão;
- multiplicadores de contexto;
- partidas válidas e filtros da amostra.

### 3.3 Amostra observada

**FATO OBSERVADO:** a planilha seleciona até os dez jogos mais recentes do mandante em casa e do visitante fora, com opção de incluir a temporada anterior.

**RECOMENDAÇÃO:** tornar quantidade e filtros configuráveis, preservando os dez jogos como preset inicial.

### 3.4 Fórmula conceitual

Para o mandante:

`média base = média a favor do mandante × peso próprio + média cedida pelo visitante × peso adversário`

`média refinada = média base × multiplicador HFA × SOS × forma × lesões × ritmo × must win`

Para faltas e cartões, a planilha usa conjunto específico:

`média refinada = média base × HFA × SOS × ritmo × must win × árbitro`

**DECISÃO PENDENTE:** confirmar se todos os multiplicadores devem ser aplicados de forma puramente multiplicativa e se existirão limites diferentes por mercado.

### 3.5 Pesos

- Os pesos representam a importância relativa da produção própria e da concessão do adversário.
- **RECOMENDAÇÃO:** a soma deve ser 1,00; o sistema deve impedir aprovação fora da tolerância.
- Pesos podem variar por mercado, competição e participante.

### 3.6 Multiplicadores

- `1,00`: sem ajuste;
- acima de `1,00`: eleva a expectativa;
- abaixo de `1,00`: reduz a expectativa.

**FATO OBSERVADO:** o Word menciona faixa usual de `0,90` a `1,10`.

**DECISÃO PENDENTE:** aprovar limites rígidos, permissões para exceção e comportamento quando vários ajustes extremos se acumularem.

### 3.7 Hierarquia de configuração

**DECISÃO APROVADA:**

`partida → campeonato → global`

O valor mais específico substitui o menos específico para o mesmo parâmetro. Cada configuração deve registrar valor, justificativa, autor, data, versão e configuração substituída.

**RECOMENDAÇÃO:** ajustes de partida devem exigir justificativa textual; presets não devem apagar o valor original usado em uma precificação aprovada.

### 3.8 Exemplo observado

O Word apresenta produção do mandante de 1,60 gol e concessão do visitante de 1,10, com pesos 0,60 e 0,40:

`1,60 × 0,60 + 1,10 × 0,40 = 1,40`

Aplicando os multiplicadores exemplificados, a expectativa é arredondada para aproximadamente 1,47. O sistema deve guardar o valor de cálculo com precisão superior à exibida.

### 3.9 Saídas

- médias base e refinada de cada participante;
- probabilidades por resultado;
- odds justas;
- linhas projetadas;
- explicação de cada ajuste e comparação com o valor sem contexto.

### 3.10 Limitações e testes

- subjetividade e risco de ajuste retrospectivo;
- correlação entre multiplicadores;
- sensibilidade excessiva à multiplicação de fatores;
- testes de pesos, precedência, limites, justificativa, reprodutibilidade e impacto isolado de cada multiplicador.

## 4. Método 2 — força relativa ao campeonato

### 4.1 Objetivo

Estimar expectativas usando o desempenho do time em relação à média do campeonato, sem pesos subjetivos ou contexto manual.

### 4.2 Dados de entrada

- média do campeonato para mandantes e visitantes;
- média a favor do mandante em casa;
- média cedida pelo visitante fora;
- média a favor do visitante fora;
- média cedida pelo mandante em casa;
- amostra, mercado e período.

### 4.3 Fórmula conceitual

Para o mandante:

`força ofensiva = média a favor do mandante / média dos mandantes no campeonato`

`fragilidade defensiva adversária = média cedida pelo visitante / média cedida pelos visitantes no campeonato`

`expectativa mandante = força ofensiva × fragilidade defensiva × média dos mandantes no campeonato`

O visitante usa o mesmo processo com as médias de visitantes.

### 4.4 Exemplo observado

O Word apresenta:

- mandante com média de 1,84;
- visitante cedendo 1,31;
- média do campeonato de 1,49.

Assim, as forças relativas aproximadas são 1,23 e 0,88, produzindo expectativa próxima de 1,61.

### 4.5 Regras de segurança

- Média da liga igual a zero deve gerar erro explícito.
- A média da liga deve usar a mesma competição, temporada, período e definição estatística da amostra dos times.
- **DECISÃO PENDENTE:** definir se a média da liga usará temporada inteira disponível até a data da partida ou janela equivalente à amostra.
- Jogos posteriores à data da análise não podem contaminar uma precificação histórica.

### 4.6 Saídas, limitações e testes

Saídas: forças relativas, expectativa de cada time, expectativa total, probabilidades, odds e linhas.

Limitações:

- instabilidade no início da temporada;
- ligas heterogêneas e mudanças de divisão;
- sensibilidade a médias muito baixas;
- possível inadequação para mercados cuja distribuição varia muito entre times.

Testes: médias por mando, divisões por zero, corte temporal, simetria, comparação manual e regressão por mercado.

## 5. Método 3 — frequência observada

### 5.1 Objetivo

Mostrar a frequência com que um evento ocorreu nas partidas válidas da amostra, sem aplicar distribuição probabilística.

### 5.2 Fórmula

`frequência = quantidade de ocorrências válidas / quantidade real de jogos válidos`

Exemplos de ocorrência: vitória, empate, over de uma linha, ambas marcam ou cobertura de handicap.

### 5.3 Denominador

- Cada time contribui apenas com partidas em que os campos necessários são numéricos e disponíveis.
- A quantidade solicitada, como dez, não substitui a quantidade efetivamente válida.
- Amostras dos dois times podem possuir tamanhos diferentes.

**FATO OBSERVADO:** as fórmulas principais examinadas usam `ISNUMBER` para o denominador. Uma aba legada usa `COUNTA` e não deve ser migrada sem revisão.

### 5.4 Ausências e pouca amostra

- Ausência de estatística remove somente aquela observação do mercado afetado.
- O sistema exibe numerador, denominador e intervalo de confiança ou indicador de incerteza.
- **RECOMENDAÇÃO:** nunca exibir apenas “80%” quando o resultado é “4 de 5”; mostrar ambos.

### 5.5 Configuração e versionamento

O Método 3 deve versionar definição do evento, filtros, pesos de recência se introduzidos, regra de combinação das amostras e política de confiança.

### 5.6 Limitações e testes

- frequência passada não é garantia de probabilidade futura;
- resultados extremos são comuns em amostras pequenas;
- combinar os dois times com quantidades diferentes pode alterar a interpretação.

Testes: denominador com vazios e zeros, amostras desiguais, nenhuma observação, limites asiáticos e soma de eventos complementares.

## 6. Distribuição de Poisson

### 6.1 Aplicação observada

Os Métodos 1 e 2 usam a distribuição de Poisson para converter uma média esperada `λ` na probabilidade de uma contagem:

`P(X = k) = e^(-λ) × λ^k / k!`

Para placar exato, multiplica-se a probabilidade de gols do mandante pela do visitante, assumindo independência.

### 6.2 Totais

- Under `n,5`: probabilidade acumulada até `n`.
- Over `n,5`: `1 - probabilidade acumulada até n`.

### 6.3 Cauda e totalização

**RISCO:** limitar o placar a 6 × 6 perde massa de probabilidade.

**RECOMENDAÇÃO:** o motor deverá calcular a cauda até que a massa residual fique abaixo da tolerância e registrar:

- limite usado;
- soma calculada;
- massa residual;
- eventual normalização, se aprovada.

**DECISÃO PENDENTE:** aprovar tolerância e se a exibição será normalizada para 100% ou mostrará a massa residual separadamente.

### 6.4 Adequação por mercado

**RISCO:** Poisson supõe relação específica entre média e variância e independência de eventos. Cartões, faltas e algumas estatísticas podem apresentar dispersão maior, dependência temporal ou limites práticos.

**RECOMENDAÇÃO:** Poisson será hipótese inicial, não verdade permanente. Cada mercado posterior deverá comparar calibração e alternativas, como Poisson ajustada ou distribuição binomial negativa, antes da aprovação.

## 7. Odds justas e linhas

Para mercados sem reembolso:

`odd justa = 1 / probabilidade decimal`

Para mercados com reembolso ou liquidação parcial, aplicar a regra de valor esperado descrita no [catálogo de mercados](03-business-rules-and-market-catalog.md#64-odd-justa-com-liquidação-parcial).

**RECOMENDAÇÃO:** não arredondar probabilidades antes de calcular odds. Arredondamento é apenas de apresentação.

## 8. Versionamento e auditoria

Uma versão de modelo deve registrar:

- identificador e nome, como `Método 1 v1.0`;
- status: experimental, candidata, aprovada, substituída ou arquivada;
- fórmula e código correspondentes;
- mercados suportados;
- parâmetros e limites;
- conjunto de testes e resultados;
- responsável, justificativa e data de aprovação;
- versão anterior substituída.

O snapshot de uma precificação deve preservar o resultado, mesmo que dados, configurações ou código mudem depois.

## 9. Estratégia de testes dos modelos

- testes unitários de cada média, peso e multiplicador;
- probabilidades de Poisson conhecidas;
- soma da matriz e massa residual;
- odds justas sem e com reembolso;
- todas as 17 linhas de handicap do MVP;
- vazios, zeros, divisões por zero e parâmetros inválidos;
- precedência global, campeonato e partida;
- amostras pequenas, incompletas e desiguais;
- reprodução dos confrontos de referência definidos em [MVP, roadmap e validação](11-mvp-roadmap-and-validation.md).

## 10. Decisões pendentes dos modelos

- limites e soma obrigatória dos pesos;
- limites dos multiplicadores e permissão para exceções;
- quantidade mínima por método e mercado;
- política de cauda e tolerância numérica;
- janela usada nas médias do campeonato;
- confiança estatística exibida no Método 3;
- distribuições alternativas para mercados futuros;
- fórmula final de odd justa para todas as liquidações asiáticas.
