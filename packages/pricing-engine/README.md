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

As fixtures atuais são sintéticas, públicas e mantidas somente em memória. O
harness de regressão é puro, determinístico e compara estruturas tipadas,
usando `NumericPolicy` para floats. Não há fixtures proprietárias, I/O ou
dependências de runtime além da biblioteca padrão.

Inclui a distribuição Poisson adaptativa: materializa inicialmente `0–10`,
expande pelo residual até o alvo padrão de `1e-14` e aplica limite de segurança
de `1000`. Não há truncagem fixa `0–6` nem renormalização silenciosa; falhas de
convergência retornam erros tipados. A rotina permanece pura, sem I/O e com
runtime somente na biblioteca padrão.

A camada de distribuições também combina duas Poisson independentes em uma matriz
auditável de placares e deriva a distribuição de diferença de gols. Ambas
preservam a massa residual combinada, não fazem renormalização nem truncagem
fixa, e permanecem puras, sem I/O e somente com a biblioteca padrão.

Mercados básicos disponíveis nesta etapa: resultado 1X2, dupla chance, BTTS e
totais simples nas linhas de meia unidade de 0.5 a 5.5. As odds são justas,
sem margem, e a massa residual permanece explícita sem renormalização.

O motor liquida handicap e totais asiáticos de forma pura e auditável, com os
cinco estados `WIN`, `HALF_WIN`, `PUSH`, `HALF_LOSS` e `LOSS`. Linhas de quarto
sofrem split canônico nas linhas pares adjacentes, cada uma com metade da stake
conceitual. A decisão usa cálculo inteiro em quartos, sem float, arredondamento
ou cálculo financeiro. A precificação asiática transforma cada célula da matriz
nos cinco estados e em frações esperadas de vitória, reembolso e derrota. A odd
justa é `(1 - pushed_fraction) / won_fraction`; ela fica explicitamente ausente
quando não há fração vencedora. Handicap e totais aceitam linhas inteiras, meias
e de quarto, preservam a massa residual e nunca renormalizam ou aplicam margem.
Os catálogos de candidatos e a seleção da linha principal são determinísticos:
o handicap usa HOME e a linha oposta AWAY com sinal invertido; totais usam OVER
e UNDER na mesma linha. Não há edge, EV, stake, recomendação, I/O ou dependências
de runtime além da biblioteca padrão.

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
