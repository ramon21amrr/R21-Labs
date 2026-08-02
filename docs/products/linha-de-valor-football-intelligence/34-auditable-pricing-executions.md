# Execuções de precificação auditáveis

## Escopo

A APP-007 adiciona o recurso persistente de execuções do Método 1, sem alterar o
endpoint não persistente `POST /matches/{match_id}/method-one/pricing` da APP-006
nem a matemática do Pricing Engine. A aplicação chama apenas a fachada pública
`lvfi_pricing.models.method_one`.

Cada tentativa termina em um único registro imutável:

- `completed`: a serialização pública canônica do resultado foi produzida;
- `blocked_sample_incomplete`: uma das séries históricas obrigatórias não tinha
  dez observações elegíveis;
- `technical_failure`: a fronteira pública não produziu um resultado canônico.

Os dois últimos estados são respostas de recurso persistido, não resultados
calculados. O código de falha é sanitizado (`method_one_sample_incomplete` ou
`method_one_execution_failed`) e nunca inclui exceção, caminho local, origem,
planilha, hash de arquivo ou número de linha.

## API pública

- `POST /matches/{match_id}/method-one/pricing-executions` cria um registro e
  retorna `201` para qualquer estado terminal.
- `GET /pricing-executions/{execution_id}` lê somente o snapshot armazenado.
- `GET /matches/{match_id}/method-one/pricing-executions?page=1&page_size=25`
  lista por `created_at DESC, execution_id DESC`; a paginação é limitada a 100.

O cabeçalho `X-Request-ID` é persistido como `correlation_id`. O cabeçalho
opcional `Idempotency-Key` é a única forma de repetir a mesma solicitação:
mesma partida e mesma chave retornam o registro já existente. Sem a chave, cada
POST é uma execução intencional nova, mesmo se suas impressões digitais forem
iguais.

O contrato expõe `execution_id`, estado, timestamps, correlation ID,
fingerprints de amostra/entrada/resultado, versões públicas, parâmetros de
seleção, payload canônico de entrada, resultado canônico e código sanitizado.
Ele não expõe ORM, caminhos, dados de importação, nem campos de odds, valor,
recomendação, oportunidade, aposta ou Value Tracker. Os exemplos OpenAPI são
sintéticos.

## Persistência e repetibilidade

A tabela `pricing_executions` é criada pela revisão `20260802_03`. O insert é
transacional: a aplicação prepara a amostra, a entrada e o resultado antes de
executar um único insert; falha de banco realiza rollback e não deixa registro
parcial. A tabela tem check constraints por formato de estado e gatilho
PostgreSQL `BEFORE UPDATE OR DELETE` que rejeita mutações. A API não oferece
rotas de edição ou exclusão.

A impressão da amostra usa uma projeção JSON ordenada mínima, sem proveniência.
A impressão da entrada usa SHA-256 da representação canônica pública de
`MethodOneRequest`; a impressão do resultado é o `content_hash` público do
payload do Método 1. A entrada e o resultado são armazenados como o texto UTF-8
canônico já produzido pela fachada e são apenas desserializados em consultas —
nunca recalculados.

São persistidas as versões congeladas: Pricing Engine/distribuição `1.1.1`,
Método 1 `1.0.0` e schema canônico `1`.

## Índices e acesso

A chave primária é `execution_id`; a unicidade `(match_id, idempotency_key)`
protege repetição explícita e aceita múltiplos valores nulos. O índice
`(match_id, created_at DESC, execution_id DESC)` suporta a listagem
ordenada. A listagem faz uma verificação de partida, um `COUNT` e uma consulta
paginada, todos set-based; não carrega relacionamentos por item e não introduz
N+1.

A migration é reversível: o downgrade remove gatilho, função e tabela nessa
ordem. A validação usa um banco `codex_task_*` descartável no PostgreSQL
institucional em `127.0.0.1:55432`, removido após os testes.
