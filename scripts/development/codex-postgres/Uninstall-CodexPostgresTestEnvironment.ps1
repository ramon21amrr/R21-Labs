[CmdletBinding(SupportsShouldProcess)]
param([Parameter(Mandatory)][switch]$RemoveClusterData)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$taskName = 'R21CodexPostgres16'
$rootDirectory = 'C:\ProgramData\R21\CodexPostgres16'
$dataDirectory = Join-Path $rootDirectory 'data'
$postgres = 'C:\Program Files\PostgreSQL\16\bin\postgres.exe'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run this script from an elevated Administrator PowerShell session.' }
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($null -ne $task) {
    $action = $task.Actions | Select-Object -First 1
    if ($null -eq $action -or $action.Execute -ne $postgres -or $action.Arguments -notlike "*$dataDirectory*") { throw 'The task name exists but does not point to the isolated R21 Codex cluster; refuse to remove it.' }
    if ($task.State -eq 'Running') { Stop-ScheduledTask -TaskName $taskName }
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}
$legacyService = Get-CimInstance Win32_Service -Filter "Name='$taskName'" -ErrorAction SilentlyContinue
if ($null -ne $legacyService) {
    if ($legacyService.PathName -notlike "*$dataDirectory*") { throw 'The legacy service name exists but does not point to the isolated R21 Codex cluster; refuse to remove it.' }
    if ((Get-Service -Name $taskName).Status -ne 'Stopped') { Stop-Service -Name $taskName -Force }
    & sc.exe delete $taskName | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Unable to remove the legacy PostgreSQL service.' }
}
if ($PSCmdlet.ShouldProcess($rootDirectory, 'Remove the isolated Codex PostgreSQL cluster and protected credentials')) {
    if (Test-Path -LiteralPath $rootDirectory) { Remove-Item -LiteralPath $rootDirectory -Recurse -Force }
}
Write-Output 'Removed the R21 Codex PostgreSQL test environment; the permanent PostgreSQL service on port 5432 was not changed.'