# API de consultas históricas de partidas

## Objetivo

A LVFI-APP-004 expõe uma camada somente leitura para competições, temporadas, times, partidas e estatísticas históricas normalizadas pela APP-003.

## Arquitetura

As rotas FastAPI usam schemas públicos, serviço de aplicação e repositório SQLAlchemy Core assíncrono. O repositório lê exclusivamente as tabelas canônicas da APP-003, com joins explícitos para competição, temporada, mandante, visitante e presença de estatísticas. Nenhum objeto ORM, registro bruto, hash, caminho de arquivo ou detalhe administrativo é devolvido.

## Endpoints

- `GET /competitions` e `GET /competitions/{competition_id}`
- `GET /seasons` e `GET /seasons/{season_id}`
- `GET /teams` e `GET /teams/{team_id}`
- `GET /matches`, `GET /matches/{match_id}` e `GET /matches/{match_id}/statistics`

## Filtros, paginação e ordenação

Listagens recebem `page` (padrão 1) e `page_size` (padrão 25, máximo 100). Partidas aceitam `competition_id`, `season_id`, `home_team_id`, `away_team_id`, `team_id`, `date_from` e `date_to`. A ordenação de partidas é estável por data e identificador; resultados vazios retornam `items: []` com metadados de página.

## Contratos, erros e OpenAPI

As respostas incluem somente identificadores, nomes, datas e estatísticas canônicas. Estatísticas são divididas por mandante/visitante e primeiro tempo/jogo completo, sem métricas derivadas. Parâmetros desconhecidos, IDs inválidos e intervalos de data inválidos retornam envelope sanitizado 422; recursos ausentes retornam 404. Todas as respostas preservam `X-Request-ID`. O OpenAPI descreve rotas, parâmetros e respostas.

## PostgreSQL e desempenho

A consulta de partidas faz joins explícitos e uma consulta de contagem paginada, evitando carregamento por entidade e N+1. Não há migration nesta task: os índices e relações APP-003 existentes são suficientes para os filtros expostos.

## Testes e segurança

A suíte usa somente dados sintéticos e cobre serviços, schemas, rotas, filtros, OpenAPI, erros, correlation ID e repositório. A validação completa exige PostgreSQL descartável, sem workbook, dump, credencial, URL real ou dados históricos versionados.

## Limitações e próxima etapa

Não há autenticação, edição, upload, importação, odds ou execução do Método 1. Próxima etapa: LVFI-APP-005 — Seleção de partida e construção das amostras do Método 1.