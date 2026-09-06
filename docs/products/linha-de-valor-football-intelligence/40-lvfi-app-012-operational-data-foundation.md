# LVFI-APP-012 — Fundação Operacional de Dados

## Autoridade, objetivo e fronteira

Task autorizada pelo Product Owner em 2026-09-06, após a integração da
`R21-GOV-002`. A base é o `main` no commit
`1bd965545de45fa478e1b10e8625ddad3a6ede11`.

Esta task entrega a fundação operacional para um único administrador local:

- prévia e confirmação explícita de importações XLSX, XLSM e CSV;
- identificação de linhas aceitas, rejeitadas, duplicadas e em conflito antes da
  confirmação;
- cadastro de partidas futuras;
- revisões justificadas de estatísticas, sem apagar o valor anterior;
- proveniência de arquivo, hash, origem, ator local, instante e resultado.

Ela não altera o Pricing Engine, Método 1, seus schemas, hashes, fixtures ou
fórmulas. Métodos 2 e 3, configurações, snapshots, Match Center, PDF,
autenticação completa e fornecedores automáticos permanecem fora de escopo.

## Contrato de dados

O layout histórico de 25 colunas continua sendo a referência compatível. O
importador não executa macros e nunca converte ausência em zero. A prévia é
determinística para os bytes enviados: cabeçalho, tipos, valores negativos,
relações primeiro-tempo/jogo, chutes no gol/finalizações, chave canônica e
duplicidade são validados antes de qualquer escrita definitiva.

As tabelas históricas largas existentes continuam sendo a projeção compatível
necessária ao Método 1. A task acrescenta observações/revisões append-only com
partida, estatística, lado, período, valor ou indisponibilidade, origem, motivo,
ator e data. Uma correção atualiza a projeção compatível somente depois de
registrar a revisão; a execução já persistida preserva seus próprios snapshots.

Partidas manuais futuras não recebem estatísticas sintéticas. Elas entram no
mesmo catálogo normalizado de competição, temporada e times, mas sem
`match_statistics` até existir informação completa e validada.

## Interfaces previstas

As APIs existentes permanecem compatíveis. A task acrescenta contratos
administrativos para:

1. enviar arquivo e obter prévia limitada e auditável;
2. confirmar uma prévia com chave de idempotência;
3. cadastrar partida manual futura;
4. listar e criar revisões de uma estatística;
5. consultar lotes, problemas e proveniência sem expor arquivo bruto.

A interface web oferece uma tela administrativa local para prévia/confirmação,
cadastro de partida e correção com motivo. Ela consome os DTOs da API e não
contém cálculo de precificação.

## Migration, reversão e aceite

A migration será exclusivamente aditiva, exceto por permitir `source_record_id`
nulo para partida manual sem arquivo. O downgrade remove os objetos novos e
restaura a obrigatoriedade somente quando não houver partidas manuais; esse
bloqueio evita destruição silenciosa de dados.

O aceite exige importação idempotente, rejeição explícita de inconsistências,
ausência distinta de zero, correção rastreável, preservação dos baselines do
Método 1, testes API/migration no PostgreSQL descartável e inspeção da tela web.

## Validação integral de 2026-09-06

Em PostgreSQL 16 isolado e recém-criado, as migrations foram aplicadas até
`20260906_07`; 116 testes passaram com cobertura de statements e branches em
100%. A execução confirmou prévia/confirmação idempotente, duplicidade, partida
futura, revisão disponível, indisponibilidade distinta de zero e bloqueio de
UPDATE no ledger append-only. Lint, typecheck, testes e build do frontend
passaram; o smoke da página administrativa através do proxy local alcançou a
API e o PostgreSQL isolado. O banco `codex_task_lvfi_app_012` foi removido após
o gate; a instância permanente em `5432` permaneceu fora do fluxo.

O processo isolado da tarefa pode encerrar com `0xC000013A`. O harness passou a
iniciar a tarefa oficial e aguardar o loopback antes de criar, migrar, testar ou
remover um banco descartável. A correção não cria infraestrutura paralela nem
altera o cluster, credenciais, serviço ou banco permanente.
