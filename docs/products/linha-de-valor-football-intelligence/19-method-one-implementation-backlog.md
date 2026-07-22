# Backlog de implementação do Método 1

## 1. Finalidade e estado

Este backlog divide a LVFI-ENG-003 em Tasks pequenas, verificáveis e dependentes
de gates explícitos. Ele não autoriza iniciar nenhuma Task.

**Estado atual:** `LVFI-ENG-003-T01` documental. A implementação matemática
está em **NO-GO** enquanto as decisões `M1-PEND-001` a `M1-PEND-007` não forem
aprovadas.

## 2. Estratégia de versão

- Pricing Engine atual: `1.0.0`, preservado;
- pacote alvo da ENG-003: `1.1.0`, por adição compatível de capacidade pública;
- Método 1 alvo: `1.0.0` após aprovação e validação matemática;
- sample, configuração, request, result, canonical e integration schemas: v1;
- fórmula e política de recência possuem versões independentes;
- Tasks intermediárias permanecem parte de um release não publicado; somente a
  validação final promove o pacote.

## 3. Gates transversais

Cada Task exige:

1. plano específico aprovado;
2. working tree e baseline confirmados;
3. implementação restrita ao plano;
4. testes e gates de qualidade aplicáveis;
5. revisão e aceite;
6. commit coerente;
7. nenhuma funcionalidade da Task seguinte.

Mudança em fórmula, arquitetura, dependência, schema ou escopo estatístico exige
retorno ao planejamento.

## 4. Sequência recomendada

| Ordem | Task | Entrega | Dependência principal | Versão esperada |
|---:|---|---|---|---|
| 1 | `LVFI-ENG-003-T01` | documentação e gate | ENG-002 aceita | sem mudança de pacote |
| 2 | `LVFI-ENG-003-T02` | contratos de observação e amostra | T01 e novo plano | schemas de amostra v1, release não publicado |
| 3 | `LVFI-ENG-003-T03` | contratos e configuração do Método 1 | T02 | schemas Method 1 v1, release não publicado |
| 4 | `LVFI-ENG-003-T04` | validação e médias contextuais uniformes | T03 e `M1-PEND-003/007` | fórmula de média v1 candidata |
| 5 | `LVFI-ENG-003-T05` | combinação produção/concessão | T04 e `M1-PEND-001/002/006` | fórmula Method 1 v1 candidata |
| 6 | `LVFI-ENG-003-T06` | ajustes, qualidade, erros e warnings | T05 e `M1-PEND-004` | configuração v1 candidata |
| 7 | `LVFI-ENG-003-T07` | integração controlada com engine | T06 e `M1-PEND-005` | integration schema v1 |
| 8 | `LVFI-ENG-003-T08` | serialização e hashing | T07 | canonical schema v1 |
| 9 | `LVFI-ENG-003-T09` | fixtures e regressão consolidadas | T08 | baseline segura candidata |
| 10 | `LVFI-ENG-003-T10` | validação final e release | T09 | pacote `1.1.0`, Método 1 `1.0.0` |

## 5. T01 — planejamento e decisões

### Objetivo

Consolidar fronteiras, contratos, matemática, testes, backlog e gate.

### Arquivos

Documentos 15–20 e índice do produto.

### Critérios de aceite

- fontes autoritativas revisadas;
- estado aprovado, observado, recomendado e pendente separados;
- sete decisões bloqueadoras registradas;
- links, numeração, terminologia e escopo validados;
- nenhuma alteração no pacote ou em documentos 01–14;
- gate final explícito.

### Riscos

- recomendação ser interpretada como decisão;
- documento antigo continuar sendo lido isoladamente;
- fragmentação ou links inconsistentes.

### Validações

Verificação de links, `git diff --check`, escopo Git e inspeção de dados
proprietários.

## 6. T02 — contratos compartilhados de observação e amostra

### Objetivo

Implementar somente os contratos reutilizáveis de observação, janela, definição,
snapshot, exclusão e qualidade da amostra.

### Dependências

- T01 aceita;
- plano específico aprovado;
- nenhuma dependência das fórmulas do Método 1.

### Arquivos previstos

- novos módulos coesos sob `lvfi_pricing.models.samples`;
- fachadas públicas correspondentes;
- testes unitários e de propriedades de amostra;
- documentação do pacote estritamente afetada.

### Critérios de aceite

- estados de observação distinguem zero, ausência, não aplicável, inválido,
  suspeito e pendente;
- snapshots preservam IDs, ordem, filtros, exclusões, versões e hash;
- 5, 10, 15, 20, temporada e período personalizado são representáveis;
- casa, fora e geral são representáveis;
- contratos imutáveis, determinísticos e sem I/O;
- nenhuma regra do Método 1, 2 ou 3 implementada.

### Riscos

- abstração compartilhada prematura;
- contrato assumir persistência futura;
- flags de qualidade divergirem do engine.

### Testes

Estados, invariantes, duplicidade, ordem, cortes, limites, hashes, imutabilidade e
ausência de I/O.

### Versão

Schemas de amostra v1; pacote ainda não promovido.

## 7. T03 — contratos e configuração do Método 1

### Objetivo

Implementar request, configuração, pesos, ajustes, explicação, resultado,
metadados e elegibilidade de distribuição, sem fórmulas de cálculo.

### Dependências

- T02 aceita;
- catálogo de campos revisado;
- plano específico aprovado.

### Arquivos previstos

Módulos sob `lvfi_pricing.models.method_one`, fachada pública, testes e
documentação afetada.

### Critérios de aceite

- configuração chega resolvida, versionada e hasheada;
- pesos e multiplicadores reutilizam tipos públicos existentes;
- request exige quatro snapshots compatíveis;
- result e explanation são imutáveis;
- nenhum cálculo de média, Poisson ou mercado;
- nenhuma alteração incompatível no engine `1.0.0`.

### Riscos

- contratos congelarem decisão matemática ainda pendente;
- metadados voláteis contaminarem identidade;
- Method 1 importar engine ou mercados.

### Testes

Construção nominal, tipos incorretos, schemas, versões, limites, dependências,
imutabilidade e inspeção de imports.

### Versão

Schemas Method 1 v1 candidatos; pacote não promovido.

## 8. T04 — validação e médias contextuais

### Objetivo

Validar os quatro snapshots e calcular médias uniformes auditáveis.

### Dependências

- T03 aceita;
- `M1-PEND-003` e `M1-PEND-007` aprovadas;
- plano específico aprovado.

### Arquivos previstos

Calculador de média e validações no módulo do Método 1, testes unitários,
property-based tests e fixtures sintéticas.

### Critérios de aceite

- `math.fsum` e denominador real;
- zero incluído; estados não observados tratados conforme política;
- vazio bloqueia; `1–4` produz cálculo auditável; `5–9` avisa;
- ordem e IDs preservados;
- política uniforme explícita;
- nenhuma ponderação não aprovada.

### Riscos

- vazio virar zero;
- amostra insuficiente virar erro que impede auditoria;
- resultado depender da ordem acidental.

### Testes

Médias conhecidas, zeros, ausências, estados inválidos, datas empatadas,
canceladas, limites e propriedades de média.

### Versão

Fórmula de média uniforme v1 candidata.

## 9. T05 — combinação de produção e concessão

### Objetivo

Produzir taxas base do mandante e visitante a partir das quatro médias.

### Dependências

- T04 aceita;
- `M1-PEND-001`, `M1-PEND-002` e `M1-PEND-006` aprovadas;
- plano específico aprovado.

### Arquivos previstos

Função pura de combinação, termos de explicação, testes e fixtures.

### Critérios de aceite

- fórmula implementada exatamente na versão aprovada;
- pesos validados e não normalizados;
- denominadores das séries permanecem independentes;
- assimetria segue decisão aprovada;
- explicação reconcilia contribuições e taxa base;
- nenhuma média por quantidade de jogos implícita.

### Riscos

- pesos de recência confundidos com pesos de combinação;
- dupla ponderação por tamanho;
- assimetria escondida.

### Testes

Extremos de peso, exemplos manuais, simetria, linearidade aplicável, assimetria,
tolerância e sensibilidade de hash.

### Versão

Fórmula Method 1 v1 candidata.

## 10. T06 — ajustes, qualidade, erros e warnings

### Objetivo

Aplicar somente ajustes aprovados e produzir explicação e qualidade completas.

### Dependências

- T05 aceita;
- `M1-PEND-004` aprovada;
- catálogo de ajustes aprovado;
- plano específico aprovado.

### Arquivos previstos

Aplicador de ajustes, agregação de qualidade e issues, testes e documentação.

### Critérios de aceite

- composição idêntica à decisão aprovada;
- etapas antes/depois preservadas;
- faixa e exceções de multiplicadores validadas;
- qualidade agregada usa pior snapshot;
- warnings determinísticos e seguros;
- erros críticos não produzem taxa parcial.

### Riscos

- extremos por fatores correlacionados;
- ordem não determinística;
- catálogo diferente por estatística sem versão.

### Testes

Identidade, sequência, faixa, exceções, duplicidade, aplicabilidade, qualidade,
mensagens seguras e hashes.

### Versão

Configuração e explicação v1 candidatas.

## 11. T07 — integração com o Pricing Engine

### Objetivo

Converter taxas elegíveis em `PoissonRate` e provar composição com
`PricingRequest` e `run_pricing_engine`, sem o Método 1 chamar o engine.

### Dependências

- T06 aceita;
- `M1-PEND-005` aprovada;
- plano específico aprovado.

### Arquivos previstos

Contrato/função de elegibilidade na camada do modelo, envelope de composição e
testes de integração. O orquestrador existente não será alterado salvo nova
aprovação explícita e compatível.

### Critérios de aceite

- somente estatística/período aprovados viram `PoissonRate`;
- primeiro tempo e partida usam requests separados;
- engine recebe os valores brutos;
- Method 1 não seleciona mercados;
- erros do modelo impedem chamada do engine;
- contratos e hashes v1 existentes permanecem idênticos.

### Riscos

- toda taxa ser tratada como Poisson;
- período se perder no envelope;
- integração contaminar o engine com amostras.

### Testes

Nominal, estatística não elegível, qualidade inválida, taxas extremas, versões,
regressão completa do engine e inspeção do grafo.

### Versão

Integration schema v1 candidato; engine permanece `1.0.0`.

## 12. T08 — serialização e hashing

### Objetivo

Produzir payload canônico e SHA-256 para request, configuração, amostra,
resultado e envelope do Método 1.

### Dependências

- T07 aceita;
- schemas congelados;
- plano específico aprovado.

### Arquivos previstos

Serialização específica do Método 1 sob a camada de serialização, fachada,
testes unitários, propriedades e documentação.

### Critérios de aceite

- `float.hex()`, UTF-8, chaves ordenadas e ordem semântica;
- metadados voláteis excluídos;
- hashes sensíveis a todo conteúdo matemático;
- nenhuma alteração nos bytes/hashes existentes do `PricingResult`;
- serialização não recalcula nem arredonda.

### Riscos

- ciclo entre modelo e serialização;
- campo volátil no hash;
- mudança acidental do schema v1 do engine.

### Testes

Bytes congelados sintéticos, repetição, sensibilidade, schema inválido, tipos não
suportados, separação de hashes e processos distintos.

### Versão

Canonical Method 1 schema v1 candidato.

## 13. T09 — fixtures e regressão consolidadas

### Objetivo

Completar a cobertura segura da fórmula normativa e das divergências históricas
relevantes.

### Dependências

- T08 aceita;
- revisão de propriedade intelectual;
- plano específico aprovado.

### Arquivos previstos

Fixtures sintéticas/sanitizadas, harness de regressão e testes nas áreas já
aprovadas.

### Critérios de aceite

- catálogo M1-FX-001 a M1-FX-014 coberto;
- regressão normativa separada da histórica;
- nenhuma identificação proprietária;
- hashes e expectativas revisados;
- decisões `M1-PEND` rastreadas aos casos correspondentes.

### Riscos

- fixture sanitizada ser reidentificável;
- comportamento do Excel ser tratado como norma;
- cobertura numérica sem cobertura semântica.

### Testes

Suíte completa unitária, property, regressão, integração, segurança e
determinismo.

### Versão

Baseline segura candidata para Method 1 `1.0.0`.

## 14. T10 — validação final

### Objetivo

Auditar conjuntamente T02–T09 e decidir release e integração controlada.

### Dependências

- todas as Tasks anteriores aceitas;
- sete decisões matemáticas aprovadas;
- plano específico aprovado.

### Arquivos previstos

Correções comprovadamente necessárias, documentação pública do pacote e
documento final de validação. Nenhuma aplicação externa.

### Critérios de aceite

- pytest, cobertura de linhas e branches, mypy strict, Ruff, `compileall` e
  `pip check` aprovados;
- build, instalação limpa e smoke da API pública aprovados;
- regressão integral do engine `1.0.0` preservada;
- desempenho dentro do orçamento ou divergência decidida;
- ausência de I/O, dependências externas e dados privados;
- documentação de versões, schemas, erros e limitações concluída;
- gate final explícito.

### Riscos

- promoção de versão antes do aceite;
- mudança incompatível escondida como adição;
- desempenho induzir dependência prematura.

### Testes

Todos os gates da [estratégia de testes](18-method-one-test-strategy.md), wheel
limpo e determinismo entre processos.

### Versão

Pacote `1.1.0`, Método 1 `1.0.0` e schemas v1, somente se o gate final for GO.

## 15. Trabalho futuro fora da sequência inicial

- política de recência não uniforme;
- estatísticas além do escopo aprovado;
- distribuições alternativas;
- integração com banco, API, interface ou PDF;
- Método 2 e Método 3;
- calibração automática por resultados operacionais.

Cada item exige Initiative/Task e decisão próprias.

## 16. Referências

- [Plano técnico](15-method-one-technical-plan.md)
- [Catálogo de contratos](16-method-one-contract-catalog.md)
- [Decisões matemáticas](17-method-one-mathematical-decisions.md)
- [Estratégia de testes](18-method-one-test-strategy.md)
- [Gate](20-method-one-planning-gate.md)
