# LVFI-APP-015 — Workflow de Revisão, Aprovação e Snapshot

## Autoridade e limite

Esta task é autorizada explicitamente pelo Product Owner em 2026-09-10. Ela
implementa, de forma aditiva, o workflow auditável previsto no
[plano mestre](39-lvfi-master-plan-rebaseline.md), sobre uma execução de
precificação já persistida pela aplicação. A fonte atual que satisfaz esse
vínculo é uma `pricing_execution` do Método 1 com estado `completed`: ela já
retém entrada e resultado canônicos, amostra, fingerprints e versões.

O vínculo não executa, reinterpreta ou altera Método 1, Método 2, Método 3 ou o
Pricing Engine. Método 2 e Método 3 não possuem nesta base um registro de
execução HTTP/persistido compatível; integrá-los ao workflow requer uma task
autorizada própria. Esta decisão mantém o contrato aditivo e não reduz os
artefatos já existentes.

Não inclui Match Center, PDF, autenticação ou múltiplos usuários, staking,
apostas ou serviços externos. Enquanto não houver autenticação, `actor` é uma
declaração local registrada, como na APP-014.

## Estados e transições

Uma análise nasce em `draft`. `POST` de cálculo recebe uma execução persistida
`completed` da mesma partida e efetiva a transição `draft → calculated`; o
registro incorpora os metadados de cálculo, mas não modifica a execução de
origem. `POST` de revisão, somente em `calculated`, cria um evento append-only
com `actor`, decisão textual `reviewed`, justificativa e horário. `POST` de
aprovação exige ao menos uma revisão e efetiva `calculated → approved`, também
como evento append-only. Não há transição para trás, reabertura, atualização ou
remoção. Repetir uma transição incompatível é rejeitado.

O histórico ordena deterministicamente por `created_at` e identificador e o
banco proíbe `UPDATE` e `DELETE` nas análises, eventos e snapshots.

## Snapshot e reprodução

Somente a aprovação cria um snapshot, uma única vez por análise. Seu payload
canônico JSON, serializado com chaves ordenadas e separadores estáveis, recebe
SHA-256. Ele congela:

- identificadores e projeção da partida/dados da análise;
- a configuração efetiva APP-014 completa, seus hashes e evidência de revisões;
- execução de origem, entrada e resultado canônicos, estado, todos os
  fingerprints e versões de motor/distribuição/método/schema;
- fingerprint e IDs da amostra, parâmetros públicos, warnings/falha quando
  presentes, e os eventos de revisão/aprovação necessários à auditoria.

O endpoint de consulta devolve apenas esse material persistido. Assim, a leitura
e a reprodução documental do snapshot não consultam configuração, partidas,
amostras nem resultados mutáveis posteriores. O `snapshot_hash` permite validar
o payload integral sem recalculá-lo.

## Contrato HTTP mínimo

- `POST /matches/{match_id}/analyses` cria rascunho;
- `POST /analyses/{analysis_id}/calculate` vincula a execução persistida
  concluída e calcula;
- `POST /analyses/{analysis_id}/reviews` registra revisão;
- `POST /analyses/{analysis_id}/approve` aprova e cria o snapshot;
- `GET /analyses/{analysis_id}` e `GET /matches/{match_id}/analyses` consultam
  análise e histórico;
- `GET /analyses/{analysis_id}/snapshot` e `GET /analysis-snapshots/{snapshot_id}`
  consultam o snapshot imutável.

A API é a única responsável por transições, hashes e captura. A web apenas
consome os DTOs e expõe ações mínimas de criar, calcular, revisar, aprovar e
consultar o snapshot.

## Migração e validação

A migration deve ser aditiva e reversível, com FKs restritivas, índices de
consulta, constraints de estado e triggers de append-only. Os testes cobrem
transições válidas/inválidas, pré-requisito de revisão, determinismo do hash,
integridade e imutabilidade PostgreSQL real, e que o snapshot permanece idêntico
depois de uma nova revisão de configuração ou mudança de dados de origem.
