[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'CodexPostgresTest.psm1') -Force

$configuration = Get-CodexPostgresConfiguration
$task = Get-ScheduledTask -TaskName $configuration.TaskName -ErrorAction SilentlyContinue
$ready = Test-CodexPostgresService
$credentialPresent = Test-Path -LiteralPath $configuration.CredentialPath -PathType Leaf
[ordered]@{
    task = $configuration.TaskName
    task_status = if ($null -eq $task) { 'absent' } else { $task.State.ToString() }
    endpoint = "$($configuration.Host):$($configuration.Port)"
    ready = $ready
    credential_present = $credentialPresent
} | ConvertTo-Json -Compress