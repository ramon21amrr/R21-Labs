[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Database,
    [string]$ApiPath = (Join-Path $PSScriptRoot '..\..\..\apps\api'),
    [ValidateSet('head', 'base', '20260724_01', '20260727_02')][string]$UpgradeTo = 'head',
    [ValidateSet('base', '20260724_01')][string]$DowngradeTo,
    [switch]$RunTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'CodexPostgresTest.psm1') -Force
$resolvedApiPath = (Resolve-Path -LiteralPath $ApiPath).Path

Invoke-CodexPostgresMigration -Database $Database -Target $UpgradeTo -ApiPath $resolvedApiPath
if ($DowngradeTo) {
    Invoke-CodexPostgresDowngrade -Database $Database -Target $DowngradeTo -ApiPath $resolvedApiPath
}
if ($RunTests) {
    $previous = $env:LVFI_DATABASE_URL
    $hadPrevious = Test-Path Env:LVFI_DATABASE_URL
    $env:LVFI_DATABASE_URL = Get-CodexPostgresConnectionString -Database $Database
    try {
        Push-Location -LiteralPath $resolvedApiPath
        try {
            & uv run pytest -q
            if ($LASTEXITCODE -ne 0) { throw 'API tests failed against the isolated Codex task database.' }
        }
        finally { Pop-Location }
    }
    finally {
        Remove-Item Env:LVFI_DATABASE_URL -ErrorAction SilentlyContinue
        if ($hadPrevious) { $env:LVFI_DATABASE_URL = $previous }
    }
}
Write-Output "Completed Codex PostgreSQL task execution for: $Database"
