[CmdletBinding()]
param([Parameter(Mandatory)][string]$Database)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'CodexPostgresTest.psm1') -Force
Remove-CodexPostgresTaskDatabase -Database $Database
Write-Output "Removed isolated Codex task database: $Database"
