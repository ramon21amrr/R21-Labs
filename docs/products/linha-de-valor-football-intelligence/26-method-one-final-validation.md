# Validação final do Método 1

## 1. Identificação e decisão

- **Task:** `LVFI-ENG-003-T10`
- **Componente:** `packages/pricing-engine`
- **Distribuição final:** `1.1.0`
- **Método 1 final:** `1.0.0`
- **Pricing Engine preservado:** `1.0.0`
- **Schema canônico do Método 1:** `1`
- **Decisão técnica:** **READY para integração controlada por camadas externas.**

Esta validação encerra T02–T10 do Método 1. Não autoriza backend, banco, API,
interface, PDF, importação de dados, fornecedores, Value Tracker, Método 2 ou
Método 3.

## 2. Escopo auditado

Foram auditados os contratos compartilhados de amostra, contratos e configuração
do Método 1, médias contextuais, taxas-base, catálogo e resolução de
multiplicadores, integração explícita com o Pricing Engine, orquestração,
serialização, hashing, regressões, exports, empacotamento e documentação.

O fluxo validado é:

```text
MethodOneRequest
→ médias contextuais
→ taxas-base
→ multiplicadores resolvidos e taxas ajustadas
→ PoissonRate + PricingRequest
→ PricingResult
→ MethodOneFinalResult
→ bytes canônicos e identidades SHA-256
```

Não foi encontrado defeito em matemática, contratos públicos, schemas, ordem
canônica, determinismo ou integração. A única correção necessária foi promover
as versões de pré-release para as versões finais e atualizar a documentação. Como
`method_version` e `package_version` integram o conteúdo canônico, essa promoção
altera justificadamente apenas os vetores congelados do Método 1; os hashes do
Pricing Engine permanecem inalterados.

## 3. Contratos, matemática e integração

`run_method_one` recebe quatro snapshots imutáveis e compatíveis: produção e
concessão do mandante em casa, produção e concessão do visitante fora. Somente
observações `OBSERVED`, inclusive zero, participam de cada média uniforme. As
médias usam `math.fsum` e denominadores independentes.

As taxas-base preservam a fórmula aprovada de produção própria e concessão
adversária, com pesos padrão `0.50/0.50`. Os multiplicadores positivos são
aplicados multiplicativamente na ordem do catálogo; cada categoria resolve no
máximo um candidato pela precedência `MATCH → COMPETITION → GLOBAL`, respeitando
a faixa fechada `[0.90, 1.10]` e a aplicabilidade `HOME`/`AWAY`.

Somente `goals/first_half` e `goals/regulation_time` elegíveis, de qualidade não
bloqueada, são convertidos em `PoissonRate`. A construção de `PricingRequest` é
mínima e explícita; o Método 1 não seleciona mercados nem altera o Pricing
Engine. O resultado consolidado conserva explicação, qualidade, warnings,
blockers, versões e resultado de precificação imutáveis.

## 4. API, serialização e identidades

A superfície pública permanece em `lvfi_pricing.models.method_one`, incluindo
`run_method_one`, `MethodOneFinalResult`,
`serialize_method_one_final_result` e `method_one_identity`. Não foram
adicionadas APIs de raiz nem aliases acidentais.

O schema canônico v1 usa JSON UTF-8 compacto, chaves ordenadas, tuplas tipadas,
`float.hex()`, timestamps UTC conscientes e SHA-256 em minúsculas. A identidade
separa:

- `input_hash`: request e candidatos de multiplicador;
- `configuration_hash`: somente `MethodOneConfiguration`;
- `result_hash`: conteúdo consolidado, igual ao `content_hash` do payload.

Os bytes são independentes de locale, timezone local, plataforma e ordem
incidental de mapeamentos. Alterações futuras de schema exigem bump explícito;
a promoção desta Task não alterou schema, fórmula, catálogo ou matemática.

## 5. Versões e hashes de regressão

| Item | Antes | Final |
|---|---|---|
| Distribuição | `1.1.0a10` | `1.1.0` |
| Método 1 | `1.0.0a5` | `1.0.0` |
| Pricing Engine | `1.0.0` | `1.0.0` |
| Schema canônico Método 1 | `1` | `1` |

Vetores finais do Método 1:

- `baseline_candidate`: `e80340fae279a0d2adcc2f6ab31130cfd4cb3b9745a6d0b33d1b31e7afc49b02`
- `no_multipliers`: `4f4a627cb8ee78dd9e876b1e199639455719effa02264489b948233d524974cb`
- `partial_count5`: `77df2df41f0d338d5590eddb9802ef6257a3b6a4710658b12053bfd38e3652bd`
- configuração de regressão: `34a33777d62a07b606e599de23dd2889efb24c19c009ce31775cc6ace35e9c76`

## 6. Qualidade, wheel e instalação limpa

- `pytest`: 548 aprovados; 3.130 statements e 1.044 branches, ambos 100%.
- Ruff check e format check: aprovados.
- mypy strict, compileall e pip check: aprovados.
- Cenário congelado `10.0 × 10.0` do Pricing Engine: aprovado pela suíte de
  validação final; seus hashes permanecem congelados.
- Regressões e propriedades do Método 1: aprovadas, incluindo determinismo,
  precedência, limites, integração e hashes.
- Wheel: `lvfi_pricing_engine-1.1.0-py3-none-any.whl`.
- SHA-256 da wheel:
  `9502aa0e637b3221ac134ef670525cfb3009f928716eb32c4f250deb162958a0`.
- Metadata: versão `1.1.0`, `Requires-Python >=3.13,<3.14`, sem `Requires-Dist`.
- Conteúdo: somente runtime `lvfi_pricing`, `py.typed` e metadata; sem testes e
  sem `lvfi_pricing.testing`.
- Instalação limpa com `--no-deps` e `pip check`: aprovada.
- Smoke fora do source tree: importação da wheel, `run_method_one`, payload e
  as três identidades SHA-256 aprovados.

## 7. Limitações e integração futura

O Método 1 é um núcleo matemático puro: não busca nem persiste dados, não
calibra o modelo Poisson e não produz odds de bookmaker, edge, EV, stake ou
recomendações. O hash é identidade de conteúdo, não assinatura ou mecanismo de
autenticação. A integração futura deve preservar versões, schemas, hashes,
erros e warnings, sem arredondar ou renormalizar o núcleo.

Qualquer aplicação, persistência, fornecedor de dados, distribuição alternativa,
recência não uniforme, Método 2 ou Método 3 requer Task, plano, aprovação e
testes próprios.

## 8. Encerramento

A T10 confirma que o Método 1 `1.0.0` satisfaz as decisões `D-M1-001–007`, os
ADRs aplicáveis e os gates de release, preservando o Pricing Engine `1.0.0`.

**Condição final: READY.**
