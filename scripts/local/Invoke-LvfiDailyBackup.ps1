[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ApiEnvironmentPath,
    [Parameter(Mandatory)][string]$PdfArtifactsPath,
    [Parameter(Mandatory)][string]$BackupRoot,
    [Parameter(Mandatory)][string[]]$ActiveDataPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$environmentFile = (Resolve-Path -LiteralPath $ApiEnvironmentPath -ErrorAction Stop).Path
$databaseLine = Get-Content -LiteralPath $environmentFile | Where-Object { $_ -match '^\s*LVFI_DATABASE_URL\s*=' } | Select-Object -First 1
if (-not $databaseLine) { throw 'ApiEnvironmentPath does not contain LVFI_DATABASE_URL.' }
$databaseUrl = ($databaseLine -split '=', 2)[1].Trim()
if ([string]::IsNullOrWhiteSpace($databaseUrl)) { throw 'LVFI_DATABASE_URL is empty.' }
if ($databaseUrl.StartsWith('postgresql+asyncpg://', [StringComparison]::OrdinalIgnoreCase)) {
    $databaseUrl = 'postgresql://' + $databaseUrl.Substring('postgresql+asyncpg://'.Length)
}
& (Join-Path $PSScriptRoot 'Backup-Lvfi.ps1') -DatabaseUrl $databaseUrl -PdfArtifactsPath $PdfArtifactsPath -OperationalConfigPath $environmentFile -BackupRoot $BackupRoot -ActiveDataPath $ActiveDataPath
