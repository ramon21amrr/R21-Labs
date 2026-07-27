# Construção de amostras históricas do Método 1

## Objetivo

A LVFI-APP-005 adiciona a seleção somente leitura da partida-alvo e das duas
amostras históricas canônicas que serão entregues à futura execução do Método 1.
Ela não calcula taxas, probabilidades, odds, linhas, mercados ou rankings.

## Fonte e fronteira

O endpoint `GET /matches/{match_id}/method-one/sample` usa exclusivamente as
tabelas normalizadas da APP-003 e a camada de consulta assíncrona da APP-004.
O contrato público devolve somente identificadores, nomes, datas e estatísticas
canônicas; não expõe ORM, proveniência, arquivo de origem, hash, linha de fonte
ou credencial.

## Regras autoritativas aplicadas

- A quantidade solicitada é `10`, conforme o preset inicial documentado em
  `03-business-rules-and-market-catalog.md` e `04-pricing-models.md`.
- A amostra do mandante contém somente partidas nas quais o mandante-alvo jogou
  em casa; a do visitante contém somente partidas nas quais o visitante-alvo
  jogou fora.
- Cada série é independente, admite tamanhos assimétricos e registra sua própria
  quantidade encontrada, completude e motivo de insuficiência.
- A seleção restringe-se à competição e temporada da partida-alvo. A inclusão de
  temporada anterior está desativada: a documentação registra essa opção apenas
  como fato observado, sem regra normativa que defina predecessor de temporada.
  Nenhum rótulo de temporada é ordenado ou inferido pela aplicação.
- A ordem canônica é `played_on DESC, match_id ASC`, conforme `D-M1-003`.
- A partida-alvo é sempre excluída. Com a precisão disponível (`date`), somente
  partidas estritamente anteriores na chave `(played_on, match_id)` podem entrar:
  data anterior, ou mesma data com identificador menor. Isso exclui qualquer
  partida futura e torna o desempate de mesma data determinístico.
- Apenas partidas com conjunto de estatísticas normalizadas participam. Zero
  observado permanece válido; ausência de estatísticas não é convertida em zero.
  As estatísticas necessárias para o escopo inicial são gols de primeiro tempo e
  gols de tempo regulamentar, separados por mandante e visitante.

Os estados especiais de `D-M1-007` permanecem a regra de elegibilidade do Método
1. O modelo APP-003 não persiste estado de partida; sua importação controlada
somente materializa observações normalizadas válidas. Se estados forem modelados
em etapa futura, o repositório deverá excluí-los antes de aplicar o limite.

## Completude e bloqueios

Cada série solicita dez partidas. Menos de dez retorna
`complete: false`, a quantidade real e
`insufficient_eligible_matches`; o endpoint mantém a resposta auditável e inclui
warning por série. A classificação de qualidade `0`, `1–4`, `5–9` e `10+` e a
execução do Método 1 pertencem à LVFI-APP-006.

Partida-alvo inexistente retorna `404` sanitizado. Falhas de persistência retornam
o envelope sanitizado já usado pela APP-004. Todas as respostas preservam
`X-Request-ID`.

## Desempenho e testes

O alvo é carregado pela consulta APP-004 e o repositório executa exatamente duas
consultas PostgreSQL Core limitadas e com joins explícitos: uma série para o
mandante e uma para o visitante. Não há consulta por partida, logo não há N+1.

Os testes usam apenas dados sintéticos e cobrem partida inexistente, exclusão da
partida-alvo e de futuras, mesma data, ordenação, separação de mando, temporada,
estatísticas ausentes, insuficiência, contrato público, erro sanitizado,
correlation ID, OpenAPI e PostgreSQL descartável em `127.0.0.1:55432`.
