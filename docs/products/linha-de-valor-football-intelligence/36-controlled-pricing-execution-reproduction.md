# Reprodução controlada de execuções de precificação

APP-009 reproduz exclusivamente uma execução `completed` da APP-007 usando o
`canonical_input` que já está persistido. Não consulta partidas, não reconstrói
amostras e não modifica a execução original.

`POST /pricing-executions/{execution_id}/reproductions` sempre cria uma tentativa
append-only. A tentativa guarda correlation ID, timestamps, fingerprints de
entrada e resultado, versões original/atual e diferenças ordenadas por caminho.
Os resultados terminais são `exact_match`, `mismatch`, `incompatible_version`,
`blocked` e `technical_failure`.

Schema, Pricing Engine, distribuição e Método 1 precisam coincidir exatamente.
Uma incompatibilidade bloqueia a execução antes da fronteira pública do engine;
payloads antigos não são convertidos. O mesmo vale para entrada canônica inválida.
Em uma versão compatível, a API decodifica estritamente o schema canônico 1,
confirma a impressão digital e chama apenas a fachada pública do Método 1.

`GET /pricing-execution-reproductions/{reproduction_id}` lê uma tentativa e
`GET /pricing-executions/{execution_id}/reproductions?page=1&page_size=25`
lista tentativas por `created_at DESC, reproduction_id DESC`. Os registros são
protegidos por gatilho PostgreSQL contra atualização e exclusão.
