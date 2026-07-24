# LVFI-ENG-004 — Estabilidade numérica de totais e baseline versionada

## Decisão e escopo

**DECISÃO APROVADA:** corrigir a estabilidade numérica dos totais simples, promover o Pricing Engine de `1.0.0` para `1.0.1` e a distribuição de `1.1.0` para `1.1.1`.

**PRESERVADO:** Método 1 `1.0.0`, catálogo `lvfi-method-one-adjustments@1.0.0`, schema canônico `1`, API pública, formato de serialização e células materializadas da matriz.

A baseline histórica `1.0.0` e a baseline operacional `1.0.1` estão versionadas em `packages/pricing-engine/tests/integration/pricing_engine_baselines.py` e `packages/pricing-engine/tests/integration/pricing_engine_payload_baselines.json.gz`. Os testes operacionais validam `1.0.1`; os vetores históricos permanecem auditáveis.

## Sintoma e causa raiz

O caso mínimo `0.001953125 × 0.001953125` podia produzir soma materializada acima de um por um ULP. A matriz calculava corretamente cada célula, mas a soma materializada poderia diferir da massa probabilística canônica, produto das probabilidades acumuladas das distribuições Poisson. Totais derivados de subconjuntos podiam então sofrer o mesmo efeito de representação.

## Correção

A matriz continua materializando e preservando cada célula original. A massa total canônica passa a ser o produto das massas acumuladas das distribuições; a soma materializada continua validada contra essa massa dentro da tolerância explícita. Nos totais simples, uma seleção é somada normalmente e a complementar é derivada da massa canônica. Não há normalização de células, clamp global, alteração de tolerâncias, mudança de schema ou ocultação de `CalculationError` material.

## Baselines e hashes

| Cenário | Baseline `1.0.0` | Baseline `1.0.1` | Classificação |
|---|---|---|---|
| `0.0 × 0.0` | `8051a1b099137b2c56df3733e1e418d9ed9f95df3c35761c42b89b71bb311c75` | `92dd0e200cfc270a47db68ca5d141886a7a038ae1bffc03f4c9e6d2397d15a55` | B — somente versão |
| `0.5 × 0.5` | `21271b4f51985ee5bec7c635dc9a25f15b3f5304571c761fc68fb4ac790e2e9b` | `124e7b7755c2942af3030ffb4b8a110d11365277f4bfa746026a5ffa3128441b` | B — somente versão |
| `1.0 × 1.0` | `174828b2a00fabb07fedd8621d6ac696695ae006df18f0eeb9296c853e1c0e51` | `e82cdc5a3a6f928e73c5cde10a64cc0193c76dd2877fc72623dffef841eb19d4` | A — matemática e versão |
| `1.5 × 1.0` | `1b9791d0dd26fbb7bca068d18dc259a5e07ccf6e3fe7ea1bd4a699f59006f10b` | `e45ea750576085fa40d3ebfe0cfc7dde86eeb96cd3dddabcdccd0d3617f4cc2c` | A — matemática e versão |
| `1.0 × 1.5` | `3f271310adaa3ad25689a03f748c8467a2b8b982dcfa0301e9c5c0f6446b1ad9` | `94b555c09467c4028e7606885ae12eb7ba49e264fc99dc7cca3bba4329062060` | A — matemática e versão |
| `2.5 × 1.2` | `4b545f5fb97be85c2adb8d042d601b0ebf53dc4e0acae8408a3e5ceeac6c9210` | `cee70d41efdc544ec2cc293216d029bd243885dc432fb321bd8b37b7d70ddf10` | B — somente versão |
| `5.0 × 3.0` | `f175b1729f579a7048b045c1219f7007c0f51fb6b78b6d7263d62a20c7c42004` | `034edc8c0112f463332c95ab482083715e1b2e7820a06702f28c30a4b06ba370` | B — somente versão |
| `10.0 × 10.0` | `11bdfc2a7addcf241a248f2a6bdfa888e7d4a6aa639095a809f59a11bba5d670` | `e3c69898066ea218fdf087596b9226602c0f21bb1ec023787755242c2a55ecee` | B — somente versão |

Todos os hashes mudam porque `PACKAGE_VERSION` e `PricingEngineMetadata.package_version` fazem parte do payload canônico; a serialização compacta UTF-8, ordem de campos e schema permanecem os mesmos.

Os cinco cenários não afetados matematicamente preservaram integralmente seus resultados, mas receberam novos hashes canônicos porque a versão faz parte da identidade serializada.

## Grupo A: evidência matemática

A massa canônica muda somente no último bit representável nos cenários afetados. Para `1.0 × 1.0`, a massa da matriz passa de `0.9999999999999979` para `0.9999999999999978`, o residual de `2.1094237467877974e-15` para `2.220446049250313e-15` e o UNDER 2.5 de `0.6766764161830635` para `0.6766764161830634`. Para `1.5 × 1.0` e `1.0 × 1.5`, a massa passa de `0.9999999999999946` para `0.9999999999999944` e o residual de `5.440092820663267e-15` para `5.551115123125783e-15`; os preços de totais exibidos permanecem iguais, mas a massa derivada e os mercados dependentes passam a registrar a identidade canônica corrigida.

A auditoria de regressão compara os bytes canônicos completos preservados no fixture compactado. No Grupo B, remove apenas valores de versão e exige igualdade integral do restante do payload. No Grupo A, também mascara exclusivamente campos canônicos de massa, probabilidade e odds derivados; todo o restante precisa coincidir com o payload histórico. Os hashes completos de ambas as versões permanecem congelados no vetor de baseline.

## Método 1 e compatibilidade

O Método 1 continua em `1.0.0` e seu schema canônico continua em `1`. Como seu envelope registra a versão da distribuição, seus vetores operacionais recebem a identidade `1.1.1` sem mudança de fórmula: `e80340fae279a0d2adcc2f6ab31130cfd4cb3b9745a6d0b33d1b31e7afc49b02` → `111aa9233114b89f0e77b4f5890f062f06c94ad0d369bc9465a46a13fb741179` para `baseline_candidate`; os demais vetores seguem o mesmo contrato versionado nos testes. Não houve mudança de API, contrato público ou schema.