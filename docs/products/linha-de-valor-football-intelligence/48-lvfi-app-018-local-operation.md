# LVFI-APP-018 — Operação local, backup e recuperação

## Limite operacional

Esta capacidade é local e de um único administrador. Os scripts não iniciam
piloto, não publicam serviços, não acessam integrações externas e não reproduzem
nenhum cálculo do domínio. O diretório `LVFI_PDF_STORAGE_DIR` é fornecido ao
processo da API; os PDFs continuam pertencendo ao snapshot aprovado e aos seus
metadados persistidos.

Os endpoints existentes são `GET /health` (processo HTTP) e `GET /ready`
(PostgreSQL). O launcher só declara êxito quando ambos retornam os estados
esperados. Erros dos scripts não imprimem URL de banco, senha, conteúdo de
configuração ou token.

## Iniciar e parar no Windows

Prepare um arquivo de ambiente local, fora do Git, que contenha a configuração
da API, inclusive `LVFI_DATABASE_URL`. Escolha também diretórios locais para
artefatos PDF e estado do launcher. O estado guarda somente PIDs, URLs locais e
logs de processo; não guarda segredos.

```powershell
$apiEnv = 'C:\LVFI\config\api.env'
$pdfs = 'C:\LVFI\data\pdfs'
$state = 'C:\LVFI\runtime'
.\scripts\local\Start-Lvfi.ps1 -ApiEnvironmentPath $apiEnv -PdfArtifactsPath $pdfs -StateDirectory $state
.\scripts\local\Test-LvfiHealth.ps1 -ApiBaseUrl 'http://127.0.0.1:8000'
.\scripts\local\Stop-Lvfi.ps1 -StateDirectory $state -Confirm:$false
```

`Start-Lvfi.ps1` aplica as migrations antes de iniciar a API, salvo quando a
opção explícita `-SkipMigrations` é usada para um ensaio já migrado. Ele inicia
web e API; `-ApiOnly` é destinado ao ensaio operacional. O stop valida o instante
de criação do PID antes de usar `taskkill /T`, impedindo que um PID reutilizado
encerre um processo não relacionado.

Antes de migration ou upgrade relevante, execute o backup manual abaixo e só
prossiga após receber o caminho do bundle e seu hash de manifesto.

## Backup diário e retenção

O backup contém dump PostgreSQL em formato custom, a árvore de PDFs (incluindo
metadados armazenados junto aos artefatos) e a configuração operacional indicada.
Cada bundle é publicado de uma área de staging apenas depois de concluído e tem
`manifest.json`, `manifest.sha256` e SHA-256 de cada arquivo. Os bundles são
append-only; a poda só remove bundles íntegros reconhecidos pelo manifesto e que
não pertençam a nenhuma classe retida.

O destino deve estar fora de **todos** os diretórios de dados ativos. Declare os
diretórios ativos explicitamente; não use o diretório de dados PostgreSQL nem o
de PDFs como destino de backup.

```powershell
$active = @('C:\LVFI\data', 'C:\LVFI\config', 'C:\LVFI\runtime')
$backups = 'D:\LVFI-backups'
.\scripts\local\Invoke-LvfiDailyBackup.ps1 -ApiEnvironmentPath $apiEnv -PdfArtifactsPath $pdfs -BackupRoot $backups -ActiveDataPath $active
.\scripts\local\Register-LvfiDailyBackupTask.ps1 -At '02:00' -ApiEnvironmentPath $apiEnv -PdfArtifactsPath $pdfs -BackupRoot $backups -ActiveDataPath $active
```

A execução diária recebe sempre a classe `daily`; a de domingo também recebe
`weekly` e a do primeiro dia do mês também recebe `monthly`. A retenção mantém
14 diários, 8 semanais e 6 mensais, preservando um bundle enquanto ele pertence
a pelo menos uma dessas janelas. Caches, logs, builds e sessões são excluídos
mesmo se existirem sob uma fonte indicada. O agendamento não inclui a URL de
banco em sua linha de comando: ela
é lida do arquivo operacional no momento da execução.

## Restauração e ensaio obrigatório

Use sempre destinos de ensaio isolados, valide o manifesto antes de alterar
qualquer destino e informe `-Force` conscientemente. A restauração exige a
confirmação padrão do PowerShell; `-Confirm:$false` é apropriado apenas em um
ensaio automatizado para recursos isolados. `pg_restore --clean --if-exists`
substitui o banco alvo, e `-ReplacePdfArtifacts` substitui a árvore PDF alvo.

```powershell
$bundle = 'D:\LVFI-backups\lvfi-YYYYMMDDTHHMMSSZ-xxxxxxxxxxxx'
$restoreRoot = 'C:\LVFI-rehearsal'
.\scripts\local\Restore-Lvfi.ps1 -BackupPath $bundle -RestoreRoot $restoreRoot -TargetDatabaseUrl 'postgresql://.../lvfi_rehearsal' -TargetPdfArtifactsPath 'C:\LVFI-rehearsal\pdfs' -TargetOperationalConfigPath 'C:\LVFI-rehearsal\config\api.env' -RestoreOperationalConfig -ReplacePdfArtifacts -Force
```

O ensaio completo é, nesta ordem:

1. Criar banco, PDFs, configuração e state directory de ensaio isolados.
2. Restaurar banco, PDFs e configuração com o comando acima; o script verifica
   SHA-256 do manifesto e de todos os arquivos antes da escrita.
3. Preservar a configuração restaurada para validação de hash e subir a aplicação
   com um arquivo de ambiente de overlay, fora do bundle, apontado ao banco de
   ensaio; executar health/readiness e autenticar o administrador local.
4. Consultar um snapshot aprovado e a lista de PDFs, baixar o primeiro artefato
   e registrar o ID, SHA-256 de metadados e tamanho retornados.

```powershell
$secret = Read-Host 'Senha do administrador de ensaio' -AsSecureString
.\scripts\local\Test-LvfiRecovery.ps1 -ApiBaseUrl 'http://127.0.0.1:8000' -SnapshotId '<snapshot-aprovado>' -AdminPassword $secret
```

5. Parar a aplicação e remover exclusivamente o banco, diretórios e state
   directory do ensaio. Não remova o bundle de origem.

O objetivo contratado é RPO de 24 horas, atendido pelo agendamento diário, e
RTO de até duas horas, medido do início da restauração validada até o retorno do
check final. Registre horários de início e fim do ensaio junto ao bundle; os
scripts não declaram RTO como atingido sem essa medição real.
