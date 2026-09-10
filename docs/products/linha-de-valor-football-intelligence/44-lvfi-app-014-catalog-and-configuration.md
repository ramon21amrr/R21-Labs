# LVFI-APP-014 — Catálogo e Configuração

## Autoridade e fronteira

Esta task foi autorizada explicitamente pelo Product Owner em 2026-09-10. Ela
implementa uma camada LVFI aditiva e versionada de catálogo e configuração. As
fontes materiais são [39 — Plano mestre](39-lvfi-master-plan-rebaseline.md),
[41 — Camada estatística](41-lvfi-app-013-statistics-layer.md),
[21 — Catálogo operacional](21-market-operational-catalog-decision.md),
[05 — Requisitos](05-requirements.md) e
[ADR-LVFI-008](../../architecture/decisions/ADR-LVFI-008-estrategia-de-versionamento.md).

Não altera o Pricing Engine, os Métodos 1, 2 ou 3, contratos e hashes históricos,
nem conecta o catálogo operacional à seleção de linhas do Engine. Também não
inclui workflow de aprovação, snapshots, Match Center, PDF, recomendações ou
integrações externas.

## Catálogo `lvfi-mvp@1.0.0`

O catálogo é imutável, possui hash SHA-256 do conteúdo canônico e retém sua
referência em cada revisão. A versão inicial contém somente decisões já
autorizadas:

- linhas de handicap asiático em quartos de `-3,00` a `+3,00`, inclusivas (25);
- linhas de total asiático em quartos de `0,25` a `6,00`, inclusivas (24), sem
  `0,00`;
- filtros estatísticos: tamanho `5`, `10`, `15` ou `20`; casa, fora ou geral;
  competição da partida ou todas as elegíveis; temporada atual ou atual e
  anterior; e as métricas `goals_scored`, `goals_conceded`, `result_win`,
  `corners`, `shots_on_target`, `shots`, `cards` e `fouls`;
- bandas de probabilidade: baixa abaixo de 40%, intermediária entre 40% e 60%
  inclusive, e alta acima de 60%.

O catálogo descreve linhas e parâmetros; não expõe pesos ou multiplicadores
livres. Pesos e multiplicadores requerem integração própria com o contrato
matemático congelado e valores não declarados nas fontes não são inventados.

## Revisões e precedência

Uma revisão configura exatamente um parâmetro enumerado do catálogo em um dos
escopos `global`, `competition` ou `match`. Cada gravação é append-only, contém
autor declarado no contexto local, justificativa, horário, versão e hash do catálogo, valor validado e a
referência da revisão que substitui no mesmo parâmetro e escopo. O banco rejeita
`UPDATE` e `DELETE` nas revisões e no catálogo.

Gravações simultâneas da mesma cadeia são serializadas na transação PostgreSQL
por uma chave canônica de catálogo, parâmetro, escopo e alvo; a ponta existente é
travada antes de registrar sua sucessora. O lock é liberado no commit e não afeta
a integridade ou o conteúdo de cadeias independentes.

Para uma partida, a configuração efetiva é resolvida de modo determinístico por
parâmetro: `match → competition → global`. Para cada escopo, somente sua revisão
mais recente é candidata; as anteriores continuam no histórico como substituídas.
Os candidatos não selecionados aparecem na evidência de revisões descartadas,
com seu escopo e hashes. A ausência em todos os escopos permanece explícita: esta
task não inventa valores padrão ausentes das fontes. O resultado inclui referências de todas as revisões candidatas,
escopo/vencedor por parâmetro, hash canônico da configuração efetiva e o contexto
de partida/competição. A mesma partida, catálogo e histórico produzem o mesmo
payload efetivo e hash.

## Contrato HTTP

- `GET /configuration-catalogs/lvfi-mvp/1.0.0` retorna o catálogo imutável e seu
  hash.
- `POST /administration/configuration-revisions` cria uma revisão validada;
  escopo de competição ou partida só aceita o identificador de entidade existente
  no banco.
- `GET /administration/configuration-revisions` retorna o histórico filtrável,
  ordenado deterministicamente e sem expor dados internos não necessários.
- `GET /matches/{match_id}/configuration/effective` retorna apenas a
  configuração reproduzível, a evidência de precedência e o hash efetivo.

A web consome esses DTOs; não recalcula precedência, hash, estatísticas ou
precificação no navegador.

## Limite operacional atual

O produto ainda não possui autenticação/autorização. Portanto, o `actor` é uma
declaração registrada para operação local, não uma identidade autenticada. A
integração de identidade e perfis permanece fora desta task.

## Compatibilidade e validação

A migração é aditiva e reversível: adiciona as tabelas/índices/triggers da
camada sem reescrever dados ou estruturas existentes. A cobertura valida linhas,
valores enumerados, escopos, histórico, append-only, determinismo, precedência,
sanitização de erros, migração PostgreSQL real e regressão dos contratos
existentes. O catálogo continua fora da seleção do Pricing Engine até uma task
expressamente autorizada.
