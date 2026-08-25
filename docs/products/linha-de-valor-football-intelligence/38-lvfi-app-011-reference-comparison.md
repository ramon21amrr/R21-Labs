# LVFI-APP-011 — Referência externa e comparação Modelo × Referência

APP-011 acrescenta observações manuais externas, sempre vinculadas a uma partida e
a um snapshot ENG-006 persistido. Cada observação é append-only, possui timestamp,
correlation ID e chave de idempotência; alterações criam novo registro.

As rotas públicas são `POST /matches/{match_id}/market-references`, `GET
/market-references/{observation_id}`, `GET /matches/{match_id}/market-pricings/{market_pricing_id}/market-references`
e `GET /market-references/{observation_id}/comparison`.

A comparação lê somente o payload canônico já armazenado pela ENG-006. Handicap
Asiático, Asian Total e Totais usam quartos de linha inteiros; a diferença assinada
é `referência - modelo`, em passos de 0,25. Para mercados sem linha, ela retorna os
valores comparáveis sem fabricar diferença de passos. A API rejeita seleção, mercado,
linha ou vínculo partida/snapshot incompatível. O navegador apenas apresenta os DTOs.
