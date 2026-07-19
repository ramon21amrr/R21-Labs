# Estado atual e auditoria da planilha

## 1. Escopo e método de inspeção

**FATO OBSERVADO:** os materiais originais foram tratados como somente leitura. A inspeção utilizou leitura do pacote XLSM, fórmulas armazenadas, valores em cache, estrutura do DOCX, extração textual dos PDFs e inspeção visual das imagens e dos PDFs renderizados.

A inspeção inicial foi complementada pela auditoria dinâmica e pela baseline matemática da `LVFI-DISC-002`. O protocolo, as evidências consolidadas e os limites de validade estão em [Auditoria dinâmica e baseline matemático](12-dynamic-audit-and-mathematical-baseline.md).

## 2. Inventário dos materiais

| Material | Evidência observada | Papel no discovery |
|---|---|---|
| `RAMON AUTOMATICA 1.1 2026.xlsm` | Planilha com dados, fórmulas, VBA, controles e relatório | Principal referência funcional e matemática |
| `METODOS E CALCULOS.docx` | Descrição dos Métodos 1, 2 e 3 e dos mercados | Referência conceitual e de intenção de negócio |
| `19 SAO PAULO E ATHLETICO PR.pdf` | Relatório exportado do Excel | Exemplo de conteúdo e problema de impressão |
| `38 WEST HAM E LEEDS.pdf` | Segundo relatório exportado do Excel | Comparação e confirmação do padrão de saída |
| Duas capturas de tela | Lista de partidas e central da partida de terceiro | Referência conceitual de navegação, sem autorização para cópia |

## 3. Visão geral do XLSM

### 3.1 Estrutura

- **FATO OBSERVADO:** 12 abas, sendo 5 visíveis e 7 ocultas.
- **FATO OBSERVADO:** nenhuma aba foi identificada como `veryHidden`.
- **FATO OBSERVADO:** a aba ativa armazenada é `Entradas`.
- **FATO OBSERVADO:** existe uma tabela estruturada chamada `tbl_jogos`.
- **FATO OBSERVADO:** existem 16 nomes definidos, incluindo listas de campeonatos, temporadas e times.
- **FATO OBSERVADO:** existem validações de dados para datas, campeonatos, temporadas e times.
- **FATO OBSERVADO:** existem sete controles ActiveX relacionados a seleção de times, novo jogo, salvamento e limpeza de formulário.
- **FATO OBSERVADO:** existe um projeto VBA com aproximadamente 77 KB.
- **FATO OBSERVADO:** não foram encontrados vínculos externos, Power Query, conexões ou tabelas dinâmicas no pacote.

### 3.2 Inventário por aba

| Aba | Estado | Objetivo observado | Entradas/saídas principais | Destino sugerido | Risco ou pendência |
|---|---|---|---|---|---|
| `Resumo` | Oculta | Versão anterior de históricos e mercados | Times, médias e tabelas de probabilidade | Legado a comparar | Sem referências de fórmula observadas; contém rótulos possivelmente antigos |
| `FORMULARIO` | Visível | Cadastro manual de partidas | Data, campeonato, temporada, times e 20 estatísticas | Importação/administração | Depende de VBA não executado |
| `Entradas` | Visível | Seleção da análise e configuração do Método 1 | Campeonato, temporada, times, pesos, multiplicadores e observações | Central da partida/configuração | Mistura entrada, visualização e dados derivados |
| `Lançamentos` | Visível | Relatório completo e cálculo de mercados | Históricos, estatísticas, métodos, odds justas e linhas | Interface, relatórios e serviços separados | 5.570 fórmulas, 365 mesclagens e alta complexidade visual |
| `Parâmetros` | Oculta | Cálculos intermediários e matrizes de placar | Médias refinadas, Poisson e probabilidades | Pricing Engine | Matriz limitada a 6 × 6 e forte dependência de referências celulares |
| `JOGOS` | Visível | Base de partidas | 2.129 linhas e 25 colunas | Banco interno e importação | Sem IDs externos ou procedência por registro |
| `TABELAS_AUX` | Visível | Listas para validação | Campeonatos, temporadas e times | Cadastros normalizados | Nomes e duplicidades dependem de conferência manual |
| `AUX_BLOCOS` | Oculta | Filtrar e ordenar jogos do mandante e visitante | `tbl_jogos` e seleção de `Entradas` | Serviço de amostras | Fórmulas dinâmicas e dependência de recursos recentes do Excel |
| `AUX_MEDIAS` | Oculta | Calcular médias do campeonato | Campeonato, temporada e estatísticas | Serviço estatístico | Tratamento de ausências precisa ser formalizado |
| `METODO 02` | Oculta | Protótipo do Método 2 para gols | Históricos, médias da liga e Poisson | Legado de validação | Sem referências diretas observadas a partir das telas principais |
| `ULTIMOS 10` | Oculta | Protótipo do Método 3 | Frequências em dez jogos | Legado de validação | Algumas fórmulas usam `COUNTA` sobre células com fórmula |
| `Planilha2` | Oculta | Notas e lista inicial de mercados | Rótulos e comentários manuais | Conhecimento a consolidar | Não deve permanecer como fonte normativa isolada |

**FATO OBSERVADO:** a auditoria dinâmica e o inventário VBA não encontraram eventos automáticos que tornem todas as abas parte do fluxo principal. Ainda assim, ausência de referência de fórmula não prova que uma aba seja descartável; classificação definitiva exige uma decisão de produto sobre usos manuais e históricos.

## 4. Base de jogos

### 4.1 Perfil observado

- 2.129 partidas;
- 25 campos: data, competição, temporada, mandante, visitante e 20 estatísticas;
- 10 campeonatos com registros;
- período entre 17 de maio de 2025 e 17 de julho de 2026;
- temporadas armazenadas como 2026 e, em quatro registros, 2027;
- nenhuma célula vazia nos registros inspecionados;
- nenhuma duplicidade pela chave provisória data, competição, mandante e visitante;
- nenhuma estatística negativa;
- nenhuma inconsistência básica em que valor do primeiro tempo excedesse o total da partida;
- chutes no gol não excederam finalizações nos testes estruturais executados.

### 4.2 Limitações da base

- **RISCO:** um zero pode representar ocorrência real ou dado indisponível preenchido como zero.
- **FATO OBSERVADO:** não há campo de fornecedor, ID externo, data de importação, versão da correção ou responsável por registro.
- **RISCO:** o campo `Temporada` usa um rótulo numérico que precisa ser separado de datas reais de início e fim, especialmente em calendários que atravessam dois anos.
- **DECISÃO APROVADA:** toda estatística futura guardará valor, disponibilidade, origem e revisão, distinguindo zero observado, ausência, não aplicável, inválido e pendente de revisão, conforme `D-MATH-009` e `D-MATH-010`.

### 4.3 Varredura de qualidade da LVFI-DISC-002

**FATO OBSERVADO:** dos 2.129 registros, 1.512 foram classificados como válidos para fixtures, 616 como válidos com ressalva de temporada/ano civil, um como suspeito, nenhum como inválido e nenhum como duplicado.

Os 616 registros com ressalva deverão ser normalizados na importação futura sem alterar os originais. A linha de origem 1808, CRB x Ponte Preta, com 13 cartões do mandante, permanece suspeita e excluída de baselines e calibrações até verificação manual; ela não foi classificada como inválida.

## 5. Dependências observadas

```mermaid
flowchart LR
    J["JOGOS / tbl_jogos"] --> AB["AUX_BLOCOS"]
    J --> AM["AUX_MEDIAS"]
    TA["TABELAS_AUX"] --> E["Entradas"]
    AB --> E
    AM --> E
    E --> L["Lançamentos - históricos"]
    L --> P["Parâmetros - médias e Poisson"]
    P --> O["Lançamentos - mercados e odds"]
    F["FORMULARIO + VBA"] -. "fluxo testado em cópias" .-> J
    O -. "exportação testada em cópia" .-> PDF["PDF"]
```

**FATO OBSERVADO:** `Lançamentos` referencia intensamente `Entradas` e `Parâmetros`; `Parâmetros` usa estatísticas intermediárias de `Lançamentos`. Esse ciclo em nível de abas não significa necessariamente referência circular de células, mas aumenta a dificuldade de entendimento.

## 6. VBA, controles e formulário

Foram identificados controles com nomes compatíveis com:

- seleção de mandante e visitante;
- criação de novo jogo;
- salvamento do formulário;
- limpeza do formulário;
- exportação manual da área de impressão para PDF.

Também foram encontradas referências textuais a rotinas de inclusão de `SEERRO/IFERROR` em fórmulas e exportação `ExportAsFixedFormat`.

**FATO OBSERVADO:** a extração controlada posterior identificou 18 componentes e nove procedimentos, sem eventos automáticos de workbook ou de ciclo de vida das planilhas. Fontes e p-code foram comparados, e os fluxos de novo jogo, limpeza, salvamento e PDF foram executados em cópias descartáveis.

**FATO OBSERVADO:** os testes confirmaram seis defeitos `LVFI-LEGACY-001` a `LVFI-LEGACY-006`, incluindo limpeza incompleta, erro silencioso, escrita não atômica, validação estatística insuficiente, ausência de deduplicação e PDF ilegível. O inventário e os resultados resumidos estão no [documento 12](12-dynamic-audit-and-mathematical-baseline.md).

## 7. Fórmulas e achados matemáticos preliminares

### 7.1 Matriz de placares

**FATO OBSERVADO:** as matrizes examinadas calculam placares de 0 a 6 gols para cada time.

**RISCO:** resultados com sete ou mais gols de qualquer participante ficam fora da soma. No confronto armazenado na planilha, as probabilidades de resultado dos Métodos 1 e 2 totalizam aproximadamente 99,85% e 99,82%.

- **DECISÃO APROVADA — D-MATH-001:** o futuro motor usará cálculo integral, analítico ou adaptativo; massa residual será registrada e observável, sem descarte ou normalização silenciosa. A matriz 0–6 permanece apenas como comportamento observado do legado.

### 7.2 Cores

**DECISÃO APROVADA:** baixa probabilidade é menor que 40%; intermediária é de 40% a 60%; alta é maior que 60%.

**FATO OBSERVADO:** regras da planilha usam limites como `<39,9%` e `>60,1%`, criando pequenos intervalos sem correspondência exata com a decisão.

- **RECOMENDAÇÃO:** centralizar os limites em configuração versionada e usar os mesmos valores na plataforma e no PDF.

### 7.3 Tratamento de erros

**FATO OBSERVADO:** `IFERROR/SEERRO` é a função dominante em `Lançamentos`.

**RISCO:** transformar qualquer erro em vazio dificulta distinguir ausência normal, divisão por zero, referência quebrada e falha de cálculo.

- **DECISÃO APROVADA — D-MATH-011:** entradas serão validadas e erros serão tipados; erro crítico não poderá virar vazio e bloqueará aprovação e publicação.

### 7.4 Legado e inconsistências

**FATO OBSERVADO:** abas antigas contêm rótulos como handicap `+1,4`, enquanto a área principal usa linhas de 0,25.

**FATO OBSERVADO:** a aba oculta `ULTIMOS 10` possui fórmulas com `COUNTA` sobre intervalos que incluem fórmulas, embora o Método 3 principal use testes `ISNUMBER` para contar jogos válidos.

- **DECISÃO PENDENTE:** classificar cada uma dessas abas como vigente, referência histórica ou descartável.
- **RECOMENDAÇÃO:** não migrar fórmula de aba legada sem confirmar se ela participa do fluxo atual.

## 8. PDFs atuais

**FATO OBSERVADO:** os dois PDFs possuem uma primeira página A4 paisagem com muitas tabelas comprimidas e uma segunda página vazia.

**Impacto:** embora o conteúdo seja amplo, sua leitura em tela ou impressão é prejudicada e a página vazia sugere área de impressão excessiva.

**RECOMENDAÇÃO:** reorganizar o relatório em seções e páginas temáticas, conforme [Experiência do usuário e PDF](09-user-experience-and-pdf.md), sem reproduzir a largura da planilha.

## 9. Limitações consolidadas após a auditoria dinâmica

| Limitação remanescente | Consequência |
|---|---|
| A baseline cobre 14 fixtures, não todo o espaço de estados. | Equivalência observada não certifica correção universal do XLSM. |
| A base não registra procedência completa por linha. | Fonte, licença e correções históricas precisam ser reconciliadas na importação. |
| A matriz legada é truncada em 0–6. | O futuro motor seguirá `D-MATH-001`, mesmo quando divergir deliberadamente do legado. |
| O JR-07 usa cenário sintético controlado. | O caso cobre semântica, mas não substitui dados reais de temporada anterior. |
| Há seis defeitos operacionais confirmados. | As rotinas legadas não devem ser migradas como especificação do produto. |

## 10. Encerramento

Os entregáveis dinâmicos, o baseline, os defeitos, os fixtures e as 16 decisões aprovadas foram consolidados em [Auditoria dinâmica e baseline matemático](12-dynamic-audit-and-mathematical-baseline.md). O gate atual permite planejar o Pricing Engine, sem autorizar sua implementação.
