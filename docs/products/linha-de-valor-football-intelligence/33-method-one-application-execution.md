# Execução do Método 1 pela aplicação

## Escopo

`POST /matches/{match_id}/method-one/pricing` executa o Método 1 para gols no
tempo regulamentar. A escolha é explícita porque a fronteira pública
`MethodOneRequest` executa um único par `statistic`/`period`; a APP-005 entrega
também os gols do primeiro tempo para uma futura execução pública específica,
sem ampliar esta rota ou introduzir parâmetro não autorizado.

## Fluxo

1. A aplicação obtém a partida e as duas séries determinísticas da APP-005.
2. Ela bloqueia antes do engine se uma série não tiver dez partidas, se a
   temporada anterior estiver habilitada, se a chave temporal/contextual divergir
   ou se qualquer gol obrigatório estiver ausente ou inválido.
3. As séries são convertidas exatamente nas quatro séries públicas: produção e
   concessão do mandante em casa; produção e concessão do visitante fora.
4. A aplicação chama somente `lvfi_pricing.models.method_one` e
   `lvfi_pricing.models.samples`, ambos fachadas públicas do pacote versionado.
5. O retorno HTTP preserva o envelope canônico do engine e seus campos públicos
   de hash e versão; não há arredondamento, normalização, cálculo paralelo ou
   persistência pela API.

O corte usa meia-noite UTC da data normalizada da partida-alvo. A APP-005 já
autoriza somente a chave histórica `(played_on, match_id)` anterior; a APP-006
revalida essa condição e não permite partidas futuras.

## Contrato e erros

O sucesso contém apenas o envelope canônico `MethodOneFinalResult`, hash de
conteúdo, algoritmo, schema e versões públicas do Pricing Engine: pacote `1.1.1`,
Método 1 `1.0.0` e schema canônico `1`. O exemplo OpenAPI é sintético.

Partida inexistente retorna `404` sanitizado. Amostra incompleta ou inválida e
falha tipada do engine retornam `422` sanitizado. Todas as respostas preservam
`X-Request-ID`. A rota não persiste execuções, não expõe proveniência/importação
e não implementa odds de mercado, recomendação, aposta ou Value Tracker.
