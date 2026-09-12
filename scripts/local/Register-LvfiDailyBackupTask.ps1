[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'Medium')]
param(
    [Parameter(Mandatory)][datetime]$At,
    [Parameter(Mandatory)][string]$ApiEnvironmentPath,
    [Parameter(Mandatory)][string]$PdfArtifactsPath,
    [Parameter(Mandatory)][string]$BackupRoot,
    [Parameter(Mandatory)][string[]]$ActiveDataPath,
    [string]$TaskName = 'LVFI Daily Backup'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($TaskName)) { throw 'TaskName is required.' }
$scriptPath = Join-Path $PSScriptRoot 'Invoke-LvfiDailyBackup.ps1'
$arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$scriptPath`"", '-ApiEnvironmentPath', "`"$ApiEnvironmentPath`"", '-PdfArtifactsPath', "`"$PdfArtifactsPath`"", '-BackupRoot', "`"$BackupRoot`"")
foreach ($path in $ActiveDataPath) { $arguments += @('-ActiveDataPath', "`"$path`"") }
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ($arguments -join ' ')
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
if ($PSCmdlet.ShouldProcess($TaskName, 'register daily local LVFI backup task')) {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Description 'LVFI local backup: PostgreSQL, PDF artifacts and operational configuration.' -Force | Out-Null
}
[pscustomobject]@{ task_name = $TaskName; daily_at = $At.ToString('HH:mm'); backup_root = $BackupRoot }
