# ADR-LVFI-007 — Serialização e hashes

## Status

Aprovada

## Data

2026-07-19

## Responsáveis e aprovadores

- Decisão e aprovação: Product Owner
- Registro: planejamento aprovado da `LVFI-ENG-001` e formalização na `LVFI-ENG-002-T01`

## Contexto

O motor precisa transportar resultados e demonstrar repetibilidade. JSON comum não garante, sozinho, uma representação byte a byte estável, e metadados operacionais como horário e duração fariam execuções matematicamente idênticas produzir hashes diferentes.

## Problema

Definir serialização canônica, algoritmo e fronteira do `calculation_hash` sem misturar transporte, apresentação e metadados voláteis.

## Decisão

- separar JSON de transporte do payload canônico de hash;
- ordenar chaves de objetos;
- preservar a ordem semanticamente definida dos arrays;
- representar floats por `float.hex()` no payload canônico;
- representar enums por códigos canônicos;
- representar timestamps de transporte em UTC;
- representar ausência por `null`;
- usar SHA-256;
- excluir metadados voláteis do `calculation_hash`;
- versionar os schemas e a regra canônica;
- não incluir caminhos locais nem dados privados desnecessários.

## Motivo

A separação permite evoluir o transporte sem alterar implicitamente a identidade matemática. `float.hex()` preserva exatamente o valor `binary64`, e SHA-256 fornece uma identidade estável e amplamente suportada pela biblioteca padrão.

## Alternativas consideradas

- hash do JSON de transporte: sensível a formatação e campos operacionais.
- hash de `repr()` dos objetos: representação não é contrato canônico nem interoperável.
- floats decimais arredondados: podem colidir para resultados binários diferentes.
- incluir timestamp de execução: impede repetibilidade entre execuções equivalentes.
- payload canônico separado: escolhido por preservar identidade e compatibilidade explícitas.

## Consequências positivas

- repetibilidade byte a byte verificável;
- valores `binary64` preservados sem arredondamento;
- metadados operacionais podem variar sem mudar o cálculo;
- contratos podem declarar mudanças incompatíveis por versão.

## Consequências negativas

- existem duas representações a manter;
- arrays exigem regra de ordenação ou preservação explícita;
- mudança do schema canônico altera hashes e requer migração consciente.

## Riscos

- incluir campo volátil por engano;
- ordenar array cuja ordem possua significado;
- usar código de enum instável;
- interpretar o hash como assinatura de autenticidade ou sigilo.

## Relação com D-MATH

Preserva igualdade e tolerâncias de `D-MATH-002`, precisão de `D-MATH-003`, ausência de arredondamento interno de `D-MATH-004` e revisões imutáveis de `D-MATH-016`.

## Relação com decisões anteriores

- requisitos de reprodutibilidade `RNF-001` a `RNF-006` em [Requisitos](../../products/linha-de-valor-football-intelligence/05-requirements.md);
- snapshot imutável em [Domínio e modelo de dados](../../products/linha-de-valor-football-intelligence/06-domain-and-data-model.md).

## Impacto sobre Sprints futuras

A `T12` implementará schemas, serialização e hash. Aplicações futuras armazenarão separadamente o payload matemático, metadados de execução e auditoria. Alterações futuras de contrato exigirão versão de schema sem reescrever snapshots aprovados.
