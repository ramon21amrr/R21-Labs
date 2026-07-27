# Contrato da fonte histórica v1

## Identificação e validação

| Item | Valor |
| --- | --- |
| Fonte | `RAMON AUTOMATICA 1.1 2026.xlsm` na área de inputs autorizada |
| Formato | XLSM |
| SHA-256 aprovado | `93AF701AEF942A7C99004F7D95D8BE9D4DEEC81D07A260E376AF8E4ABED4FB7C` |
| Aba e tabela | `JOGOS` / `tbl_jogos` |
| Intervalo | `A:Y` (`A1:Y2130` na validação) |
| Cabeçalhos | 25 |
| Leitura | `openpyxl` em `read_only=True`, `data_only=True`, `keep_vba=False` |
| Macros | Proibidas; não são executadas, lidas ou persistidas pelo importador |
| Status | APPROVED |
| Autoridade | Product Owner — decisão de continuidade da LVFI-APP-003 |
| Data da validação | 2026-07-27 |

O hash foi verificado antes e depois da leitura segura. O arquivo não é versionado,
nem são registrados dados de partidas ou extratos reconstruíveis.

## Mapeamento canônico

Os campos estatísticos representam contagens inteiras não negativas. Zero é uma
observação legítima; `NULL` representa ausência legítima somente onde a coluna é
opcional. Texto em estatística preenchida, número negativo, data inválida e
primeiro tempo maior que o total são erros de rejeição da normalização. O valor
bruto permanece em `source_records` para auditoria.

| Coluna | Cabeçalho original | Campo canônico | Tipo | Obrigatório | Período e regra |
| --- | --- | --- | --- | --- |
| A | `Data` | `matches.played_on` | date | sim | data explícita válida |
| B | `Campeonato` | `competitions.display_name` | text | sim | trim e Unicode; vazio rejeita |
| C | `Temporada` | `seasons.label` | text | sim | rótulo preservado; não infere intervalo de datas |
| D | `Mandante` | `teams.display_name` (home) | text | sim | chave auxiliar normalizada; não pode igualar visitante |
| E | `Visitante` | `teams.display_name` (away) | text | sim | chave auxiliar normalizada; não pode igualar mandante |
| F | `Gols_Mand_1T` | `match_statistics.home_goals_first_half` | integer | sim | `0..`; não pode exceder H |
| G | `Gols_Vis_1T` | `match_statistics.away_goals_first_half` | integer | sim | `0..`; não pode exceder I |
| H | `Gols_Mand_Jogo` | `match_statistics.home_goals_full_match` | integer | sim | `0..`; total de jogo |
| I | `Gols_Vis_Jogo` | `match_statistics.away_goals_full_match` | integer | sim | `0..`; total de jogo |
| J | `Fin_Mand_1T` | `match_statistics.home_shots_first_half` | integer | sim | `0..`; não pode exceder L |
| K | `Fin_Vis_1T` | `match_statistics.away_shots_first_half` | integer | sim | `0..`; não pode exceder M |
| L | `Fin_Mand_Jogo` | `match_statistics.home_shots_full_match` | integer | sim | `0..`; total de jogo |
| M | `Fin_Vis_Jogo` | `match_statistics.away_shots_full_match` | integer | sim | `0..`; total de jogo |
| N | `Chu_gol_Mand_1T` | `match_statistics.home_shots_on_target_first_half` | integer | sim | `0..`; não pode exceder P ou J |
| O | `Chu_gol_Vis_1T` | `match_statistics.away_shots_on_target_first_half` | integer | sim | `0..`; não pode exceder Q ou K |
| P | `Chu_gol_Mand_Jogo` | `match_statistics.home_shots_on_target_full_match` | integer | sim | `0..`; não pode exceder L |
| Q | `Chu_gol_Vis_Jogo` | `match_statistics.away_shots_on_target_full_match` | integer | sim | `0..`; não pode exceder M |
| R | `Esc_Mand_1T` | `match_statistics.home_corners_first_half` | integer | sim | `0..`; não pode exceder T |
| S | `Esc_Vis_1T` | `match_statistics.away_corners_first_half` | integer | sim | `0..`; não pode exceder U |
| T | `Esc_Mand_Jogo` | `match_statistics.home_corners_full_match` | integer | sim | `0..`; total de jogo |
| U | `Esc_Vis_Jogo` | `match_statistics.away_corners_full_match` | integer | sim | `0..`; total de jogo |
| V | `Fal_Mand_Jogo` | `match_statistics.home_fouls_full_match` | integer | sim | `0..`; total de jogo |
| W | `Fal_Vis_Jogo` | `match_statistics.away_fouls_full_match` | integer | sim | `0..`; total de jogo |
| X | `Cart_Mand_Jogo` | `match_statistics.home_cards_full_match` | integer | sim | `0..`; total de jogo |
| Y | `Cart_Vis_Jogo` | `match_statistics.away_cards_full_match` | integer | sim | `0..`; total de jogo |

## Regras de conversão e invalidação

Datas são convertidas por parser explícito; inteiros são aceitos somente quando
representam integralmente uma contagem. Espaços externos e Unicode podem ser
normalizados para chaves auxiliares, sempre preservando o texto bruto e exibido.
Não há fuzzy matching, preenchimento automático ou substituição silenciosa.

O contrato é inválido se o nome, o hash, a aba/tabela, a ordem A:Y, qualquer
cabeçalho ou a quantidade de 25 colunas mudar. Qualquer invalidação exige nova
versão do contrato e decisão do Product Owner antes de importação.

## Modelo e operação

A migration `20260727_02` cria `import_batches`, `source_records`,
`import_issues`, `competitions`, `seasons`, `teams`, `matches` e
`match_statistics`. Batches são idempotentes por hash do arquivo e aba; cada
linha preserva seu hash e valores brutos, inclusive quando rejeitada. A chave
canônica de partida é temporada, data, mandante e visitante. Conflitos não são
mesclados automaticamente e geram issue auditável.

O comando é `python -m lvfi_api.cli historical-import --file <arquivo> --sheet
JOGOS --dry-run` ou `--execute`. O SHA-256 aprovado é o padrão da CLI e pode ser
fornecido explicitamente para fixture ou fonte autorizada futura. Os códigos são
`0` para conclusão sem rejeições, `2` para conclusão com rejeições, `3` para
falha estrutural da fonte e `4` para falha de configuração ou banco.

O perfil agregado externo produzido na validação inicial registra 2.129 linhas,
25 colunas, nenhuma linha vazia ou parcial, nenhuma data inválida, nenhum valor
negativo e nenhuma duplicidade exata ou pela chave de negócio. Ele permanece fora
do Git em área temporária autorizada.
## Validação controlada em PostgreSQL

A validação usou PostgreSQL 16.14 em cluster descartável isolado. O upgrade até
`20260727_02`, o downgrade exclusivo da APP-003 até `20260724_01` e o novo
upgrade foram aprovados. O schema resultante possui oito tabelas APP-003, 58
constraints e 19 índices.

O dry-run da fonte aprovada leu 2.129 registros, com 2.129 aceitos, zero
rejeitados e zero warnings, sem persistir batch. A primeira importação persistiu
um batch, 2.129 registros brutos auditáveis, 2.129 partidas e 2.129 conjuntos de
estatísticas; não houve issues, órfãos ou incoerências primeiro-tempo/jogo. A
segunda importação retornou a fonte como já processada e preservou todas as
contagens.

A role, o banco e as credenciais da aplicação foram temporários e removidos ao
fim da validação. Nenhum XLSM, dado de linha, CSV, dump, credencial ou URL de
banco foi versionado.