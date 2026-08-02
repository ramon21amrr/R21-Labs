# Histórico e comparação de execuções de precificação

## Escopo

A APP-008 amplia a leitura dos snapshots imutáveis criados pela APP-007. Não
executa o Método 1, não chama o Pricing Engine e não altera registros. O endpoint
não persistente da APP-006 e a fronteira pública do engine permanecem inalterados.

## Histórico filtrável

`GET /matches/{match_id}/method-one/pricing-executions` aceita paginação limitada
(`page`, `page_size`) e os filtros exatos:

- `status`;
- `created_from` e `created_to`;
- `pricing_engine_version`;
- `method_one_version`;
- `sample_fingerprint`;
- `correlation_id`.

A ordenação é `created_at_desc` por padrão e pode ser `created_at_asc`. Em ambos
os casos `execution_id` é o desempate na mesma direção, portanto a paginação tem
ordem determinística. Todos os filtros são aplicados no banco antes do total e da
página; a consulta não carrega relacionamentos por execução.

O correlation ID já pertence ao contrato público de APP-007. Ele só é usado aqui
como filtro de igualdade desse identificador público; chaves de idempotência e
detalhes administrativos continuam fora da resposta.

## Comparação

`GET /pricing-execution-comparisons?left_execution_id={id}&right_execution_id={id}`
compara duas execuções persistidas. As duas devem existir, ser distintas e
pertencer à mesma partida. Como a tabela é exclusiva do Método 1, não há
conversão nem inferência entre métodos.

A resposta contém campos folha ordenados lexicalmente, cada qual com valores
esquerdo/direito, indicador `equal` e, quando aplicável, `delta`. Ela compara
estado, timestamps públicos, fingerprints, versões, parâmetros públicos
canônicos, entrada canônica, resultado canônico e o código de falha sanitizado.

A comparação declara `canonical_compatible=false` e lista as incompatibilidades
quando divergem schema, versão do Pricing Engine, distribuição ou Método 1. Nessa
situação os payloads continuam visíveis como snapshots, mas nenhum delta é
calculado. Deltas só são emitidos para folhas numéricas não booleanas de entrada
ou resultado canônico sob versões e schema compatíveis. Não há coerção silenciosa
de schema ou versão.

A consulta carrega os dois registros por uma única leitura set-based. Ela não tem
dependência da fachada do engine e não pode recalcular resultado algum.

## Segurança e imutabilidade

As rotas devolvem apenas a projeção pública já estabelecida: não expõem ORM, SQL,
caminhos, dados de planilha/linha de origem, payloads internos, segredos ou stack
traces. Erros de ausência e requisição incompatível usam os envelopes sanitizados
da API; o middleware preserva `X-Request-ID`.

APP-008 não cria rotas de atualização ou exclusão. O gatilho PostgreSQL
append-only de APP-007 continua protegendo `pricing_executions`; a tarefa apenas
executa leituras.
