[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory)][string]$BackupPath,
    [Parameter(Mandatory)][string]$TargetDatabaseUrl,
    [Parameter(Mandatory)][string]$RestoreRoot,
    [Parameter(Mandatory)][string]$TargetPdfArtifactsPath,
    [string]$TargetOperationalConfigPath,
    [switch]$RestoreOperationalConfig,
    [switch]$ReplacePdfArtifacts,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'LvfiLocal.Common.psm1') -Force

if (-not $Force) { throw 'Restore requires -Force after reviewing the target paths.' }
if ($RestoreOperationalConfig -and [string]::IsNullOrWhiteSpace($TargetOperationalConfigPath)) { throw 'TargetOperationalConfigPath is required with -RestoreOperationalConfig.' }
$backup = Resolve-LvfiLocalPath -Path $BackupPath -Label 'BackupPath'
$restoreRoot = Resolve-LvfiLocalPath -Path $RestoreRoot -Label 'RestoreRoot'
$manifest = Test-LvfiLocalManifest -BackupPath $backup
$pgRestore = Get-Command pg_restore -ErrorAction SilentlyContinue
if (-not $pgRestore) { throw 'PostgreSQL client pg_restore was not found. Install the approved PostgreSQL client and retry.' }
$dumpPath = Join-LvfiLocalSafePath -Root $backup -RelativePath 'database/postgresql.dump'
if (-not (Test-Path -LiteralPath $dumpPath -PathType Leaf)) { throw 'Backup does not contain the PostgreSQL dump.' }
$pdfSource = Join-LvfiLocalSafePath -Root $backup -RelativePath 'pdf-artifacts'
if (-not (Test-Path -LiteralPath $pdfSource -PathType Container)) { throw 'Backup does not contain PDF artifacts.' }
$targetPdf = [IO.Path]::GetFullPath($TargetPdfArtifactsPath)
Assert-LvfiLocalRestoreTarget -RestoreRoot $restoreRoot -Candidate $targetPdf -BackupPath $backup -Label 'TargetPdfArtifactsPath'
$configurationSource = Join-LvfiLocalSafePath -Root $backup -RelativePath 'operational-config'
if ($RestoreOperationalConfig) { Assert-LvfiLocalRestoreTarget -RestoreRoot $restoreRoot -Candidate $TargetOperationalConfigPath -BackupPath $backup -Label 'TargetOperationalConfigPath' }

function Invoke-LvfiPgRestore {
    param([string]$Executable, [string]$ConnectionUrl, [string]$Dump)
    $connection = [uri]$ConnectionUrl
    if ([string]::IsNullOrWhiteSpace($connection.UserInfo)) { throw 'Target database URL must contain local PostgreSQL credentials.' }
    $connectionParts = $connection.UserInfo.Split(':', 2)
    if ($connectionParts.Count -ne 2) { throw 'Target database URL must contain a local PostgreSQL password.' }
    $port = if ($connection.IsDefaultPort) { 5432 } else { $connection.Port }
    $previousPgPassword = $env:PGPASSWORD
    try {
        $env:PGPASSWORD = [uri]::UnescapeDataString($connectionParts[1])
        & $Executable '--clean' '--if-exists' '--no-owner' '--no-privileges' '--exit-on-error' "--host=$($connection.Host)" "--port=$port" "--username=$([uri]::UnescapeDataString($connectionParts[0]))" "--dbname=$($connection.AbsolutePath.TrimStart('/'))" $Dump
        if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL restore failed. Database connection details were not written to output.' }
    }
    finally { $env:PGPASSWORD = $previousPgPassword }
}

if ($PSCmdlet.ShouldProcess('target PostgreSQL database', 'replace from validated LVFI backup')) {
    Invoke-LvfiPgRestore -Executable $pgRestore.Source -ConnectionUrl $TargetDatabaseUrl -Dump $dumpPath
}
if ($ReplacePdfArtifacts) {
    if ($PSCmdlet.ShouldProcess($targetPdf, 'replace PDF artifacts from validated LVFI backup')) {
        if (Test-Path -LiteralPath $targetPdf) { Remove-Item -LiteralPath $targetPdf -Recurse -Force }
        New-Item -ItemType Directory -Path $targetPdf -Force | Out-Null
        Get-ChildItem -LiteralPath $pdfSource -Force | Copy-Item -Destination $targetPdf -Recurse -Force
    }
}
if ($RestoreOperationalConfig) {
    $targetConfiguration = [IO.Path]::GetFullPath($TargetOperationalConfigPath)
    if ($PSCmdlet.ShouldProcess($targetConfiguration, 'replace operational configuration from validated LVFI backup')) {
        if ($manifest.operational_config.kind -eq 'file') {
            if (Test-Path -LiteralPath $targetConfiguration -PathType Container) { throw 'TargetOperationalConfigPath is a directory, but the backup contains a configuration file.' }
            New-Item -ItemType Directory -Path (Split-Path $targetConfiguration -Parent) -Force | Out-Null
            Copy-Item -LiteralPath (Join-LvfiLocalSafePath -Root $backup -RelativePath ("operational-config/" + $manifest.operational_config.name)) -Destination $targetConfiguration -Force
        }
        elseif ($manifest.operational_config.kind -eq 'directory') {
            if (Test-Path -LiteralPath $targetConfiguration) { Remove-Item -LiteralPath $targetConfiguration -Recurse -Force }
            New-Item -ItemType Directory -Path $targetConfiguration -Force | Out-Null
            Get-ChildItem -LiteralPath $configurationSource -Force | Copy-Item -Destination $targetConfiguration -Recurse -Force
        }
        else { throw 'Backup operational configuration metadata is invalid.' }
    }
}
[pscustomobject]@{ restored_backup = $backup; manifest_sha256 = (Get-FileHash -LiteralPath (Join-Path $backup 'manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant(); pdf_artifacts_replaced = [bool]$ReplacePdfArtifacts; operational_config_restored = [bool]$RestoreOperationalConfig }
