# Decisão do catálogo operacional de mercados do MVP

## 1. Identificação

- **Task:** `LVFI-DESIGN-001`
- **Natureza:** decisão de produto e documentação
- **Status:** **DECISÃO APROVADA**
- **Implementação:** não autorizada por esta decisão

Este documento formaliza a separação entre o universo matemático preservado pela
R21 Labs e as linhas usadas na operação inicial do Linha de Valor Football
Intelligence. A decisão aplica simplicidade, evolução incremental, documentação
útil e baixo acoplamento conforme o
[Company Context](../../company/company-context.md).

## 2. Contexto e problema

O diagnóstico `LVFI-ENG-003-T02-B01` identificou que a seleção da linha principal
avalia todas as linhas geradas pelo suporte matemático da distribuição. No
cenário sintético `10.0 × 10.0`, o handicap produziu aproximadamente 345
candidatos e o total asiático aproximadamente 341. O custo dominante ocorreu na
precificação repetida de cada candidato.

O universo amplo é útil para completude, investigação de extremos e validação.
Ele não representa, por si só, o conjunto que precisa ser calculado e apresentado
na operação cotidiana. O produto deve precificar linhas relevantes para uso real,
comparação com mercado e relatórios, sem transformar capacidade matemática em
custo operacional automático.

## 3. Decisão

**DECISÃO APROVADA:** o LVFI passa a distinguir dois catálogos com finalidades e
governança próprias.

### 3.1 Catálogo matemático interno

Destina-se a auditoria, pesquisa, validação matemática, cenários extremos e
estudos futuros. Pode conter universo amplo, inclusive linhas sem utilidade
comercial imediata. Não será o catálogo operacional padrão, não determinará
automaticamente a linha principal apresentada e não será reduzido por esta
decisão.

### 3.2 Catálogo operacional LVFI — MVP

Destina-se à precificação prática, comparação futura com mercado, relatórios,
escolha da linha principal operacional e controle de desempenho, payload e
regressão.

É um recorte explícito, finito e versionado. A linha principal operacional será
escolhida apenas entre suas linhas, preservando o critério matemático aprovado de
proximidade da odd justa a `2,00`.

## 4. Catálogo operacional aprovado

### 4.1 Handicap asiático

O MVP contém 25 linhas, de `-3,00` a `+3,00`, inclusive, em incrementos de
`0,25`:

| Linha | Linha | Linha | Linha | Linha |
|---:|---:|---:|---:|---:|
| `-3,00` | `-2,75` | `-2,50` | `-2,25` | `-2,00` |
| `-1,75` | `-1,50` | `-1,25` | `-1,00` | `-0,75` |
| `-0,50` | `-0,25` | `0,00` | `+0,25` | `+0,50` |
| `+0,75` | `+1,00` | `+1,25` | `+1,50` | `+1,75` |
| `+2,00` | `+2,25` | `+2,50` | `+2,75` | `+3,00` |

A faixa amplia o recorte anterior de `-2,00` a `+2,00`, preserva simetria e
cobre partidas com favoritismo mais acentuado.

### 4.2 Total asiático

O MVP contém 24 linhas, de `0,25` a `6,00`, inclusive, em incrementos de
`0,25`:

| Linha | Linha | Linha | Linha | Linha | Linha |
|---:|---:|---:|---:|---:|---:|
| `0,25` | `0,50` | `0,75` | `1,00` | `1,25` | `1,50` |
| `1,75` | `2,00` | `2,25` | `2,50` | `2,75` | `3,00` |
| `3,25` | `3,50` | `3,75` | `4,00` | `4,25` | `4,50` |
| `4,75` | `5,00` | `5,25` | `5,50` | `5,75` | `6,00` |

A faixa incorpora e amplia as linhas simples de `0,5` a `5,5` já suportadas
pelo Pricing Engine e acrescenta linhas inteiras e de quarto. Ela cobre o uso
operacional esperado do MVP, mas não prova cobertura de todos os fornecedores.
A cobertura será reavaliada quando existirem dados reais de provedores.

A linha `0,00` permanece no catálogo matemático, mas não no operacional. Em
`UNDER 0,00`, nenhum resultado produz vitória e a odd justa pode ser
indefinida. O caso-limite não tem utilidade comercial esperada no MVP.

## 5. Por que o universo máximo não é automaticamente o melhor produto

Linhas distantes da prática operacional repetem preços que não serão comparados
ou apresentados, aumentam latência, CPU, `evaluated_lines`, payload e superfície
regressiva e podem transformar extremos matemáticos em comportamento padrão.

O melhor catálogo operacional é o menor conjunto que cobre a necessidade real
com margem consciente para evolução. O universo amplo continua disponível no
catálogo matemático, sem perda de conhecimento ou limitação estrutural.

## 6. Impacto estimado de desempenho

No cenário `10.0 × 10.0`:

| Mercado | Candidatos amplos | Catálogo MVP | Redução | Fator |
|---|---:|---:|---:|---:|
| Handicap asiático | ~345 | 25 | ~92,8% | 13,8 vezes menos |
| Total asiático | ~341 | 24 | ~93,0% | 14,2 vezes menos |

Os números medem candidatos, não prometem redução equivalente do tempo total.
Distribuição, matriz, serialização e outros custos permanecem. Benchmarks
pertencem ao plano técnico futuro.

## 7. Coerência matemática e documental

Esta decisão não altera as decisões da
[auditoria dinâmica e baseline matemático](12-dynamic-audit-and-mathematical-baseline.md):

- `D-MATH-003`: linhas continuam em unidades inteiras de quartos;
- `D-MATH-005`: linha principal continua mais próxima da odd justa `2,00`,
  com os desempates aprovados;
- `D-MATH-012`: linhas de quarto continuam decompostas e liquidadas por inteiro;
- `D-MATH-016`: precificações aprovadas e seus catálogos continuam imutáveis.

Preservar todas as linhas calculadas, como exigem `D-MATH-005` e o
[ADR-LVFI-005](../../architecture/decisions/ADR-LVFI-005-handicap-asiatico.md),
significa preservar as linhas do catálogo escolhido para a execução. Isso não
obriga o catálogo operacional a reproduzir o universo matemático máximo.

Esta decisão supera, apenas para o catálogo operacional do MVP:

- a faixa `-2,00` a `+2,00` do documento
  [03 — Regras de negócio e catálogo de mercados](03-business-rules-and-market-catalog.md);
- o requisito `RF-062` do documento [05 — Requisitos](05-requirements.md);
- a mesma faixa do documento
  [11 — MVP, roadmap e validação](11-mvp-roadmap-and-validation.md);
- a pendência sobre linhas de total do documento 03.

Os documentos 01–20 permanecem inalterados. Para faixas operacionais, este
documento é a decisão mais recente e específica.

## 8. Hashes, payloads, contratos e regressões

Esta tarefa documental não altera payload, hash, `evaluated_lines`, contrato
Python, serialização, schema, regressão ou versão.

Na implementação futura:

- `evaluated_lines` refletirá o catálogo escolhido;
- payload canônico, bytes e hash mudarão, mesmo se linha e preço selecionados
  permanecerem iguais;
- fixtures e hashes afetados ganharão novas expectativas sem sobrescrever
  snapshots históricos;
- resultados anteriores continuarão vinculados às versões e hashes originais;
- mudar apenas valores não exige novo schema se estrutura e tipos não mudarem.

O [ADR-LVFI-007](../../architecture/decisions/ADR-LVFI-007-serializacao-e-hashes.md)
continua suficiente para serialização. O
[ADR-LVFI-008](../../architecture/decisions/ADR-LVFI-008-estrategia-de-versionamento.md)
exige versão independente de catálogo; a implementação deverá estabelecer o
catálogo operacional como `1.0.0` e registrar a versão usada em cada resultado.

## 9. ADR, versão, engine e schema

| Item | Decisão nesta tarefa |
|---|---|
| Novo ADR | Não; ADRs LVFI-005, 007 e 008 cobrem as fronteiras. |
| Mudança de versão | Não. |
| Pricing Engine | Sem alteração. |
| Contrato Python | Sem alteração. |
| Schema | Sem alteração. |

O plano técnico futuro decidirá como fornecer o catálogo à seleção. Expor
candidatos por `PricingRequest`, mudar o padrão do motor ou alterar estruturas
públicas exigirá avaliação de compatibilidade, contratos, schema e eventual ADR.
Esta decisão não antecipa nem autoriza essa escolha.

## 10. Preservação da capacidade futura

Permanecem possibilidades futuras, não requisitos autorizados do MVP:

- catálogos customizados por mercado, competição ou fornecedor;
- modos comercial e pesquisa;
- ampliação versionada de faixas;
- múltiplos catálogos versionados;
- fallback controlado para linha real ausente do catálogo vigente.

Cada possibilidade dependerá de necessidade comprovada, decisão de produto,
plano próprio, testes e avaliação de compatibilidade.

## 11. Recomendação final

Adotar este catálogo como baseline operacional do MVP e preservar separadamente
o catálogo matemático. A implementação deverá usar catálogo explícito e
versionado, medir ganho real e proteger hashes e snapshots históricos. Nenhuma
otimização ou alteração do Pricing Engine está autorizada nesta tarefa.

**DECISÃO PENDENTE DE IMPLEMENTAÇÃO**

A implementação desta decisão dependerá de:

1. aprovação explícita do Product Owner;
2. plano técnico próprio;
3. avaliação de impacto nos hashes;
4. testes regressivos;
5. gate de execução.
