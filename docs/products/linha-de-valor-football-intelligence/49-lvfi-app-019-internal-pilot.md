# LVFI-APP-019 — Piloto interno e validação operacional

## Autoridade, objetivo e limites

Esta task foi autorizada explicitamente pelo Product Owner em 2026-09-12. O
objetivo foi validar o LVFI em operação interna real, antes da decisão de corte.
Em 2026-09-13, o Product Owner aprovou a evidência final, o cutover interno e a
publicação/encerramento institucional. A autorização não inclui dinheiro real,
transação financeira, comercialização, Value Tracker, coleta/provedor externo
ou integração externa.

APP-012 a APP-018, o Pricing Engine e os Métodos 1, 2 e 3 são contratos
preservados. O Método 1 continua congelado; os resultados dos três métodos são
registrados separadamente. O workflow auditável e o PDF são aplicáveis à
execução persistida do Método 1 conforme a APP-015; Método 2 e Método 3 não
ganham persistência, workflow ou matemática nesta task.

O controle do piloto separa o banco `codex_task_*` usado por testes PostgreSQL
do banco descartável usado para importação/piloto. Fixtures de integração usam
IDs explícitos, que não avançam sequências PostgreSQL; reutilizar esse mesmo
banco para uma importação poderia provocar colisão artificial de sequência.
O contorno é remover o banco de testes e criar/migrar outro banco descartável
antes da importação, nunca aplicar `setval` no cluster permanente nem modificar
dados ou contratos do produto.

## Critérios oficiais de piloto e corte

As fontes de autoridade são o documento 11 (seções 4, 8 e 11), o documento 39
(gates de aceite do programa) e `GOV-D-015`. O piloto só pode recomendar a
decisão de corte quando houver carga válida, comparação paralela com a
planilha-oráculo/legado disponível, reprodução, backup e restauração ensaiados,
PDF aceito, ausência de regressão crítica, pelo menos 20 análises distribuídas
por cinco competições e aceite explícito do Product Owner. A decisão de corte
permanece humana e não é produzida por este protocolo.

## Regras de evidência e dados

1. Cada análise usa exclusivamente uma partida real e dados importados ou
   cadastrados com proveniência rastreável. Fixtures e dublês de teste validam
   o harness, mas nunca contam para os mínimos do piloto.
2. Antes de executar, registrar para cada fonte: identificador, origem,
   fingerprint SHA-256 quando aplicável, competição, temporada, quantidade de
   partidas e estatísticas aceitas/rejeitadas. Não registrar conteúdo privado
   nem credenciais no repositório ou nos logs.
3. Cada entrada da matriz tem um `analysis_key` estável, data/hora, partida
   selecionada, competição, corte temporal, configuração efetiva e IDs das
   amostras. O corte é estrito e não admite look-ahead.
4. A comparação LVFI × legado/oráculo registra método, versão, configuração,
   seleção, mercado/linha quando houver, valores brutos e exibidos, tolerância,
   diferença e justificativa. Se não houver oráculo disponível para uma
   análise, registrar `indisponível`; ela não satisfaz o critério de comparação
   paralela.
5. Não preencher lacunas com dados sintéticos, valores estimados ou resultados
   de testes. O relatório distingue capacidade validada por testes de análise
   real validada no piloto.

## Critério metodológico aprovado — fechamento técnico

Por decisão explícita do Product Owner, a validação paralela do piloto é
separada por método. Método 1 e Método 2 só são comparados ao legado onde a
saída está observável e vinculada de modo reproduzível à análise; ausência de
vínculo não pode ser preenchida por recálculo do XLSM nem por inferência de
células. Método 3 é validado exclusivamente contra os baselines e fixtures
sanitizados, versionados e aprovados da `LVFI-ENG-005`, preservando o contrato
`method_three_observed_frequency` `1.0.0`, seu cutoff estrito e a semântica de
ausência. Esta decisão não transforma o XLSM em oráculo de vínculos que ele não
registra e não autoriza mudança de matemática, versões, fixtures, contratos ou
APP-012–018.

## Protocolo de execução

### Preparação

- Resolver `HEAD`, `main` e `origin/main` no runtime; validar o baseline e
  executar o perfil de qualidade aplicável.
- Usar banco PostgreSQL descartável `codex_task_*` pelos scripts versionados,
  sem criar cluster, `.env`, `connection.json` ou arquivo de credenciais.
- Inventariar dados reais disponíveis e criar a matriz de 20 `analysis_key` em
  pelo menos cinco competições. Se a matriz não puder ser completada, executar
  somente as chaves sustentadas e registrar o déficit exato por competição.

### Uma análise válida

1. Capturar evidência da importação/revisão que disponibilizou os dados.
2. Selecionar a partida, confirmar competição, temporada e corte.
3. Capturar amostras e IDs dos Métodos 1, 2 e 3; executar os três métodos com
   configuração/versionamento explícitos e preservar warnings ou bloqueios.
4. Executar comparação com o legado/oráculo disponível, sem apagar divergência.
5. Para a execução persistida concluída do Método 1, criar análise, calcular,
   revisar, aprovar e obter snapshot imutável. Gerar PDF exclusivamente desse
   snapshot e verificar identificador, hash e template. Consultar o histórico
   de auditoria e comprovar reprodução documental pelo snapshot.
6. Registrar duração das etapas, impedimentos de usabilidade, retrabalho,
   defeitos e classificação P0/P1/P2/P3. Um defeito sem reprodução é marcado
   como observação e não como defeito confirmado.

### Recuperação

Executar o ensaio APP-018 com PostgreSQL, PDFs, metadados e configuração em
ambiente descartável. Confirmar hashes, `/health`, `/ready`, um snapshot
aprovado e seu PDF; registrar RPO/RTO observados e remover o banco temporário.

## Classificação

| Classe | Critério operacional |
| --- | --- |
| P0 | perda/corrupção de dados, exposição sensível, resultado crítico incorreto ou indisponibilidade sem contorno |
| P1 | jornada crítica bloqueada com contorno impraticável ou divergência material não explicada |
| P2 | defeito relevante com contorno seguro, atraso importante ou retrabalho repetível |
| P3 | defeito menor de clareza, ergonomia ou apresentação sem afetar integridade |

P0 ou P1 aberto impede recomendação técnica positiva. P2/P3 permanecem visíveis
no painel, com impacto e contorno, e não são mascarados por agregação.

## Painel final mínimo

O resumo final informa, sem arredondar ou inferir: análises reais validadas,
competições distintas, chaves comparadas com oráculo, cobertura por etapa,
divergências, contagens P0/P1/P2/P3, desempenho, usabilidade/retrabalho,
resultado da recuperação, gates, critérios atingidos/não atingidos, déficit de
dados e recomendação técnica `APTO` ou `NÃO APTO` para decisão do Product Owner.

## Execução e fechamento técnico — 2026-09-13

O Graphify existente foi consultado como índice, mas é anterior ao HEAD; as
conclusões materiais foram confirmadas nos originais. A fonte XLSM aprovada foi
lida somente após SHA-256 `FDCA46B855CC3FA28A34F622D282221F9B8E3EA41B0B6664432D9614D45D3924`
e revalidada após a inspeção. Não houve acesso a `APOSTAS`, recálculo, gravação
ou atualização do workbook.

As evidências privadas retidas registram 20 jornadas técnicas distintas em
cinco competições: dados importados, partida, amostras e versões M1/M2/M3,
configuração, cálculo, revisão, aprovação, snapshot, PDF e reprodução exata.
O XLSM não possui vínculo histórico reproduzível por `analysis_key`, cutoff,
seletores, amostras ou saídas dos três métodos. Pelo critério aprovado, M1/M2
não receberam comparação forçada (0 comparações sustentadas); M3 foi validado
contra os 20 testes sanitizados e aprovados da ENG-005, sem divergência e com
`method_three_observed_frequency` `1.0.0` preservado.

A colisão P2 de sequência foi reproduzida como interação entre fixtures de
integração com IDs explícitos e importação no mesmo banco descartável. O
contorno de isolamento foi revalidado em banco novo: importação do XLSM aprovado
com 2.694 aceitos, zero rejeitados e zero warnings, seguida de remoção do banco
temporário; nenhum `setval`, schema ou dado permanente foi alterado.

O ensaio APP-018 foi concluído exclusivamente em bancos e diretórios
descartáveis. O backup oficial incluiu PostgreSQL, PDFs, metadados e configuração
operacional; o manifesto e os SHA-256 foram validados antes da restauração. A
API restaurada passou health/readiness, a credencial administrativa original foi
confirmada por entrada local oculta, e snapshot, PDF, hashes e auditoria foram
recuperados sem divergência. Os dois bancos, APIs, bundles, PDFs, configuração
temporária e resíduos `codex_task_*` foram removidos; PostgreSQL institucional
permaneceu em `127.0.0.1:55432` aceitando conexões.

| Métrica | Resultado |
| --- | --- |
| Jornadas técnicas / competições | 20 / 20; 5 / 5 |
| M1/M2, comparações legadas sustentadas | 0 / 20; 0 / 20 |
| M3, baselines ENG-005 | 20 / 20 PASS |
| Divergências de cálculo confirmadas | 0 |
| Recuperação APP-018 | PASS; autenticação, snapshot/PDF/hashes e auditoria restaurados |
| RPO / RTO | 106,231 s / 64,379 s |
| P0 / P1 / P2 / P3 abertos | 0 / 0 / 0 / 0 |
| QA independente | PASS |

Todos os critérios técnicos do protocolo foram atingidos, observada a limitação
aceita pelo Product Owner de que M1/M2 não possuem vínculo legado reproduzível.
A recomendação técnica é `APTO`; o Product Owner aprovou o cutover interno.
Isto não altera APP-012–018, contratos, versões ou matemática e não autoriza
atividade financeira, comercial, Value Tracker ou integração externa.

## Publicação e encerramento institucional

O commit técnico-documental `d0cd4ccd0c9ff2bf02168614844e0d59262293dc` foi
publicado pelo PR #50 e integrado em `main` pelo merge commit
`79880af721ace00e27f86557d6e058880823a69e`. O encerramento documental ocorre
nesta sequência autorizada, sem criar ou inferir task sucessora.
