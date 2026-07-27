# Ambiente PostgreSQL persistente de testes do Codex

## Arquitetura

R21-DEV-002 mantém um PostgreSQL 16 isolado para bancos descartáveis de tasks do
Codex. Ele não recebe dados de produto, não cria `connection.json` e não altera a
instância permanente em `127.0.0.1:5432`.

| Componente | Limite aplicado |
| --- | --- |
| Tarefa agendada | `R21CodexPostgres16`, executada como o usuário atual do Codex, iniciada no logon e com até três reinícios |
| Processo | `postgres.exe` do PostgreSQL 16; arquivos e processo pertencem ao usuário do Codex |
| Cluster | `C:\ProgramData\R21\CodexPostgres16\data`, fora do repositório e de `C:\tmp` |
| Rede | somente `127.0.0.1:55432`; IPv6 e demais endereços são rejeitados |
| Role normal | `codex_test`: `NOSUPERUSER`, `NOCREATEROLE`, `CREATEDB`, `NOREPLICATION`, `NOBYPASSRLS` |
| Segredos | DPAPI por usuário em diretório protegido fora do Git; nunca em terminal, logs, Graphify ou contexto |

O processo usa a conta Windows do Codex para que os arquivos do cluster e o
processo tenham o mesmo dono. Portanto, após reiniciar o Windows, o ambiente
inicia automaticamente no logon dessa conta; a recuperação da tarefa reinicia o
processo até três vezes. A porta `5432`, seus arquivos e sua credencial não fazem
parte desse fluxo.

As ACLs são construídas por SID: usuário atual via `WindowsIdentity.GetCurrent().User`,
SYSTEM (`S-1-5-18`) e Administrators (`S-1-5-32-544`). Não há `Everyone`,
`Users`, `Authenticated Users` nem principal AppContainer não verificado. A
configuração local do projeto do Codex permite apenas a raiz protegida da
credencial, sem rede e sem acesso de escrita ao cluster, binários ou à instância
em `5432`.

## Instalação única

O instalador elevado é idempotente. Ele verifica PostgreSQL 16, identidades e ACLs
antes de alterá-las; inicializa apenas um diretório vazio; recusa tarefa ou serviço
homônimo apontando para outro cluster; preserva o cluster válido em novas execuções.
Ele cria a tarefa agendada, limita `postgresql.conf` e `pg_hba.conf`, e cria ou
reconcilia a role normal. A senha administrativa é usada somente durante bootstrap
ou rotação e não é disponível aos scripts normais.

```powershell
scripts/development/codex-postgres/Install-CodexPostgresTestEnvironment.ps1
```

Execute esse comando uma única vez em PowerShell como Administrador. Não execute
`initdb`, `pg_ctl`, `sc.exe` nem modifique a instância de `5432` manualmente.
Abra uma nova sessão do Codex depois da instalação para carregar a configuração do
projeto e rode a validação abaixo.

## Uso automático em tasks

Use exclusivamente nomes `codex_task_<id_em_minúsculas>`. Os scripts recusam
qualquer outro nome e a conexão é montada apenas na memória do processo.

```powershell
$database = 'codex_task_r21_dev_999'
scripts/development/codex-postgres/New-CodexPostgresTaskDatabase.ps1 -Database $database
scripts/development/codex-postgres/Invoke-CodexPostgresTask.ps1 -Database $database -RunTests
scripts/development/codex-postgres/Remove-CodexPostgresTaskDatabase.ps1 -Database $database
```

`Invoke-CodexPostgresTask.ps1` fornece `LVFI_DATABASE_URL`, `LVFI_ENVIRONMENT`
e `LVFI_APP_NAME` somente ao processo de Alembic. A suíte de API recebe apenas a
URL efêmera, preservando seus testes de configuração. Para rollback explícito, use
`-DowngradeTo 20260724_01`; para falha, use
`Clear-CodexPostgresFailedTask.ps1 -Database $database`, que encerra sessões e
remove apenas o banco já validado.

O fluxo normal é: criar banco isolado → migrations e testes → validar → remover
banco → preservar o cluster. Não use role administrativa em uma task normal.

## Validação e diagnóstico

Em nova sessão do Codex e worktree confiável, execute:

```powershell
scripts/development/codex-postgres/Test-CodexPostgresTestEnvironment.ps1
```

O validador comprova binários, loopback `55432`, criação sem administração,
upgrade até `head`, SQL, downgrade controlado, retorno a `head`, testes da API,
proibição de criar role, negação na porta `5432`, remoção e ausência de bancos
`codex_task_*` residuais. Ele não imprime a senha nem a URL.

Para status sem segredo:

```powershell
scripts/development/codex-postgres/Get-CodexPostgresTestEnvironment.ps1
```

Se não estiver pronto após um reinício, confirme o logon do usuário do Codex e o
estado da tarefa `R21CodexPostgres16`. Não converta a tarefa em serviço sob outra
conta e não use a credencial administrativa para diagnóstico normal.

## Rotação e desinstalação

Para rotacionar somente a credencial da role normal, execute o instalador elevado
com `-RotateCodexCredential`. Isso mantém cluster, tarefa e dados; substitui apenas
a credencial DPAPI protegida e a senha da role. Se o arquivo administrativo estiver
ausente ou corrompido, restaure o cluster isolado ou faça remoção e instalação
limpas; não relaxe o `pg_hba.conf`.

A remoção exige elevação e intenção explícita:

```powershell
scripts/development/codex-postgres/Uninstall-CodexPostgresTestEnvironment.ps1 -RemoveClusterData -Confirm:$false
```

O script somente remove a tarefa ou serviço legado quando o comando aponta para o
diretório R21 exato e só remove `C:\ProgramData\R21\CodexPostgres16`. A instância
permanente em `5432` fica intocada.

## Prompt curto opcional

```text
Use o ambiente PostgreSQL persistente do Codex: crie codex_task_<task>, execute migrations/testes, valide e remova o banco. Não crie cluster, connection.json ou .env e não use a porta 5432.
```
