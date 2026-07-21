# LVFI Pricing Engine

Pacote Python que abrigará o núcleo matemático isolado do Linha de Valor
Football Intelligence. A fundação inclui value objects matemáticos fundamentais
(`Probability`, `FairOdds`, `PoissonRate`, `Weight`, `Multiplier` e
`QuarterLine`), com validação tipada e política numérica centralizada.

## Fronteiras

O pacote usa CPython 3.13.x e terá apenas a biblioteca padrão como dependência de
runtime. O núcleo não realiza I/O, não consulta rede, banco, ambiente ou relógio
e não conhece Excel, aplicações web, fornecedores ou geração de PDF.
O runtime continua usando somente a biblioteca padrão.

Os value objects não fazem coerção silenciosa nem I/O; `QuarterLine` é
armazenada como quartos inteiros. O runtime continua usando somente a biblioteca
padrão.

Estão fora desta Task: distribuições, mercados, liquidação, precificação,
Métodos 1, 2 e 3, fixtures matemáticas, serialização, hashes e integrações.

## Ambiente de desenvolvimento

Crie o ambiente virtual fora do repositório e, a partir desta pasta, execute:

```powershell
py -3.13 -m venv <caminho-fora-do-repositorio>
<venv>\Scripts\python -m pip install --index-url https://pypi.org/simple -r requirements-dev.lock
<venv>\Scripts\python -m pip install --no-deps --no-build-isolation -e .
```

Com o ambiente ativado, os gates locais são:

```powershell
python -m pytest --no-cov
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pip check
```

O primeiro comando executa somente os testes; o segundo inclui cobertura de
branches, linhas ausentes e o limite mínimo de 90%.

## Estrutura inicial

```text
pricing-engine/
├── pyproject.toml
├── README.md
├── requirements-dev.lock
├── src/lvfi_pricing/
│   ├── __init__.py
│   └── py.typed
└── tests/unit/test_package_import.py
```

As fronteiras e a evolução planejada estão no
[plano técnico](../../docs/products/linha-de-valor-football-intelligence/13-pricing-engine-technical-plan.md)
e nos [ADRs LVFI](../../docs/architecture/decisions/). A API matemática desta
Task está concentrada em `lvfi_pricing.domain`.
