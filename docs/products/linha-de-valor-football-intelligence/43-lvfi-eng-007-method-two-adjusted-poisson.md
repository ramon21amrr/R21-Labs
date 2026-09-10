# LVFI-ENG-007 — Método 2: Poisson ajustado

## Autoridade e fronteira

Este contrato implementa as decisões explícitas do Product Owner de 2026-09-09
para `LVFI-ENG-007`, complementadas exclusivamente pela fórmula conceitual do
Método 2 no [Documento 04](04-pricing-models.md) e pelos contratos de amostra
do [Documento 41](41-lvfi-app-013-statistics-layer.md). A fonte de dados
versionada confirma os campos brutos em [Documento 30](30-historical-data-model-and-import.md).

O núcleo é `method_two_adjusted_poisson` `1.0.0`. Não altera Método 1,
Método 3, APP-013 público, Pricing Engine, schemas ou hashes congelados.
Não cria mercado, odds, persistência de execução, endpoint público ou arredonda
qualquer cálculo.

## Seleção e partida concluída

`requested_n` é exatamente 5, 10, 15 ou 20. A seleção usa os jogos concluídos
disponíveis quando houver menos que `requested_n`; `actual_match_count` registra
o total selecionado. O corte é estrito: `played_on < cutoff.played_on` ou mesma
data com `match_id < cutoff.match_id`. A ordem é
`played_on DESC, match_id ASC`.

O predicado canônico é `match_statistics.match_id IS NOT NULL`, já usado pelo
repositório do Método 1. Não há campo de status em `matches`; a existência da
linha 1:1 de estatísticas completas é, portanto, a definição versionada e
inequívoca de partida concluída para este método. Partidas futuras sem
estatísticas não entram na amostra nem na referência.

O modo `venue` seleciona mandante em casa e visitante fora, inclusive nas
referências da competição. O modo `overall` seleciona ambos sem filtro de
mando. A competição é sempre a da partida-alvo. A temporada é `current` ou
`current_and_previous` com o ID explícito da anterior compatível.

## Séries e fórmula

Para cada lado, somente valores reais revisados da projeção histórica entram na
média; `null` permanece indisponível e zero permanece observação válida.

`λ_mandante = (média produção mandante / média referência produção mandante) × (média complemento visitante / média referência complemento visitante) × média referência produção mandante`

`λ_visitante = (média produção visitante / média referência produção visitante) × (média complemento mandante / média referência complemento mandante) × média referência produção visitante`

`λ_total = λ_mandante + λ_visitante`

O individual usa exclusivamente o lambda do respectivo time. A distribuição é
`P(X=k)=exp(-λ) × λ^k / k!`. Não há pesos, ajuste subjetivo ou multiplicador.
Nenhuma etapa arredonda valor; apresentação é a única responsável por formato.

Complementos são projeções inversas da mesma observação real do adversário:

| Produção | Complemento | Projeção real |
| --- | --- | --- |
| gols marcados | gols sofridos | gols marcados pelo adversário |
| escanteios | escanteios cedidos | escanteios do adversário |
| chutes no gol | chutes no gol cedidos | chutes no gol do adversário |
| finalizações | finalizações cedidas | finalizações do adversário |
| faltas cometidas | faltas sofridas | faltas cometidas pelo adversário |
| cartões recebidos | cartões gerados | cartões recebidos pelo adversário |

Uma série sem observação disponível ou uma média de referência igual a zero
produz resultado `blocked` com motivo explícito e a evidência inteira. Não há
substituição por zero.

## Evidência auditável

Cada resultado porta `MethodTwoEvidence` schema 1: alvo, configuração,
predicado de concluída, oito envelopes de série (produção/complemento e suas
referências) e as amostras APP-013 imutáveis. Cada envelope preserva contexto,
temporadas, cutoff, ordem, `requested_n`, `actual_match_count`/contagens,
IDs candidatos e usados, candidatos com valor ou motivo de indisponibilidade,
valores válidos, ausências, média e warnings.

A referência da competição seleciona no máximo N partidas concluídas com os
mesmos filtros. Em `venue`, cada partida contribui a observação do lado
correspondente; em `overall`, cada partida selecionada contribui suas duas
observações reais de lado. O envelope registra separadamente IDs de partidas e
`available_count`, de modo que o universo usado nunca é confundido com N nem
com dados ausentes.

Versões: `configuration_schema_version=1`, `evidence_schema_version=1` e
`result_schema_version=1`. `configuration_fingerprint`,
`evidence_fingerprint` e `result_fingerprint` usam SHA-256 de JSON UTF-8
canônico, ordenado por chave, sem espaços e sem NaN; floats usam `float.hex()`,
datas ISO-8601 e ausências `null`. IDs, ordem, motivos e valores participam do
hash.
