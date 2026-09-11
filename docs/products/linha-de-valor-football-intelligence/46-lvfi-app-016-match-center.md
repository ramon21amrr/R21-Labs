# LVFI-APP-016 — Match Center

## Autoridade e fronteira

Task autorizada explicitamente pelo Product Owner em 2026-09-10, sobre a base
estável `9bc9a7cdb58fcdf5947b5a433c602465add453e3`. O contrato consolida as
fontes [05 — Requisitos](05-requirements.md), [09 — Experiência](09-user-experience-and-pdf.md),
[39 — Plano mestre](39-lvfi-master-plan-rebaseline.md), [41 — APP-013](41-lvfi-app-013-statistics-layer.md),
[44 — APP-014](44-lvfi-app-014-catalog-and-configuration.md) e
[45 — APP-015](45-lvfi-app-015-workflow-review-approval-snapshot.md).

O Match Center é uma jornada única, por partida, sem PDF, autenticação ou
múltiplos usuários, Value Tracker, integrações externas, nova matemática ou
qualquer task posterior. APP-012 a APP-015, os Métodos 1/2/3 e o Pricing Engine
continuam com seus contratos e artefatos preservados.

## Jornada e telas

`/matches/{matchId}` apresenta identificação, competição, temporada, data e
disponibilidade de dados. As abas acessíveis são: Visão geral, Precificação,
Estatísticas, Configuração, Análise e snapshot, e Histórico e evidência.

- A visão geral consulta separadamente os resultados dos Métodos 2 e 3 apenas
  após receber todos os seletores explícitos; mostra estado, resultados e a
  evidência retornada pelo servidor.
- Precificação reutiliza a execução e o histórico append-only do Método 1.
- Estatísticas reutiliza a amostra APP-013, inclusive valores ausentes, IDs,
  filtros e warnings.
- Configuração mostra o payload efetivo APP-014, hash e precedência.
- Análise e snapshot mantém o workflow APP-015 e consulta o snapshot aprovado.
- Histórico e evidência orienta para os registros persistidos, snapshots e
  evidências de amostra, sem replicar ou alterar sua procedência.

O frontend trata loading, vazio e erro em cada superfície existente, usa abas
operáveis por teclado/foco nativo e não calcula estatísticas, frequências,
lambdas, hashes ou precedência.

## Contrato HTTP aditivo

- `GET /matches/{match_id}/method-two/result` requer `sample_size`, `context`,
  `season_scope` e uma métrica compatível; requer `previous_season_id` somente
  quando o escopo inclui a temporada anterior.
- `GET /matches/{match_id}/method-three/result` requer `sample_size`,
  `competition_scope`, `season_scope`, `metric`, `comparator` e
  `achievement_target`; aplica a mesma regra explícita de temporada anterior.

As duas respostas têm `method`, `method_version` e `payload` somente leitura.
O payload é a projeção serializada do resultado e da evidência já produzidos
pelos serviços `MethodTwoAdjustedPoissonService` e
`MethodThreeObservedFrequencyService`, que por sua vez reutilizam a camada
estatística APP-013. A rota não persiste execução, não muda configuração e não
chama o Pricing Engine.

APP-015 continua deliberadamente restrita à `pricing_execution` concluída do
Método 1: criar, revisar, aprovar ou congelar resultados dos Métodos 2/3 não é
parte deste contrato. A central os compara visualmente sem fundi-los e sem
atribuir a eles um snapshot APP-015.

## Critérios de preservação

Não há migration, mudança de schema, modificação em `packages/pricing-engine`,
alteração de fixture, versão ou hash congelado. A configuração efetiva é exibida
como evidência e não é convertida silenciosamente em seletor ou default dos
Métodos 2/3; quando falta seletor, a UI solicita a decisão do operador.
