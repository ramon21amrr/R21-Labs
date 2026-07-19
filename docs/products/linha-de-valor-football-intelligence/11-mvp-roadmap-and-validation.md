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

**FATO OBSERVADO:** concluída pela `LVFI-DISC-002`; resultados, limitações e decisões estão em [Auditoria dinâmica e baseline matemático](12-dynamic-audit-and-mathematical-baseline.md).

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

**DECISÃO APROVADA — D-MATH-002:** a regressão inicial usa tolerâncias absoluta e relativa de `1e-8` em política combinada documentada. Método, versão, seleção, mercado, período, linha, componentes asiáticos, filtros, amostra e identificadores exigem igualdade exata.

**DECISÃO APROVADA — D-MATH-004:** valores brutos são preservados; arredondamento ocorre somente na apresentação, inicialmente com duas casas para probabilidades percentuais e odds, três para lambdas e médias e passos de 0,25 para linhas asiáticas.

Na baseline, 350 de 350 comparações independentes passaram em `1e-8`. Evoluções deliberadas, como o cálculo integral da cauda, deverão ser versionadas e explicadas, nunca ocultadas pelo arredondamento.

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
| R-01 | comportamento legado fora da cobertura dos fixtures altera resultado | média | crítico | ampliar regressão de forma versionada conforme novos casos reais |
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

## 10. Decisões remanescentes para o planejamento

As decisões matemáticas `D-MATH-001` a `D-MATH-016` estão aprovadas. O planejamento ainda deverá tratar, sem reabrir essas regras:

1. escolha ou combinação de apresentação dos três métodos;
2. catálogo final do PDF-resumo e sua tecnologia de geração;
3. formato de importação, identidade e estratégia operacional de deduplicação;
4. retenção de brutos, snapshots, PDFs e logs;
5. orçamento de desempenho, disponibilidade e recuperação;
6. perfis, segregação organizacional e dados pessoais necessários;
7. primeiro provedor a testar e critérios eliminatórios;
8. contrato de IDs e evento futuro para o Value Tracker;
9. sucesso do piloto e autoridade de cutover.

## 11. Planejamento concluído, gate e próxima Task

**FATO OBSERVADO:** a `LVFI-ENG-001` foi concluída. A decomposição, os contratos, o mapeamento das decisões matemáticas, a estratégia de regressão e o backlog estão consolidados no [plano técnico do Pricing Engine](13-pricing-engine-technical-plan.md) e nos ADRs `ADR-LVFI-001` a `ADR-LVFI-010`.

A `LVFI-ENG-002` implementará somente o núcleo matemático compartilhado, mercados, contratos e serialização. Os Métodos 1, 2 e 3 pertencem, respectivamente, às `LVFI-ENG-003`, `LVFI-ENG-004` e `LVFI-ENG-005`.

O backlog atualizado antecipa `LVFI-ENG-002-T05 — fixtures seguras e harness inicial de regressão` para antes da distribuição Poisson e dos mercados.

**GO PARA IMPLEMENTAÇÃO CONTROLADA DA LVFI-ENG-002.**

O GO autoriza iniciar somente a `LVFI-ENG-002-T02 — fundação do pacote e ferramentas`, após plano específico e aprovação. Não autoriza banco, front-end, back-end, PDF, integrações ou os Métodos 1, 2 e 3.
