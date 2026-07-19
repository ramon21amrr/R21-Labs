# ADR-LVFI-010 — Ferramentas e dependências

## Status

Aprovada

## Data

2026-07-19

## Responsáveis e aprovadores

- Decisão e aprovação: Product Owner
- Registro: planejamento aprovado da `LVFI-ENG-001` e formalização na `LVFI-ENG-002-T01`

## Contexto

O núcleo matemático inicial pode ser implementado com a biblioteca padrão. Dependências numéricas, de validação, web ou persistência aumentariam superfície de atualização sem necessidade demonstrada. Ferramentas de desenvolvimento, por outro lado, são necessárias para testar, tipar e revisar o pacote.

## Problema

Fixar runtime, estilo de domínio e ferramentas mínimas sem instalar bibliotecas antecipadamente nem impedir avaliação futura baseada em evidência.

## Decisão

- suportar CPython 3.13.x;
- fixar a versão menor `3.13` no CI e atualizar patches de forma controlada;
- usar somente a biblioteca padrão no runtime inicial;
- preferir frozen dataclasses, enums e tipos imutáveis equivalentes no domínio;
- usar `pytest`, `pytest-cov`, Ruff, mypy e Hypothesis como dependências de desenvolvimento;
- executar mypy em modo estrito;
- manter Pydantic fora do núcleo;
- admitir NumPy e SciPy somente após necessidade comprovada ou benchmark aprovado;
- considerar `Decimal` apenas em futura camada de apresentação, após decisão de arredondamento;
- manter bibliotecas web, banco, PDF e fornecedores fora do pacote.

## Motivo

A biblioteca padrão atende aos contratos e cálculos aprovados com menor superfície operacional. As ferramentas selecionadas cobrem testes, propriedades, cobertura, lint, formatação e tipagem sem se tornarem dependências de runtime.

## Alternativas consideradas

- NumPy/SciPy desde o início: oferecem vetorização e funções prontas, mas não há necessidade ou benchmark que justifique o custo.
- Pydantic para todos os tipos: facilita validação de borda, porém acopla o domínio a uma biblioteca externa.
- `Decimal` em todo o cálculo: diverge da representação matemática aprovada.
- somente testes de exemplo: insuficientes para invariantes e espaços asiáticos.
- biblioteca padrão no runtime e ferramentas especializadas no desenvolvimento: escolhida pela simplicidade e qualidade verificável.

## Consequências positivas

- runtime pequeno e previsível;
- domínio independente de frameworks;
- propriedades e casos de borda testáveis com Hypothesis;
- tipagem estrita e lint consistentes desde a fundação.

## Consequências negativas

- algumas rotinas numéricas precisarão ser implementadas e revisadas internamente;
- ambiente de desenvolvimento possui várias ferramentas a manter;
- CPython 3.13 pode limitar consumidores ainda presos a versões anteriores.

## Riscos

- ferramenta de desenvolvimento virar dependência de runtime por engano;
- configuração estrita ser relaxada para contornar problemas;
- otimização prematura adicionar biblioteca sem benchmark comparável;
- patch do Python alterar comportamento e entrar no CI sem controle.

## Relação com D-MATH

Viabiliza `D-MATH-001` a `D-MATH-006` com `float` e biblioteca padrão, testa erros e handicap de `D-MATH-011` e `D-MATH-012` e aplica propriedades às validações de `D-MATH-014` e `D-MATH-015`.

## Relação com decisões anteriores

- simplicidade e proibição de ferramentas antecipadas no [Company Context](../../company/company-context.md);
- requisitos de manutenção e qualidade em [Requisitos](../../products/linha-de-valor-football-intelligence/05-requirements.md).

## Impacto sobre Sprints futuras

A `T02` configurará runtime e ferramentas; `T03` a `T13` usarão os mesmos gates. Qualquer nova dependência em `LVFI-ENG-003` a `005` exigirá ADR ou revisão explícita desta decisão, justificativa e evidência.
