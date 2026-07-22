# Plano técnico de implementação do catálogo operacional MVP

## 1. Identificação e objetivo

- **Task:** `LVFI-ENG-003-T02-B02`
- **Natureza:** planejamento técnico; nenhuma implementação é autorizada por este documento.
- **Decisão de origem:** [21 — Decisão do catálogo operacional de mercados do MVP](21-market-operational-catalog-decision.md).

Este plano define a implementação futura do catálogo operacional do Linha de
Valor Football Intelligence. O objetivo é limitar a seleção operacional de linha
principal ao catálogo MVP aprovado, preservando o universo matemático amplo,
auditabilidade, determinismo, contratos históricos e hashes já emitidos.

O plano segue o [Company Context](../../company/company-context.md): simplicidade,
baixo acoplamento, evolução incremental, documentação útil e aprovação humana
antes de qualquer alteração material.

## 2. Arquitetura proposta

### 2.1 Alternativas avaliadas

| Opção | Simplicidade | Flexibilidade | Contratos e hashes | Versionamento e manutenção | Decisão |
|---|---|---|---|---|---|
| A. Catálogo fixo interno no módulo de mercados | Inicialmente alta | Baixa; uma mudança altera comportamento implícito | Oculta a origem do resultado e dificulta reproduzir hashes | Exige editar código para cada evolução; não expressa versão própria | Descartada |
| B. Catálogo explícito e versionado como configuração interna aprovada | Alta para o MVP, sem entrada livre | Suporta novos catálogos aprovados sem mudar a matemática | A referência efetiva pode ser registrada no resultado e no hash versionado | SemVer próprio, conteúdo imutável e retenção das versões usadas | Recomendada |
| C. Catálogo informado por request | Baixa; amplia validação e tratamento de erro | Alta, porém prematura para o MVP | Muda request, payload e hash a cada chamada; aumenta superfície pública | Requer governança, autorização e persistência de qualquer catálogo arbitrário | Descartada |

### 2.2 Recomendação

Implementar futuramente a **Opção B** como um registro interno e imutável de
catálogos operacionais aprovados. A primeira entrada será identificada como
`lvfi-mvp` na versão `1.0.0`, com:

- handicap asiático: `-3,00` a `+3,00`, inclusivos, em quartos, totalizando 25 linhas;
- total asiático: `0,25` a `6,00`, inclusivos, em quartos, totalizando 24 linhas;
- exclusão explícita de `0,00` do total operacional; essa linha permanece disponível somente no catálogo matemático.

O catálogo deverá usar `QuarterLine` e tuplas ordenadas de unidades inteiras de
quartos. Sua construção validará imutabilidade, ordenação crescente, ausência de
duplicidade, faixa e simetria do handicap. Não haverá leitura de arquivo externo,
variável de ambiente, banco de dados nem configuração do usuário no MVP.

## 3. Fronteira com o Pricing Engine e contratos futuros

### 3.1 Responsabilidades

O Pricing Engine continuará agnóstico ao produto e à política comercial: Poisson,
matriz, liquidação asiática, preços justos, desempates e funções que recebem
linhas explícitas continuam matemáticos e determinísticos. A geração dinâmica
existente continuará sendo o catálogo matemático interno para pesquisa,
auditoria, testes e chamadas explícitas.

Uma fronteira operacional resolverá `lvfi-mvp@1.0.0` para os candidatos de linha
principal e os encaminhará às funções genéricas de seleção. Essa camada não
alterará fórmula, precisão, liquidação, desempate nem arredondamento; somente
define quais linhas são avaliadas na operação. O `PricingRequest` não aceitará
tuplas livres de linhas nem um catálogo livre informado pelo consumidor.

### 3.2 Impacto recomendado nos contratos

Esta Task não altera contratos. Na implementação autorizada, avaliar e aprovar
conjuntamente as seguintes mudanças:

| Artefato | Recomendação |
|---|---|
| `PricingRequest` | Não expor catálogo arbitrário. Se a execução de linha principal precisar declarar a escolha, aceitar apenas uma referência validada a um catálogo registrado; manter compatibilidade explícita com requisições legadas. |
| `PricingResult` e metadata | Registrar `catalog_id` e `catalog_version` efetivos apenas quando a seleção operacional for solicitada. Distinguir ausência de catálogo operacional de valor desconhecido. |
| Serialização e schemas | Criar versão nova e explícita para o formato que inclua a referência do catálogo. O formato anterior permanece suportado para resultados históricos. |
| Payload canônico e hash | Incluir a referência do catálogo no payload da versão nova, preservando a ordem de arrays e as regras do [ADR-LVFI-007](../../architecture/decisions/ADR-LVFI-007-serializacao-e-hashes.md). Nunca recalcular nem sobrescrever hash histórico com a nova regra. |

A referência do catálogo não substitui a versão do pacote, do modelo ou do schema.
Ela será mais um eixo de identidade, conforme o
[ADR-LVFI-008](../../architecture/decisions/ADR-LVFI-008-estrategia-de-versionamento.md).

## 4. Versionamento e migração

### 4.1 Versionamento

O catálogo operacional inicial será `lvfi-mvp@1.0.0`. A mesma versão não poderá
ser reutilizada para conteúdo diferente. Alterações de linhas exigirão novo SemVer
de catálogo, registro imutável do conteúdo e avaliação de compatibilidade; não
alterarão a versão matemática se fórmulas e regras matemáticas não mudarem.

Cada resultado operacional novo deverá identificar o catálogo efetivamente usado.
Como essa identificação compõe a reprodução operacional, payloads canônicos e
hashes da nova versão refletirão essa referência. Metadados voláteis continuarão
fora do hash.

### 4.2 Migração controlada

- O comportamento atual de seleção dinâmica permanece disponível e é a referência de snapshots e fixtures históricos.
- O novo fluxo operacional usará somente `lvfi-mvp@1.0.0` ao pedir linhas principais asiáticas.
- Snapshots históricos preservam bytes, schema, versão e hash originais; não serão atualizados em massa nem reinterpretados pelo catálogo MVP.
- Novas fixtures devem declarar se cobrem comportamento legado/matemático ou operacional/versionado. Expectativas novas não substituem evidência histórica.
- A compatibilidade deve ser exercitada por serialização e desserialização versionada, sem fallback silencioso de catálogo, schema ou hash.

## 5. Estratégia de implementação futura

1. Introduzir o registro imutável do catálogo operacional e seus validadores, sem remover os geradores matemáticos atuais.
2. Conectar a resolução do catálogo somente à rota de seleção operacional de linhas principais, passando as linhas ao seletor já existente.
3. Evoluir de modo coordenado os contratos, metadata, serialização canônica e versão de schema aprovados para registrar a referência usada.
4. Adicionar migração de fixtures e snapshots por versão, preservando as expectativas históricas em separado.
5. Executar a validação regressiva, determinística e de desempenho antes de alterar qualquer padrão operacional publicado.

Não criar catálogo por competição, fornecedor ou request nesta entrega. Esses casos dependem de necessidade comprovada, decisão de produto e plano específico.

## 6. Testes planejados

### 6.1 Regressão matemática

- Mesmo preço bruto para cada linha existente quando precificada pelo mesmo motor, política numérica e matriz.
- Mesma liquidação integral e parcial para handicap e total, inclusive linhas de quarto.
- Mesma linha selecionada quando a seleção dinâmica e a operacional usam o mesmo conjunto de candidatos.
- Preservação das regras de `D-MATH-001` a `D-MATH-016`, com atenção a `D-MATH-002` a `D-MATH-005`, `D-MATH-012` e `D-MATH-016`, e do [ADR-LVFI-005](../../architecture/decisions/ADR-LVFI-005-handicap-asiatico.md).

### 6.2 Catálogo

- Handicap com exatamente 25 linhas, quartos de `-12` a `+12`, ordem crescente, unicidade e simetria por sinal.
- Total com exatamente 24 linhas, quartos de `1` a `24`, ordem crescente, unicidade e ausência de zero.
- Rejeição tipada de catálogo vazio, fora de ordem, duplicado, com tipo inválido ou conteúdo incompatível com sua identidade aprovada.
- Imutabilidade do conteúdo e resolução determinística de `lvfi-mvp@1.0.0`.

### 6.3 Determinismo, contratos e hashes

- Mesma entrada, catálogo, versões e política geram o mesmo resultado, payload canônico, bytes e hash.
- Resultado legado continua reproduzindo o hash histórico pela versão histórica de schema e serialização.
- Resultado operacional novo possui referência correta ao catálogo e hash distinto quando a mudança de catálogo ou de schema for semanticamente aplicável.
- Arrays mantêm ordem canônica; metadados voláteis não alteram `calculation_hash`.

### 6.4 Performance

- Registrar baseline antes/depois no cenário sintético `10.0 × 10.0` para handicap e total.
- Medir o caminho de seleção com e sem cobertura de testes, após aquecimento e com múltiplas repetições; reportar mediana e dispersão.
- Confirmar `evaluated_lines == 25` para handicap e `evaluated_lines == 24` para total no fluxo operacional.
- Confirmar redução de candidatos de aproximadamente 92,8% e 93,0%, respectivamente; ganho de tempo deve ser reportado como evidência, não inferido apenas pela contagem.

## 7. Critérios de aceite da implementação futura

- Catálogo `lvfi-mvp@1.0.0` reproduz exatamente as 25 linhas de handicap e 24 de total aprovadas.
- Nenhuma regra matemática, liquidação, precisão ou desempate aprovado é alterado.
- Contratos, schemas, payloads e hashes declaram a versão aplicável; snapshots históricos permanecem íntegros.
- Regressão, testes unitários, propriedades, integração, determinismo e performance aprovados; cobertura não diminui sem justificativa e aprovação explícitas.
- `Ruff`, `mypy`, construção de wheel, instalação limpa, `pip check` e smoke test aprovados no ambiente definido pela Task executora.
- Benchmark documentado e revisado, sem regressão no caminho operacional de seleção.
- Sem dependências novas, sem exposição de catálogo arbitrário por request e sem alteração não aprovada de escopo.

## 8. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Alteração indevida de hashes históricos | Versionar schema e serialização; preservar fixtures, bytes e hashes anteriores. |
| Mudança involuntária de payload ou contrato | Evolução explícita, testes de compatibilidade e revisão antes de publicar schema novo. |
| Regressão de preço, liquidação ou desempate | Manter cálculo separado do catálogo e executar regressão matemática por linha. |
| Catálogo MVP não cobrir linha real de fornecedor | Não fazer fallback silencioso; registrar a lacuna e decidir expansão versionada com dados reais. |
| Necessidade futura de múltiplos catálogos | Usar identificação/versionamento desde `1.0.0`, sem criar seleção por fornecedor ou competição antes de haver caso aprovado. |
| Ganho de candidatos não gerar ganho proporcional de tempo | Medir end-to-end e isolar o benchmark de seleção antes de alegar benefício de latência. |

## 9. Validação desta Task documental

Antes do encerramento documental, revisar este plano contra o Company Context,
`ADR-LVFI-005`, `ADR-LVFI-007`, `ADR-LVFI-008` e `D-MATH-001` a `D-MATH-016`.
Validar links relativos e executar `git diff --check`.

Esta Task cria apenas este documento e a referência correspondente no índice do
produto. Não altera código, Pricing Engine, contratos Python, testes, schemas,
pacote, dependências ou artefatos temporários.

**PLANO PENDENTE DE APROVAÇÃO**

A implementação dependerá de:

1. aprovação explícita do Product Owner;
2. execução em modo apropriado;
3. validação regressiva completa;
4. confirmação dos impactos em hashes;
5. gate final da T02.
