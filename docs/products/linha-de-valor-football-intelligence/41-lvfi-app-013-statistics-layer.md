# LVFI-APP-013 — Camada Estatística Comum

## Autoridade, objetivo e fronteira

Task autorizada pelo Product Owner em 2026-09-07 sobre a base
`2aad5b82359ef0cabcadc66ce9e40583ff033175`. Esta entrega uma camada somente
leitura, comum e reutilizável, de amostras estatísticas históricas para métodos
futuros, Match Center e relatórios. Ela não altera o Pricing Engine, o Método 1,
APP-007 a APP-012, schemas congelados ou matemática de precificação.

Método 2, Método 3, nova fórmula de precificação, Match Center completo, PDF,
autenticação, automações e Value Tracker continuam fora de escopo. Em particular,
`LVFI-ENG-005` não foi iniciada.

## Contrato público e semântica

`GET /matches/{match_id}/statistics/sample` recebe um time participante e uma
configuração explícita: amostra de 5, 10, 15 ou 20 partidas; casa, fora ou geral;
competição da partida ou todas as elegíveis; temporada atual ou atual e anterior
identificada explicitamente; métrica; e, opcionalmente, comparador de frequência.

O contrato suporta gols marcados e sofridos, resultado, escanteios, chutes no gol,
finalizações, cartões e faltas. A resposta tipada expõe filtros aplicados,
ordenamento, partidas candidatas e usadas, IDs, valores válidos, ausências com
motivo, contagens, média, desvio-padrão populacional, coeficiente de variação,
frequências, atingimentos e avisos de completude. Ausência permanece `null`; zero
continua uma observação válida. O DTO web de resposta é distinto do DTO de
requisição para preservar campos obrigatórios anuláveis.

O corte temporal é estrito: partida anterior por data, ou pelo ID menor na mesma
data. A seleção é ordenada por `played_on DESC, match_id ASC`, limitada no banco
e determinística. A consulta SQL é conjunta e limitada, sem N+1. Revisões
estatísticas append-only determinam disponibilidade/valor apenas nesta projeção;
gols sofridos usam corretamente o valor do adversário conforme o mando.

## Interface e preservação arquitetural

O frontend configura os filtros e apresenta o DTO recebido: tamanho real,
filtros, agregados, frequências, partidas usadas e warnings. Não reproduz cálculo
estatístico ou de precificação no navegador. Erros permanecem sanitizados e a
observabilidade preserva correlation ID quando aplicável.

## Validação e integração

No PostgreSQL 16 institucional isolado em `127.0.0.1:55432`, o banco descartável
`codex_task_lvfi_app_013` recebeu todas as migrations vigentes até
`20260906_07`. A suíte completa passou com 174 testes, nenhum skip por ausência de
PostgreSQL e 100% de statements e branches. A execução cobriu tamanhos 5/10/15/20,
casa/fora/geral, competição, temporadas, corte sem look-ahead, ausência distinta
de zero, amostra parcial/vazia, média, desvio-padrão, CV, frequências, IDs usados,
determinismo e a semântica de gols sofridos para ambos os mandos.

Vitest (11), lint, typecheck e build do frontend passaram. O smoke pelo proxy do
Next alcançou frontend → API → PostgreSQL e recebeu o DTO público. O banco isolado
foi removido no encerramento do gate PostgreSQL; a porta 5432, cluster, roles,
credenciais e bancos permanentes permaneceram fora do fluxo.

A entrega técnica foi consolidada no commit
`4a28bd4d5b3e7b9cfb75c1a94834c078d5e55641`, publicada pelo PR #30 e integrada
em `main` exclusivamente por merge commit
`4d9c481627c0447e30ef794cf8645b677441c027`. A task está encerrada
institucionalmente pelo PR documental #31; `LVFI-ENG-005` não foi iniciada.
