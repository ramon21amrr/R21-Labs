[CmdletBinding()]
param([Parameter(Mandatory)][string]$Database)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'CodexPostgresTest.psm1') -Force
New-CodexPostgresTaskDatabase -Database $Database
Write-Output "Created isolated Codex task database: $Database"
