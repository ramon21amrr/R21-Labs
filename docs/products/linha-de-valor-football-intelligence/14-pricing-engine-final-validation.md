# Validação final do Pricing Engine

## 1. Identificação e decisão

- **Task:** `LVFI-ENG-002-T13`
- **Componente:** `packages/pricing-engine`
- **Versão final:** `1.0.0`
- **Runtime:** CPython 3.13.x, somente biblioteca padrão
- **Schema canônico:** v1
- **Decisão:** **GO para integração por camadas externas**, respeitados os
  critérios e limites deste documento.

A decisão encerra formalmente a `LVFI-ENG-002`. Ela não autoriza iniciar os
Métodos 1, 2 ou 3 nem qualquer aplicação, persistência ou integração externa.

## 2. Escopo concluído do ENG-002

Foram concluídos o núcleo numérico, contratos imutáveis, distribuições,
mercados, liquidação asiática, orquestração seletiva, serialização canônica,
hashing e harness seguro de regressão. A T13 auditou conjuntamente as entregas
T01–T12, corrigiu defeitos comprovados, promoveu o pacote de `0.11.0` para
`1.0.0` e executou os gates finais.

Fontes normativas revisadas: contexto institucional, R21 Development Framework,
documentação LVFI, plano técnico do Pricing Engine, ADR-LVFI-001 a 010 e
histórico Git completo do pacote.

## 3. Módulos concluídos

| Módulo | Responsabilidade final |
|---|---|
| `core` | erros, warnings e política numérica |
| `domain` | value objects matemáticos e linhas em quartos |
| `distributions` | Poisson, matriz e diferença de gols |
| `settlement` | decomposição e cinco estados asiáticos |
| `markets` | mercados básicos, asiáticos e linhas principais |
| `engine` | request, result, metadados e orquestração fina |
| `serialization` | forma canônica, bytes UTF-8 e SHA-256 |
| `testing` | fixtures/harness de desenvolvimento, excluídos do wheel |

O grafo permanece acíclico na direção operacional: fundamentos → distribuições
e liquidação → mercados → engine → serialização. Camadas inferiores não
importam engine ou serialização, e o orquestrador não contém fórmulas de
mercado.

## 4. Decisões matemáticas aplicadas

- cálculos em `binary64/float`, com `math.fsum` nas somas relevantes;
- linhas asiáticas representadas por inteiros de quartos;
- valores não finitos rejeitados;
- suporte Poisson inicialmente `0–10`, adaptativo até residual alvo `1e-14`,
  com limite técnico `1000`;
- massa residual explícita, sem clamp ou renormalização;
- matriz de placares como projeção auditável, não como recorte `0–6`;
- diferença de gols agrega cada célula exatamente uma vez;
- odds simples como inverso da probabilidade quando definidas;
- odds asiáticas pela liquidação integral das parcelas;
- valores brutos preservados, sem arredondamento interno.

## 5. Defeitos encontrados e correções

### 5.1 Odd justa asiática — D-MATH-012

A implementação anterior usava:

`(1 - pushed_fraction) / won_fraction`

Com residual positivo, essa fórmula tratava implicitamente o residual como
perda. A fórmula corrigida é exatamente:

`1 + lost_fraction / won_fraction`

O residual não entra em vitória, push ou perda. Quando `won_fraction == 0`, a
odd permanece ausente e o resultado carrega `FAIR_ODD_UNDEFINED`, sem `NaN` ou
infinito.

### 5.2 Linha principal asiática — D-MATH-005

O critério anterior usava o proxy:

`abs(2 * won_fraction + pushed_fraction - 1)`

Agora somente candidatos com odd definida participam da seleção, usando:

`abs(fair_odds - 2.0)`

Empates dentro da `NumericPolicy` escolhem a linha mais próxima de zero e,
depois, a ordem simétrica canônica. Candidatos sem odd continuam calculáveis e
auditáveis, mas não podem se tornar linha principal. Se nenhum candidato tiver
odd definida, o resultado é `CalculationError(FAIR_ODD_UNDEFINED)`.

Em `0.0 × 0.0`, handicap zero é ignorado porque sua odd é indefinida e a linha
`+0.25` é escolhida entre os preços definidos. Para total asiático `OVER`,
nenhuma linha não negativa possui vitória equivalente; a seleção da linha
principal falha de forma tipada e não retorna contrato parcial.

No contrato `AsianMainLine`, `balance_value` representa a odd justa selecionada
e `balance_distance` representa `abs(balance_value - 2.0)`. Os nomes físicos
foram preservados, portanto o schema canônico continua v1; somente o significado
matemático e os valores foram corrigidos.

### 5.3 Versão e serialização de warnings

O engine ainda declarava `0.10.0` enquanto pacote e serialização declaravam
`0.11.0`. A versão runtime passou a uma única constante compartilhada pelo
engine e envelope canônico, coerente com o pacote `1.0.0`.

O serializador também não reconhecia `CalculationWarning`, embora
`PricingResult` permitisse warnings tipados. O contrato agora serializa warning
e `mappingproxy` com ordem determinística e contexto imutável.

### 5.4 Estabilidade dos testes de propriedades

Dois testes corretos podiam falhar apenas pelo deadline padrão do Hypothesis sob
cobertura. O limite temporal foi desativado nesses testes; geração,
determinismo e invariantes permaneceram inalterados.

## 6. Contratos e API pública

A API pública é definida pelos `__all__` dos módulos abaixo; o namespace raiz
permanece sem aliases.

- `core`: `CalculationError`, `CalculationWarning`, `ErrorCode`,
  `IssueSeverity`, `NumericPolicy` e validadores numéricos.
- `domain`: `Probability`, `FairOdds`, `PoissonRate`, `Weight`, `Multiplier` e
  `QuarterLine`.
- `distributions`: contratos e builders de Poisson, matriz e diferença.
- `settlement`: contratos, enums, split e funções de liquidação asiática.
- `markets`: contratos, seleções, precificadores e seletores de linha principal.
- `engine`: requests fechados, `PricingRequest`, `PricingResult`, metadados e
  `run_pricing_engine`.
- `serialization`: `CanonicalPayload`, conversão canônica, bytes, SHA-256 e
  serialização de `PricingResult`.

Helpers iniciados por `_`, registros internos de roteamento e símbolos de teste
não integram essas fachadas. `lvfi_pricing.testing` é excluído do wheel.

## 7. Mercados suportados

- resultado 1X2;
- dupla chance `1X`, `12` e `X2`;
- ambas marcam, sim e não;
- totais simples em linhas `0.5` a `5.5`;
- handicap asiático HOME/AWAY;
- total asiático OVER/UNDER;
- linhas asiáticas inteiras, meias e de quarto;
- geração de catálogos e seleção de linha principal.

Os cinco estados asiáticos são `WIN`, `HALF_WIN`, `PUSH`, `HALF_LOSS` e `LOSS`.
Odds são justas e sem margem.

## 8. Orquestração

`PricingRequest.create` valida tipos, versão, política, unicidade e catálogo,
depois ordena mercados canonicamente. `run_pricing_engine` constrói cada
distribuição, matriz e diferença uma vez, executa somente os mercados pedidos e
para no primeiro erro. Resultado, erros, warnings e metadados são imutáveis.

Warnings são deduplicados por identidade canônica, mantêm a primeira ocorrência
equivalente e são emitidos em ordem determinística. Erros normais usam
`CalculationError` e `ErrorCode`; mensagens e contextos não carregam stack
trace, caminho local ou dado privado.

## 9. Serialização e hashing

O schema canônico v1:

- ordena chaves;
- preserva ordem semântica de tuplas;
- representa floats por `float.hex()`;
- normaliza `-0.0` para `0.0` conforme decisão aprovada;
- rejeita `NaN`, infinitos, coleções mutáveis e tipos não suportados;
- gera JSON compacto, sem BOM ou newline, codificado em UTF-8;
- usa SHA-256 em minúsculas;
- exclui o próprio hash do conteúdo hasheado.

A correção matemática alterou legitimamente odds, linhas principais, bytes e
hashes. O schema não mudou. Oito hashes sintéticos completos foram revisados e
congelados para taxas de `0.0 × 0.0` até `10.0 × 10.0`; nenhum payload contém
nome, partida, data, fonte ou caminho proprietário.

## 10. Testes e cobertura

- testes anteriores preservados: 309;
- testes finais: 337 aprovados;
- linhas executáveis: 1.558 de 1.558;
- branches: 600 de 600;
- cobertura de linhas: 100%;
- cobertura de branches: 100%.

Os cenários integrados são `0.0 × 0.0`, `0.5 × 0.5`, `1.0 × 1.0`,
`1.5 × 1.0`, `1.0 × 1.5`, `2.5 × 1.2`, `5.0 × 3.0` e `10.0 × 10.0`. Eles
cobrem ordem invertida de request, repetibilidade, mercados básicos e
asiáticos, linhas principais, serialização, hashes, imutabilidade, finitude e
ausência de conteúdo privado. Mudanças de taxa, linha e seleção alteram o hash.

## 11. Determinismo e imutabilidade

Entradas idênticas produzem contratos, bytes e hashes idênticos. A ordem de
mercados no input não altera o request canônico nem o resultado. Não há relógio,
UUID, random externo ou `hash()` nativo no runtime.

Contratos públicos usam frozen dataclasses, enums, tuplas e `mappingproxy`.
Nenhum contrato expõe `list`, `dict` ou `set` mutável. Equality depende de
conteúdo, não de identidade do objeto.

## 12. I/O, dependências e empacotamento

A varredura estática do runtime não encontrou arquivo, `pathlib`, rede, socket,
banco, subprocesso, variável de ambiente, logging de saída, Excel ou acesso a
dados proprietários. `hashlib` e `json` operam somente sobre objetos em memória.

- dependências externas de runtime: zero;
- `Requires-Dist`: ausente;
- `requirements-dev.lock`: intacto;
- wheel: `lvfi_pricing_engine-1.0.0-py3-none-any.whl`;
- instalação limpa: aprovada;
- `pip check` no ambiente original e no ambiente limpo: aprovado;
- importação e smoke test fora do source tree: aprovados;
- `lvfi_pricing.testing`: ausente do wheel.

## 13. Qualidade e gates

- Ruff format: aprovado;
- Ruff check: aprovado;
- Ruff format `--check`: aprovado;
- mypy strict: aprovado;
- pytest completo: aprovado;
- cobertura de linhas e branches: 100%;
- `compileall`: aprovado;
- `pip check`: aprovado;
- build e inspeção do wheel: aprovados;
- smoke completo da API pública: aprovado;
- determinismo em processos separados: aprovado.

## 14. Uso mínimo

```python
from lvfi_pricing.core import CalculationError
from lvfi_pricing.domain import PoissonRate
from lvfi_pricing.engine import PricingRequest, ThreeWayResultRequest
from lvfi_pricing.engine import run_pricing_engine

request = PricingRequest.create(
    PoissonRate(1.5),
    PoissonRate(1.0),
    (ThreeWayResultRequest(),),
)
if not isinstance(request, CalculationError):
    result = run_pricing_engine(request)
```

Chamadores devem tratar `CalculationError` explicitamente e nunca reconstruir
valores a partir de números arredondados de apresentação.

## 15. Instalação

```powershell
python -m pip install --no-deps lvfi_pricing_engine-1.0.0-py3-none-any.whl
python -m pip check
```

O consumidor deve usar CPython 3.13.x e importar somente pelas fachadas públicas
documentadas.

## 16. Limitações conhecidas

- Poisson independente é uma capacidade matemática, não um modelo calibrado de
  futebol.
- O custo da seleção de linha principal cresce com suporte e catálogo; correção
  e auditabilidade prevalecem sobre micro-otimização nesta versão.
- O residual permanece pequeno e explícito, não redistribuído.
- Uma seleção pode ter odd indefinida quando não possui vitória equivalente.
- O hash é identidade de conteúdo, não assinatura ou autenticação.
- O schema v1 exige migração consciente se o contrato estrutural mudar.

## 17. Itens explicitamente fora do escopo

Métodos 1, 2 e 3; geração de lambdas; banco; API HTTP; front-end; autenticação;
PDF; importação de partidas; fornecedores; odds de bookmaker; edge; EV; stake;
Kelly; recomendação; Value Tracker; persistência; rede e qualquer funcionalidade
da fase seguinte.

## 18. Critérios para integração

Uma camada externa pode consumir o engine quando:

1. fornecer apenas valores normalizados e tipos públicos válidos;
2. preservar `engine_version`, schemas, catálogo e `calculation_hash`;
3. tratar erros e warnings tipados sem convertê-los em zero ou vazio;
4. manter arredondamento fora do núcleo;
5. não renormalizar residual;
6. não depender de helpers internos ou `lvfi_pricing.testing`;
7. armazenar metadados operacionais separadamente do conteúdo matemático;
8. passar por plano, aprovação e testes de contrato próprios.

## 19. Próximos passos recomendados

O próximo bloco deve começar somente após gate próprio. A sequência aprovada é
planejar e implementar separadamente os Métodos 1, 2 e 3, usando este pacote
como núcleo imutável. Aplicações, banco, PDF e integrações continuam exigindo
ADRs e Tasks específicas.

## 20. Encerramento formal

O Pricing Engine `1.0.0` atende às decisões `D-MATH` aplicáveis, aos ADRs
LVFI-001 a 010 e aos gates da T13. Não existem pendências bloqueadoras dentro
do escopo da `LVFI-ENG-002`.

**Decisão final: GO para integração controlada por camadas externas.**
