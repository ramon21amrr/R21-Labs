# LVFI Pricing Engine

Distribuição `1.0.1` do Pricing Engine matemático do Linha de Valor Football
Intelligence, preservado na versão matemática `1.0.0`. O pacote recebe taxas
Poisson já normalizadas, calcula
distribuições e mercados e devolve contratos imutáveis, determinísticos e
auditáveis.

## Capacidades

- Poisson com suporte adaptativo e residual explícito;
- matriz de placares e distribuição de diferença de gols sem renormalização;
- resultado 1X2, dupla chance, ambas marcam e totais simples;
- handicap e total asiático com `WIN`, `HALF_WIN`, `PUSH`, `HALF_LOSS` e
  `LOSS`;
- odd asiática normativa `1 + perdas equivalentes / vitórias equivalentes`;
- linha principal escolhida entre odds definidas pela menor distância até
  `2.00`;
- serialização canônica schema v1, floats em `float.hex()`, JSON UTF-8 compacto
  e SHA-256.

O ponto de entrada é `lvfi_pricing.engine.run_pricing_engine`:

```python
from lvfi_pricing.core import CalculationError
from lvfi_pricing.domain import PoissonRate
from lvfi_pricing.engine import (
    PricingRequest,
    ThreeWayResultRequest,
    run_pricing_engine,
)
from lvfi_pricing.serialization import serialize_pricing_result

request = PricingRequest.create(
    PoissonRate(1.5),
    PoissonRate(1.0),
    (ThreeWayResultRequest(),),
)
if not isinstance(request, CalculationError):
    result = run_pricing_engine(request)
    if not isinstance(result, CalculationError):
        canonical = serialize_pricing_result(result)
```

Falhas de domínio são retornadas como `CalculationError`.

## Runtime e instalação

Requer CPython `>=3.13,<3.14`. O runtime usa exclusivamente a biblioteca padrão
e o wheel não declara `Requires-Dist`.

```powershell
python -m pip install --no-deps lvfi_pricing_engine-1.0.1-py3-none-any.whl
```

O núcleo não lê arquivos, rede, banco, relógio ou variáveis de ambiente. Também
não conhece Excel, fornecedores, aplicações web, PDF ou Value Tracker. O
namespace de fixtures `lvfi_pricing.testing` é exclusivo do source tree de
desenvolvimento e não integra o wheel.

## Desenvolvimento

Crie o ambiente virtual fora do repositório e instale o lock sem adicionar
dependências:

```powershell
py -3.13 -m venv <caminho-fora-do-repositorio>
<venv>\Scripts\python -m pip install -r requirements-dev.lock
<venv>\Scripts\python -m pip install --no-deps --no-build-isolation -e .
```

Gates locais:

```powershell
python -m ruff format .
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest
python -m compileall -q src
python -m pip check
```

A validação final executa 337 testes com 100% de linhas e branches. Detalhes,
limitações e critérios de integração estão na
[validação final](../../docs/products/linha-de-valor-football-intelligence/14-pricing-engine-final-validation.md).

## Limitações

O pacote não implementa os Métodos 1, 2 ou 3, geração de taxas, persistência,
API HTTP, interface, odds de bookmaker, edge, EV, stake, Kelly, recomendações
ou integrações externas. O hash identifica conteúdo; não é assinatura digital
nem prova de autenticidade.
