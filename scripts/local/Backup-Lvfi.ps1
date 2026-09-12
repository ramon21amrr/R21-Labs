[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$DatabaseUrl,
    [Parameter(Mandatory)][string]$PdfArtifactsPath,
    [Parameter(Mandatory)][string]$OperationalConfigPath,
    [Parameter(Mandatory)][string]$BackupRoot,
    [Parameter(Mandatory)][string[]]$ActiveDataPath,
    [datetime]$BackupTimestamp = (Get-Date).ToUniversalTime(),
    [switch]$NoPrune
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'LvfiLocal.Common.psm1') -Force
if ($DatabaseUrl.StartsWith('postgresql+asyncpg://', [StringComparison]::OrdinalIgnoreCase)) {
    $DatabaseUrl = 'postgresql://' + $DatabaseUrl.Substring('postgresql+asyncpg://'.Length)
}

function Get-RetentionClasses {
    param([datetime]$Timestamp)
    $classes = @('daily')
    if ($Timestamp.DayOfWeek -eq [DayOfWeek]::Sunday) { $classes += 'weekly' }
    if ($Timestamp.Day -eq 1) { $classes += 'monthly' }
    return $classes
}

function Remove-ExpiredLvfiBackups {
    param([string]$Root)
    $limits = @{ daily = 14; weekly = 8; monthly = 6 }
    $bundles = @()
    Get-ChildItem -LiteralPath $Root -Directory | ForEach-Object {
        $manifestPath = Join-Path $_.FullName 'manifest.json'
        if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { return }
        try {
            $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
            if ($manifest.schema -ne 'lvfi-local-backup/v1' -or -not $manifest.created_at -or -not $manifest.retention_classes) { return }
            $bundles += [pscustomobject]@{ Path = $_.FullName; CreatedAt = [datetime]::Parse($manifest.created_at).ToUniversalTime(); Classes = @($manifest.retention_classes) }
        }
        catch { return }
    }
    $retain = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($class in $limits.Keys) {
        @($bundles | Where-Object { $_.Classes -contains $class } | Sort-Object CreatedAt -Descending | Select-Object -First $limits[$class]) | ForEach-Object { [void]$retain.Add($_.Path) }
    }
    @($bundles | Where-Object { -not $retain.Contains($_.Path) }) | ForEach-Object {
        Remove-Item -LiteralPath $_.Path -Recurse -Force
    }
}

$pdfRoot = Resolve-LvfiLocalPath -Path $PdfArtifactsPath -Label 'PdfArtifactsPath'
$configuration = Resolve-LvfiLocalPath -Path $OperationalConfigPath -Label 'OperationalConfigPath'
$root = Resolve-LvfiLocalPath -Path $BackupRoot -Label 'BackupRoot' -CreateDirectory
$activePaths = @($ActiveDataPath | ForEach-Object { Resolve-LvfiLocalPath -Path $_ -Label 'ActiveDataPath' })
Assert-LvfiLocalOutsidePaths -Candidate $root -ActiveDataPath $activePaths

$pgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
if (-not $pgDump) { throw 'PostgreSQL client pg_dump was not found. Install the approved PostgreSQL client and retry.' }
$timestamp = $BackupTimestamp.ToUniversalTime()
$classes = Get-RetentionClasses -Timestamp $timestamp
$configurationIsDirectory = (Get-Item -LiteralPath $configuration).PSIsContainer
$configurationMetadata = if ($configurationIsDirectory) {
    [ordered]@{ kind = 'directory'; name = $null }
}
else {
    [ordered]@{ kind = 'file'; name = (Split-Path $configuration -Leaf) }
}
$bundleName = 'lvfi-{0:yyyyMMddTHHmmssZ}-{1}' -f $timestamp, ([guid]::NewGuid().ToString('N').Substring(0, 12))
$staging = Join-Path $root ('.staging-' + $bundleName)
$bundle = Join-Path $root $bundleName

try {
    New-Item -ItemType Directory -Path $staging -ErrorAction Stop | Out-Null
    $databaseDirectory = Join-Path $staging 'database'
    $pdfDirectory = Join-Path $staging 'pdf-artifacts'
    $configurationDirectory = Join-Path $staging 'operational-config'
    New-Item -ItemType Directory -Path $databaseDirectory, $pdfDirectory, $configurationDirectory | Out-Null
    $databaseDump = Join-Path $databaseDirectory 'postgresql.dump'
    $connection = [uri]$DatabaseUrl
    if ([string]::IsNullOrWhiteSpace($connection.UserInfo)) { throw 'Database URL must contain local PostgreSQL credentials.' }
    $connectionParts = $connection.UserInfo.Split(':', 2)
    if ($connectionParts.Count -ne 2) { throw 'Database URL must contain a local PostgreSQL password.' }
    $port = if ($connection.IsDefaultPort) { 5432 } else { $connection.Port }
    $previousPgPassword = $env:PGPASSWORD
    try {
        $env:PGPASSWORD = [uri]::UnescapeDataString($connectionParts[1])
        & $pgDump.Source '--format=custom' '--no-owner' '--no-privileges' "--file=$databaseDump" "--host=$($connection.Host)" "--port=$port" "--username=$([uri]::UnescapeDataString($connectionParts[0]))" "--dbname=$($connection.AbsolutePath.TrimStart('/'))"
        if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL backup failed. Database connection details were not written to output.' }
    }
    finally { $env:PGPASSWORD = $previousPgPassword }
    Copy-LvfiLocalRecoveryContent -Source $pdfRoot -Destination $pdfDirectory
    if ($configurationIsDirectory) {
        Copy-LvfiLocalRecoveryContent -Source $configuration -Destination $configurationDirectory
    }
    else {
        Copy-Item -LiteralPath $configuration -Destination (Join-Path $configurationDirectory (Split-Path $configuration -Leaf)) -Force
    }
    $files = Get-LvfiLocalFileManifestEntries -Root $staging
    $manifest = [ordered]@{
        schema = 'lvfi-local-backup/v1'
        created_at = $timestamp.ToString('o')
        retention_classes = $classes
        database_format = 'pg_dump_custom'
        operational_config = $configurationMetadata
        files = $files
    }
    $manifestPath = Join-Path $staging 'manifest.json'
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM
    $manifestHash = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath (Join-Path $staging 'manifest.sha256') -Value "$manifestHash  manifest.json" -Encoding ascii
    Rename-Item -LiteralPath $staging -NewName $bundleName -ErrorAction Stop
    if (-not $NoPrune) { Remove-ExpiredLvfiBackups -Root $root }
    [pscustomobject]@{ backup_path = $bundle; retention_classes = $classes; manifest_sha256 = $manifestHash }
}
catch {
    if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
    throw
}
