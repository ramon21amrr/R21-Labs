# MVP, roadmap e estratégia de validação

## 1. Objetivo

Este documento transforma a visão do produto em uma sequência executável de entregas e define como provar equivalência funcional e matemática com a planilha atual.

Classificações: **DECISÃO APROVADA** integra o direcionamento vigente; **RECOMENDAÇÃO** propõe uma decisão futura; **DECISÃO PENDENTE** exige aprovação explícita.

## 2. MVP aprovado

### 2.1 Escopo funcional

**DECISÃO APROVADA** — O MVP inclui:

1. autenticação e controle básico de acesso;
2. cadastro de competições, temporadas, times e partidas;
3. importação manual de partidas e resultados por arquivo estruturado;
4. registro e consulta do histórico recente dos times;
5. montagem das amostras mandante, visitante e geral;
6. configuração dos três modelos de [precificação](04-pricing-models.md);
7. probabilidades e odds justas para resultado, dupla chance, ambas marcam, totais de gols e handicap asiático entre `-2,00` e `+2,00`, em passos de `0,25`;
8. filtros e critérios mínimos de amostra necessários aos modelos;
9. aplicação manual dos critérios estatístico, situacional e intuitivo;
10. aprovação, rejeição e versionamento de uma precificação;
11. Match Center com comparação dos métodos e explicação dos insumos;
12. PDF-resumo auditável;
13. trilha de auditoria para importações, configurações e decisões.

### 2.2 Fora do MVP

**DECISÃO APROVADA** — Não integram o MVP:

- captura automatizada de dados ou odds externos;
- cálculo de valor esperado contra odds de mercado e geração automática de oportunidades;
- mercados de jogadores, árbitros, escanteios e cartões;
- PDF analítico completo;
- colaboração multiusuário avançada;
- planos, cobrança e gestão comercial;
- integração operacional com o Value Tracker.

Contratos e identificadores podem preparar essas evoluções, sem ampliar a implementação do MVP.

## 3. Roadmap

### Etapa 0 — Fechamento do discovery

- executar auditoria dinâmica da planilha em ambiente controlado;
- congelar uma versão-oráculo e seus hashes;
- aprovar cauda da matriz de placares e tolerâncias de equivalência;
- confirmar tratamento de zero, vazio e amostra insuficiente;
- validar liquidação das linhas asiáticas divididas;
- produzir os jogos de referência da seção 6;
- decidir retenção e origem dos dados importados.

### Etapa 1 — MVP

- identidade, autorização e auditoria;
- cadastros e importação manual;
- histórico e construção de amostras;
- motor matemático versionado;
- análise, comparação e aprovação;
- Match Center e PDF-resumo;
- regressão contra a versão-oráculo;
- operação piloto interna.

### Etapa 2 — Ampliação analítica

- estatísticas adicionais;
- PDF analítico completo;
- integração automatizada com um provedor de dados selecionado;
- monitoração de qualidade, cobertura e atraso;
- explicabilidade e comparação histórica ampliadas.

### Etapa 3 — Odds e oportunidades

- adaptadores de provedores de odds e snapshots temporais;
- margem, probabilidade implícita e valor esperado;
- elegibilidade e geração de oportunidades;
- mercados de jogadores, árbitros, escanteios e cartões;
- preparação do evento de integração com o Value Tracker.

### Etapa 4 — Produto comercial e ecossistema

- equipes e colaboração multiusuário;
- planos, limites, cobrança e administração comercial;
- integração operacional com o Value Tracker;
- métricas de adoção, resultado e retenção;
- controles ampliados de segurança e suporte.

## 4. Migração da planilha

**DECISÃO APROVADA** — A planilha é o oráculo de referência durante a migração, mas não será dependência de runtime.

**RECOMENDAÇÃO** — Aplicar seis gates:

1. **Congelamento**: guardar a versão aprovada, hash, versão do Excel, locale, data e responsável.
2. **Extração canônica**: exportar cadastros, partidas, configurações, amostras e saídas esperadas para formatos versionados.
3. **Mapeamento**: relacionar cada campo ao domínio, sem inferência silenciosa.
4. **Carga ensaiada**: importar em ambiente descartável e relatar aceitos, rejeitados, duplicados e transformados.
5. **Operação paralela**: calcular os mesmos jogos no oráculo e no novo motor, comparando valores brutos e exibidos.
6. **Cutover**: encerrar entradas na planilha somente após aceite e ensaio de retorno.

### 4.1 Regras de reconciliação

- IDs não dependem de número de linha ou posição de aba;
- datas carregam fuso e formato de origem;
- chaves naturais auxiliares detectam duplicidades;
- vazio, zero e erro de fórmula permanecem distintos;
- transformações registram origem, valor normalizado, regra e versão;
- rejeições são corrigíveis e reprocessáveis sem duplicar aceitos;
- saídas carregam versão do modelo e configuração.

### 4.2 Gate de desligamento

**RECOMENDAÇÃO** — Desligar a planilha operacional somente quando:

- 100% dos registros válidos estiverem reconciliados;
- divergências dos jogos de referência estiverem explicadas e aprovadas;
- não houver divergência crítica em mercados do MVP;
- importação, cálculo, aprovação, PDF e auditoria passarem ponta a ponta;
- backup, restauração e retorno forem ensaiados;
- usuários do piloto aprovarem o fluxo.

## 5. Camadas de validação

| Camada | O que validar | Evidência |
|---|---|---|
| Unidade | Poisson, normalização, odd justa, linhas asiáticas, filtros e amostras | testes determinísticos |
| Propriedade | limites, monotonicidade e somas coerentes | invariantes e testes gerativos |
| Contrato | importação, adaptadores e eventos | schemas versionados |
| Regressão | equivalência com a planilha-oráculo | relatório por jogo, método e mercado |
| Integração | importação até PDF e auditoria | cenários ponta a ponta |
| Segurança | autorização, segregação e dados sensíveis | matriz de acesso e testes negativos |
| Desempenho | importação, cálculo e PDF | baseline e orçamento aprovados |
| Recuperação | backup, restauração e idempotência | ensaio documentado |
| Experiência | entendimento e prevenção de erro | sessões com usuários-alvo |

## 6. Jogos de referência

Entradas e saídas esperadas devem vir da planilha-oráculo após auditoria dinâmica. Esta tabela define cobertura, não inventa resultados.

| ID | Cenário | Risco | Conferir |
|---|---|---|---|
| JR-01 | mandante claramente favorito | direção do favoritismo | 1X2, dupla chance e handicap negativo |
| JR-02 | forças equilibradas | limites e arredondamento | empate, DNB e `±0,25` |
| JR-03 | visitante claramente favorito | simetria | 1X2 e handicap positivo do mandante |
| JR-04 | expectativa muito baixa de gols | massa em placares baixos | under, ambas não e placares |
| JR-05 | expectativa muito alta de gols | truncamento | over, ambas marcam e soma da matriz |
| JR-06 | amostra abaixo do mínimo | falsa precisão | bloqueio e ausência de preço aprovável |
| JR-07 | histórico incompleto | vazio versus zero | exclusões, denominadores e auditoria |
| JR-08 | alta dispersão entre métodos | decisão humana | três métodos e aprovação |
| JR-09 | linha inteira `-2,00` | devolução | ganhar/devolver/perder |
| JR-10 | linha dividida `-1,75` | liquidação parcial | decomposição `-1,50/-2,00` |
| JR-11 | linha `-0,25` e DNB | empate | decomposição `0/-0,50` |
| JR-12 | linha dividida `+0,75` | proteção do azarão | decomposição `+0,50/+1,00` |
| JR-13 | correção após cálculo | temporalidade | invalidação, recálculo e auditoria |
| JR-14 | repetição das mesmas entradas | reprodutibilidade | hash e igualdade de saídas |

Cada fixture deve conter dados brutos e normalizados, IDs das partidas nas amostras, configuração dos métodos, matriz antes e depois da política de cauda, probabilidades e odds sem arredondamento, valores exibidos, versões e justificativa assinada para diferença aceita.

## 7. Tolerâncias e arredondamento

**DECISÃO PENDENTE** — A tolerância oficial de equivalência ainda precisa ser aprovada.

**RECOMENDAÇÃO** — Iniciar com:

- tolerância absoluta de `1e-8` para probabilidades brutas com a mesma política de cauda;
- igualdade do valor exibido após a regra oficial de arredondamento;
- comparação separada de valor bruto, normalizado e exibido;
- tolerância zero para composição de amostra, mercado, workflow e liquidação;
- divergência acima da tolerância sempre explicada, nunca escondida pelo arredondamento.

A recomendação deve ser calibrada com fixtures reais antes de se tornar contratual.

## 8. Critérios de aceite do MVP

### 8.1 Funcionais

- requisitos obrigatórios de [05-requirements.md](05-requirements.md) implementados e testados;
- jornada completa de importar, selecionar partida, revisar amostra, executar métodos, aplicar critérios, aprovar e gerar PDF;
- linhas asiáticas inteiras, meias e divididas do MVP precificadas e explicadas;
- amostra insuficiente e entrada inválida produzem bloqueio ou aviso explícito;
- ações críticas possuem autor, data, versão e antes/depois.

### 8.2 Matemáticos

- fixtures aprovados passam na tolerância oficial;
- massa respeita a política de cauda;
- probabilidades e odds respeitam invariantes;
- liquidação asiática coincide com a decomposição canônica;
- valores exibidos derivam dos brutos pela regra oficial.

### 8.3 Operacionais

- orçamentos de desempenho aprovados são atendidos;
- backup e restauração são demonstrados;
- reprocessamento não duplica importações, cálculos ou aprovações;
- PDF é legível, reproduzível e rastreável;
- usuários do piloto concluem as jornadas críticas.

## 9. Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|---|
| R-01 | fórmula ou macro não extraída altera resultado | alta | crítico | auditoria dinâmica e fixtures |
| R-02 | truncamento perde massa relevante | média | alto | política de cauda e teste de soma |
| R-03 | zero e ausência são confundidos | alta | alto | representação tipada e fixtures |
| R-04 | filtros mudam a amostra | alta | crítico | manifestar IDs e tolerância zero |
| R-05 | handicap parcial incorreto | média | crítico | decomposição e testes por margem |
| R-06 | provedor não mapeia entidades | média | alto | IDs internos, aliases e reconciliação |
| R-07 | PDF diverge do cálculo | baixa | alto | gerar do snapshot aprovado |
| R-08 | odds e Value Tracker ampliam o MVP | média | alto | gates e contratos inativos |
| R-09 | planilha muda durante migração | média | alto | congelamento e ownership |
| R-10 | dado sensível aparece em log/PDF | baixa | crítico | minimização e testes de acesso |
| R-11 | lock-in prematuro de provedor | média | médio | adaptadores e benchmark |
| R-12 | ajuste intuitivo não é explicável | média | alto | motivo e versionamento obrigatórios |

## 10. Decisões pendentes consolidadas

Antes do desenvolvimento do motor, aprovar:

1. política de cauda e tamanho da matriz de placares;
2. tolerância matemática e arredondamento;
3. amostra mínima por método e competição;
4. semântica de zero, vazio, ausente e erro herdado;
5. pesos, limites e precedência dos critérios humano-estatísticos;
6. escolha ou combinação entre os três métodos;
7. catálogo final do PDF-resumo;
8. correção, invalidação e republicação de preços;
9. formato de importação e deduplicação;
10. retenção de brutos, snapshots, PDFs e logs;
11. orçamento de desempenho e disponibilidade;
12. perfis, segregação organizacional e dados pessoais necessários;
13. primeiro provedor a testar e critérios eliminatórios;
14. contrato de IDs e evento futuro para o Value Tracker;
15. sucesso do piloto e autoridade de cutover.

## 11. Próxima Sprint recomendada

**RECOMENDAÇÃO** — Executar `LVFI-DISC-002 — Auditoria dinâmica e baseline matemático`, sem iniciar a implementação do produto.

Entregáveis:

1. planilha-oráculo congelada e executada em ambiente controlado;
2. inventário de macros, eventos, dependências ocultas e caminhos críticos;
3. fixtures JR-01 a JR-14 com entradas e saídas brutas;
4. relatório de divergências e massa probabilística;
5. decisões sobre cauda, tolerância, arredondamento, amostra e ausências;
6. testes matemáticos portáveis e independentes da planilha;
7. backlog do MVP refinado com aceite rastreável;
8. gate formal de `go/no-go` para implementar o motor.

Em paralelo, uma tarefa institucional separada deve atualizar o Company Context para refletir a prioridade aprovada da Linha de Valor sobre o Value Tracker. Essa alteração não pertence ao escopo deste discovery.
