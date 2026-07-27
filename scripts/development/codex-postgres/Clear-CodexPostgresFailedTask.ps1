[CmdletBinding()]
param([Parameter(Mandatory)][string]$Database)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'CodexPostgresTest.psm1') -Force
Stop-CodexPostgresTaskSessions -Database $Database
Remove-CodexPostgresTaskDatabase -Database $Database
Write-Output "Cleaned failed isolated Codex task database: $Database"
