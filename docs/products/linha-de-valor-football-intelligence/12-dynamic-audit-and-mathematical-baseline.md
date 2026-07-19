# Auditoria dinâmica e baseline matemático

## 1. Resumo executivo

**FATO OBSERVADO:** a sprint `LVFI-DISC-002` foi encerrada tecnicamente com a baseline `baseline_20260719T185339-0300_c1c0cffa`. Foram congelados 14 fixtures em 16 execuções, com três execuções idênticas do JR-14, 350 de 350 comparações matemáticas independentes aprovadas e 408 de 408 validações de handicap asiático aprovadas contra a semântica observada no Excel.

**DECISÃO APROVADA:** as decisões `D-MATH-001` a `D-MATH-016` deste documento são as regras iniciais do futuro Pricing Engine. Elas substituem as recomendações matemáticas que estavam pendentes antes desta sprint.

**LIMITAÇÃO:** a baseline demonstra reprodução controlada do comportamento observado nos fixtures. Ela não prova que a planilha seja matematicamente correta em todos os cenários e não transforma defeitos do legado em requisitos do produto.

## 2. Protocolo executado

O protocolo preservou os seis materiais originais como somente leitura e operou sobre cópias temporárias. As etapas foram:

1. inventário estático do pacote XLSM, fórmulas, nomes, controles e dependências;
2. abertura controlada por Excel COM em Safe Mode, com macros e eventos desativados;
3. recálculo normal e rebuild integral, com comparação de fórmulas e valores;
4. extração estática do VBA protegido sem `AccessVBOM`, seguida de comparação com p-code;
5. execução nominal e negativa de macros em cópias descartáveis autorizadas;
6. varredura de qualidade dos 2.129 registros;
7. seleção, congelamento e execução dos fixtures JR-01 a JR-14;
8. verificação independente de equivalência, cauda, `IFERROR` e handicap asiático;
9. reconciliação de hashes dos inputs, do VBA, das fórmulas e das evidências.

Durante os fixtures, nenhuma macro foi executada, nenhum input foi modificado e nenhum arquivo rastreado foi alterado. Recálculo normal e rebuild integral foram equivalentes nas 16 execuções.

## 3. Preservação e ambiente

As evidências selecionadas foram transferidas para o arquivo privado permanente da R21 Labs, fora do repositório público, no namespace do produto `linha-de-valor-football-intelligence/LVFI-DISC-002`. O arquivo contém manifestos, hashes, matrizes CSV, relatórios JSON, fixtures, resultados das 16 execuções, inventário e fontes VBA, testes de macros, defeitos, ambiente reproduzível, PDF de teste e capturas essenciais.

O manifesto privado possui SHA-256 `6D41EC2DA40CD3C055D7AEA2FBE10097F2C506E889A58699A82A69C00ABA92D9`. Foram validados 210 arquivos de payload, totalizando 59.414.409 bytes, sem divergência de hash. O arquivo privado não contém repositório Git, inputs originais, cópias XLSM descartáveis nem o ambiente virtual completo; versões, `pip freeze` e logs foram preservados.

O relatório final da baseline possui SHA-256 `6A2BFC92FF10857FC54E4F9B5BDE068A75EE15932EF57FCE582320367B552FA5`.

## 4. Auditoria dinâmica

O workbook foi aberto e recalculado somente em cópias. A reconciliação encontrou:

- igualdade entre recálculo normal e rebuild integral;
- nenhuma alteração no texto das fórmulas durante os fluxos controlados;
- nenhuma dependência externa ativa no pacote;
- nenhuma execução residual do Excel ao fim das fases;
- hashes finais dos seis inputs idênticos aos hashes iniciais.

Esses resultados qualificam o XLSM como oráculo de regressão para os comportamentos cobertos, não como dependência de runtime nem como especificação normativa universal.

## 5. Inventário resumido do VBA

A extração identificou 18 componentes: cinco módulos padrão, um módulo de workbook e 12 módulos de planilha. Foram inventariados nove procedimentos:

- `Salvar_Area_De_Impressao_PDF_Manual`;
- `AdicionarSEERRO`;
- `Inserir_SEERRO_Em_Todas_As_Formulas`;
- `AdicionarSEERRO_PTBR`;
- `LimparFormulario`;
- `btnNovoJogo_Click`;
- `cmdLimparFormulario_Click`;
- `cmdMandante_Change`;
- `cmdSalvarJogo_Click`.

Não foram encontrados eventos automáticos do workbook nem eventos de ciclo de vida das planilhas. Quatro handlers ActiveX existem; três handlers candidatos não existem. Onze componentes não possuem lógica executável relevante. A comparação direta com p-code mitigou, sem constituir prova formal absoluta, o risco de divergência entre fonte e código compilado.

## 6. Macros e testes operacionais

| Fluxo | Resultado observado |
|---|---|
| Novo jogo | Reprovado: limpou seleções e células derivadas, mas preservou campeonato e temporada. |
| Limpeza direta | Aprovada: 25 células e dois controles limpos, sem alterar a tabela. |
| Botão de limpeza | Aprovado e equivalente à limpeza direta. |
| Salvar jogo nominal | Aprovado no caminho válido: uma linha com 25 campos foi adicionada corretamente. |
| Exportar PDF | Funcionalmente aprovado com restrição grave de qualidade: duas páginas, compressão extrema e segunda página vazia. |

A aprovação do caminho nominal de salvamento não elimina os defeitos transacionais e de validação encontrados nos testes negativos.

## 7. Testes negativos

| Teste | Cenário | Resultado |
|---|---|---|
| NT-01 | cinco variações de obrigatório ausente | Aprovado: nenhuma linha criada e formulário preservado. |
| NT-02 | mandante igual ao visitante | Aprovado: nenhuma linha criada e formulário preservado. |
| NT-03 | texto, negativo e incoerência primeiro tempo/total | Reprovado: os três registros inválidos foram aceitos. |
| NT-04 | falha logo após criar a linha | Reprovado: permaneceu uma linha vazia, sem rollback. |
| NT-05 | falha no último campo | Reprovado: permaneceu uma linha com 24 de 25 campos, sem rollback. |
| NT-06 | cadastro idêntico repetido | Reprovado: duas linhas idênticas foram aceitas. |

## 8. Defeitos confirmados do legado

| ID | Defeito | Gravidade | Consequência para o produto futuro |
|---|---|---|---|
| LVFI-LEGACY-001 | Novo jogo não limpa todos os campos. | Alta | Reset deve ter pós-condição explícita e testada. |
| LVFI-LEGACY-002 | Erros são ocultados por `On Error Resume Next`. | Alta | Erros devem ser tipados, registrados e comunicados. |
| LVFI-LEGACY-003 | Cadastro pode deixar linha vazia ou parcial. | Crítica | Gravação deve ser validada antes e executada atomicamente. |
| LVFI-LEGACY-004 | Não há validação estatística suficiente. | Crítica | Tipo, domínio e coerência cruzada devem ser validados. |
| LVFI-LEGACY-005 | Não há controle de duplicidade. | Alta | Importação precisa de identidade e restrições de unicidade. |
| LVFI-LEGACY-006 | PDF legado é ilegível e contém página vazia. | Alta | Relatório deve ser redesenhado e testado quanto a paginação e legibilidade. |

## 9. Qualidade da base

Dos 2.129 registros:

- 1.512 são válidos para fixtures;
- 616 são válidos com ressalva de temporada/ano civil;
- um é suspeito;
- nenhum foi classificado como inválido;
- nenhuma duplicidade foi encontrada na varredura.

Os 616 registros com ressalva decorrem da convenção existente entre o rótulo de temporada e o ano civil. A importação futura deverá normalizar rótulo e período sem alterar os registros originais.

O registro da linha de origem 1808, CRB x Ponte Preta, contém 13 cartões do mandante. Ele permanece preservado e marcado como suspeito; não pode participar de baselines ou calibrações até verificação manual da fonte. Suspeita não equivale a invalidade confirmada.

## 10. Fixtures JR-01 a JR-14

| Fixture | Cobertura principal |
|---|---|
| JR-01 | favorito forte mandante |
| JR-02 | forças equilibradas |
| JR-03 | favorito forte visitante |
| JR-04 | expectativa baixa de gols |
| JR-05 | expectativa alta de gols e cauda |
| JR-06 | amostra insuficiente |
| JR-07 | ausência e cenário sintético controlado |
| JR-08 | dispersão entre métodos |
| JR-09 | handicap inteiro `-2,00` |
| JR-10 | handicap dividido `-1,75` |
| JR-11 | linha `-0,25` e draw no bet |
| JR-12 | handicap dividido `+0,75` |
| JR-13 | correção, nova revisão e rastreabilidade |
| JR-14 | repetibilidade das mesmas entradas |

Foram realizadas 16 execuções: uma para cada fixture, mais duas repetições adicionais do JR-14. Os três resultados canônicos do JR-14, incluindo fontes VBA lógicas, fórmulas, lambdas e probabilidades, foram idênticos.

## 11. Equivalência matemática

As 350 comparações independentes passaram na tolerância absoluta de `1e-8`. A suíte comparou valores brutos relevantes e manteve igualdade exata para composição de amostra e elementos categóricos. Não houve falha de equivalência entre o verificador independente e as saídas observadas nos fixtures.

Esse resultado é uma baseline de regressão. Regras futuras aprovadas, como o tratamento integral da cauda, podem divergir deliberadamente da matriz truncada do Excel e deverão ser testadas como evolução explícita, não escondidas como equivalência.

## 12. Cauda da distribuição e soma

**FATO OBSERVADO:** a matriz do Excel limita cada placar a 0–6 e pode omitir massa material em cenários de lambda alta. A massa truncada não é tratada explicitamente pelo legado.

**DECISÃO APROVADA:** o futuro motor calculará a distribuição integralmente, de forma analítica ou adaptativa. Massa residual será calculada, registrada e observável; nunca será descartada ou normalizada silenciosamente. Uma matriz usada para visualização crescerá até atingir a tolerância definida.

Distribuições mutuamente exclusivas e exaustivas deverão somar 1 dentro de `1e-12`. Diferença não explicada será bloqueadora.

## 13. `IFERROR`, zero e ausência

**FATO OBSERVADO:** o uso amplo de `IFERROR/SEERRO` transforma em vazio situações que podem representar ausência normal, erro, dependência vazia ou probabilidade zero. Em partes da cadeia, vazios podem ainda ser coeridos para zero.

**DECISÃO APROVADA:** o sistema não migrará esse padrão. Zero será somente uma observação real de valor zero; vazio representará ausência; estados como não aplicável, inválido e pendente de revisão serão distintos. Erros serão tipados, e erros críticos bloquearão aprovação e publicação.

## 14. Handicap asiático

As 408 validações independentes passaram contra a semântica observada no Excel. Foram cobertas perspectivas de mandante e visitante, margens relevantes e linhas inteiras, meias e de quarto.

**DECISÃO APROVADA:** linhas asiáticas serão armazenadas como unidades inteiras de quartos e liquidadas pela decomposição canônica da stake. O resultado deverá distinguir vitória integral, meia vitória, reembolso, meia derrota e derrota integral. Probabilidades e odds justas considerarão a liquidação completa.

## 15. Decisões matemáticas aprovadas

### D-MATH-001 — Cauda da distribuição

**DECISÃO APROVADA:**

Cálculo integral, analítico ou adaptativo; massa residual calculada, registrada e observável; nenhuma normalização silenciosa.

### D-MATH-002 — Tolerância de equivalência

**DECISÃO APROVADA:**

Tolerâncias absoluta e relativa iniciais de `1e-8`, segundo política combinada documentada. Método, versão, seleção, mercado, período, linha, componentes asiáticos, filtros, amostra e identificadores exigem igualdade exata.

### D-MATH-003 — Precisão interna

**DECISÃO APROVADA:**

Probabilidades, Poisson, médias e lambdas usarão ponto flutuante `binary64/double`, preservando valores brutos. Linhas asiáticas usarão unidades inteiras de quartos.

### D-MATH-004 — Arredondamento de exibição

**DECISÃO APROVADA:**

Arredondamento somente na apresentação: probabilidades e odds justas com duas casas, lambdas e médias com três, e linhas em incrementos de 0,25. A configuração visual não altera o valor bruto.

### D-MATH-005 — Linha principal

**DECISÃO APROVADA:**

O catálogo é canônico em passos de 0,25. A linha principal de handicap será a de odd justa mais próxima de 2,00; empate escolhe a linha mais próxima de zero, preserva simetria e não elimina as demais linhas calculadas.

### D-MATH-006 — Soma das probabilidades

**DECISÃO APROVADA:**

Distribuições exaustivas e mutuamente exclusivas somarão 1 dentro de `1e-12`. Toda diferença será explicada e associada à massa residual ou a erro; diferença não explicada bloqueia o fluxo.

### D-MATH-007 — Amostra mínima

**DECISÃO APROVADA:**

Menos de 5 observações é amostra insuficiente e não pode ser publicada ou aprovada; de 5 a 9 é baixa confiança, com alerta e publicação condicionada a permissão e justificativa; 10 ou mais é confiança padrão, sem garantia estatística automática.

### D-MATH-008 — Confiança da amostra

**DECISÃO APROVADA:**

Cada precificação registrará quantidades solicitada, encontrada, válida e excluída, numerador, denominador, confiança, motivos de exclusão, uso de temporada anterior e filtros.

### D-MATH-009 — Semântica de zero

**DECISÃO APROVADA:**

Zero é exclusivamente uma observação real, com origem, partida, estatística, fonte e data de coleta. Ausência, erro ou desconhecido não podem virar zero.

### D-MATH-010 — Semântica de vazio

**DECISÃO APROVADA:**

Vazio é ausência de informação, não entra automaticamente no denominador e pode bloquear cálculo. Importação distinguirá zero observado, ausência, não aplicável, inválido e pendente de revisão.

### D-MATH-011 — Tratamento de erros

**DECISÃO APROVADA:**

Erros serão tipados; o padrão amplo de `IFERROR` com retorno vazio não será migrado. Erros críticos bloqueiam aprovação e publicação.

### D-MATH-012 — Handicap asiático

**DECISÃO APROVADA:**

Liquidação pela decomposição canônica e divisão de stake, incluindo todos os estados integrais e parciais. Linhas de quarto serão decompostas nas duas linhas adjacentes.

### D-MATH-013 — Denominador do Método 3

**DECISÃO APROVADA:**

Somente observações efetivamente válidas entram no denominador. Evento, numerador, denominador, partidas incluídas e excluídas, motivos, frequência e confiança serão registrados.

### D-MATH-014 — Pesos

**DECISÃO APROVADA:**

Pesos serão finitos, estarão entre 0 e 1 e somarão 1 dentro da tolerância definida. Origem, versão e justificativa serão preservadas; configuração inválida bloqueia cálculo ou aprovação e não será corrigida silenciosamente.

### D-MATH-015 — Multiplicadores

**DECISÃO APROVADA:**

Multiplicadores serão positivos. A faixa inicial é 0,90–1,10. Exceções exigem configuração versionada, justificativa, autorização administrativa, auditoria e aprovação do Product Owner quando mudarem a regra do modelo; nenhuma limitação será silenciosa.

### D-MATH-016 — Precificação aprovada

**DECISÃO APROVADA:**

Uma precificação aprovada é imutável. Mudança de dados, filtros, amostra, parâmetros, pesos, multiplicadores, método, versão ou regra cria nova revisão vinculada, preservando a anterior. O JR-13 é o caso de referência.

## 16. Limitações e uso correto da baseline

- A cobertura é a dos 14 fixtures e não uma prova exaustiva do domínio.
- O JR-07 exigiu cenário sintético controlado porque a base não oferecia rótulo real de temporada anterior para o caso desejado.
- A matriz 0–6 do Excel é reproduzida apenas para regressão; não é a regra futura aprovada.
- O caminho nominal de uma macro não neutraliza os seis defeitos confirmados do legado.
- Os dados originais não possuem procedência completa por registro.
- O registro suspeito requer verificação manual antes de uso analítico.
- A suíte deve permanecer como regressão versionada, não como snapshot de produção.

## 17. Gate final

**GO PARA PLANEJAMENTO DO DESENVOLVIMENTO DO PRICING ENGINE.**

Este GO autoriza somente o planejamento da implementação. Não autoriza criar código, banco de dados, front-end, back-end ou desenvolver o MVP. A implementação dependerá de uma sprint própria, explicitamente aprovada.

As implicações para roadmap e aceite estão em [MVP, roadmap e estratégia de validação](11-mvp-roadmap-and-validation.md).
