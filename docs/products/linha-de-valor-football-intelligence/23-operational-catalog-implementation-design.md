# Design técnico do catálogo operacional MVP

## 1. Identificação

- **Task:** LVFI-ENG-003-T02-B03
- **Natureza:** entrega documental; não autoriza implementação.
- **Dependências:** [21 — Decisão do catálogo operacional](21-market-operational-catalog-decision.md), [22 — Plano técnico de implementação](22-operational-catalog-implementation-plan.md), [Company Context](../../company/company-context.md), [ADR-LVFI-005](../../architecture/decisions/ADR-LVFI-005-handicap-asiatico.md), [ADR-LVFI-007](../../architecture/decisions/ADR-LVFI-007-serializacao-e-hashes.md), [ADR-LVFI-008](../../architecture/decisions/ADR-LVFI-008-estrategia-de-versionamento.md) e [D-MATH-001–016](12-dynamic-audit-and-mathematical-baseline.md).
- **Status:** desenho técnico registrado; implementação pendente de aprovação.

O desenho separa o catálogo matemático amplo, preservado para auditoria,
pesquisa e validação, do catálogo operacional MVP, usado para operação,
comparação com mercado, relatórios e seleção da linha principal.

O catálogo inicial é lvfi-mvp@1.0.0: handicap asiático de -3,00 a +3,00, em
quartos, com 25 linhas; e total asiático de 0,25 a 6,00, em quartos, com 24
linhas. Total 0,00 permanece somente no catálogo matemático interno.

## 2. Arquitetura proposta

| Opção | Avaliação | Decisão |
|---|---|---|
| A. Catálogo dentro do Pricing Engine | Acopla regra de produto ao núcleo matemático, reduz a reutilização e torna a evolução de faixas menos explícita. | Rejeitada. |
| B. Módulo de catálogo no domínio LVFI | Mantém conteúdo, versões e imutabilidade sob governança de produto, mas não define sozinho a fronteira de execução. | Parcialmente adequada; fonte do catálogo. |
| C. Resolução na composição/orquestração LVFI | Separa produto, identidade operacional e matemática; preserva o engine reutilizável e permite futuros catálogos aprovados. | Recomendada. |

O catálogo operacional é artefato LVFI explícito, finito, imutável e
versionado. Seu registro contém somente versões aprovadas e retém aquelas
necessárias à auditoria; o MVP não terá configuração livre, arquivo externo,
variável de ambiente ou fallback silencioso.

A composição/orquestração LVFI resolve lvfi-mvp@1.0.0, valida a versão, obtém
candidatos permitidos e solicita a seleção de linha principal com essas linhas
explícitas. Ela é responsável pela política operacional e por vinculá-la ao
resultado.

O Pricing Engine permanece matematicamente agnóstico: recebe linhas explícitas
e executa distribuição, liquidação, precificação, desempate determinístico e
resultados matemáticos. A geração dinâmica existente continua disponível como
catálogo matemático amplo para auditoria, pesquisa, validação e chamadas
explícitas.

## 3. Fluxo operacional futuro

Catálogo operacional versionado → resolução e validação pela composição LVFI →
seleção dos candidatos permitidos → precificação matemática pelo Pricing Engine
→ seleção determinística da linha principal → resultado operacional auditável.

A composição somente limita candidatos operacionais; não muda fórmula, precisão,
arredondamento, liquidação ou desempates aprovados. Para uma linha comum aos
dois catálogos, a liquidação e a odd justa devem ser idênticas. No fluxo MVP,
evaluated_lines deve ser 25 no handicap e 24 no total, sem reduzir ou remover o
catálogo matemático.

## 4. Contratos e identidade operacional

Esta Task não altera código, contratos, schemas ou serialização. A implementação
futura seguirá estas fronteiras:

| Artefato | Direção registrada |
|---|---|
| PricingRequest | Não recebe catálogo livre, catalog_id ou catalog_version definidos pelo consumidor. A composição resolve a política antes de fornecer candidatos explícitos. |
| PricingResult | Permanece resultado matemático determinístico; resultados históricos não serão reinterpretados para inferir catálogo operacional. |
| Metadata e snapshot operacional | A camada LVFI registra catálogo efetivo, versão e vínculo estável com o resultado matemático. Ausência de catálogo é diferente de versão desconhecida. |
| Serialização e schema | Todo formato futuro de identidade operacional será explicitamente versionado; formatos antigos continuam suportados para seus resultados. |

O snapshot operacional futuro registra somente identidade estável: catálogo,
versão, resultado matemático e demais versões efetivas requeridas pelo
[ADR-LVFI-008](../../architecture/decisions/ADR-LVFI-008-estrategia-de-versionamento.md).
Horário, duração e metadados voláteis ficam fora da identidade canônica, conforme
o [ADR-LVFI-007](../../architecture/decisions/ADR-LVFI-007-serializacao-e-hashes.md).

## 5. Hashes, versionamento e migração

O conteúdo de lvfi-mvp@1.0.0 é imutável. Alterar linhas, ordem ou semântica exige
nova versão SemVer de catálogo, independente das versões de pacote, modelo e
schema, com retenção de versões referenciadas.

Snapshots e hashes históricos seguem válidos, imutáveis e verificáveis pela
versão original. Não serão recalculados, sobrescritos ou reinterpretados. Novas
execuções operacionais registram as versões efetivas e hash próprio quando a
identidade, payload canônico ou schema mudar. A referência estável do catálogo
integra a identidade operacional; campos voláteis não a alteram.

| Antes | Depois |
|---|---|
| Seleção de linha principal a partir do catálogo matemático amplo e dinâmico. | Execução operacional resolve lvfi-mvp@1.0.0 e avalia apenas candidatos aprovados. |
| Resultados, schemas, bytes e hashes identificam a execução original. | Novas execuções possuem identidade operacional própria, sem substituir histórico. |

Não haverá fallback automático quando uma linha de fornecedor não estiver no
catálogo MVP. A lacuna será registrada e tratada somente por decisão de produto e
nova versão aprovada.

## 6. Testes e gates futuros

- **Matemática:** mesma liquidação, mesma odd justa para linha igual, simetria do
  handicap e preservação dos invariantes de
  [ADR-LVFI-005](../../architecture/decisions/ADR-LVFI-005-handicap-asiatico.md) e D-MATH-001–016.
- **Catálogo:** 25 linhas de handicap e 24 de total, em quartos, ordem crescente,
  unicidade, versão e exclusão de total 0,00.
- **Determinismo:** resultados, serialização, bytes e hashes repetíveis; fixtures,
  schemas e hashes históricos reproduzíveis por seus formatos originais.
- **Performance:** cenário 10.0 × 10.0, antes/depois, com e sem cobertura,
  aquecimento, repetições, mediana e dispersão; confirmar evaluated_lines igual a
  25 no handicap e a 24 no total.
- **Gates:** pytest, coverage, Ruff, mypy, wheel, instalação limpa, pip check e
  smoke test.

## 7. Riscos e controles

| Risco | Controle planejado |
|---|---|
| Alteração de payload ou contrato | Versionamento explícito e testes de compatibilidade. |
| Alteração de hash histórico | Retenção de schemas, bytes e hashes originais; sem recálculo em massa. |
| Catálogo insuficiente | Registrar lacuna, sem fallback silencioso, e evoluir somente com nova decisão e versão. |
| Múltiplos catálogos futuros | Resolução na composição e registros versionados, sem seleção livre por consumidor no MVP. |
| Integração futura com Value Tracker | Referenciar catálogo versionado no snapshot LVFI sem criar integração nesta Task. |

PLANO PENDENTE DE APROVAÇÃO

A implementação dependerá de:

1. aprovação explícita do Product Owner;
2. execução em modo apropriado;
3. validação regressiva completa;
4. confirmação dos impactos em hashes;
5. gate final da T02.
