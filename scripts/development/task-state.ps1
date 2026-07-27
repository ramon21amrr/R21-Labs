[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('start','update','show','complete')][string]$Action,
    [string]$TaskId, [string]$Stage, [string]$NextStep, [string]$BlockedStep
)
$ErrorActionPreference = 'Stop'
$root = (git rev-parse --show-toplevel).Trim(); $path = Join-Path $root '.r21-artifacts\task-state.json'; $branch = (git branch --show-current).Trim(); $head = (git rev-parse HEAD).Trim()
if ($Action -eq 'start') { if (-not $TaskId) { throw 'TaskId is required for start.' }; New-Item -ItemType Directory -Path (Split-Path $path) -Force | Out-Null; [ordered]@{task_id=$TaskId;branch=$branch;base_commit=$head;current_commit=$head;completed_stage='baseline';blocked_stage=$null;next_step=$NextStep;gates=@();temporary_resources=@();cleanup_pending=@();timestamp=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $path -Encoding utf8 }
if (-not (Test-Path -LiteralPath $path)) { throw 'Task state is absent. Start it first.' }
$state = Get-Content -Raw -LiteralPath $path | ConvertFrom-Json
if ($state.branch -ne $branch -or $state.current_commit -ne $head) { throw 'Task state is stale for the current branch or HEAD.' }
if ($Action -eq 'update') { if ($Stage) {$state.completed_stage=$Stage}; if ($NextStep) {$state.next_step=$NextStep}; if ($BlockedStep) {$state.blocked_stage=$BlockedStep}; $state.timestamp=(Get-Date).ToUniversalTime().ToString('o'); $state | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $path -Encoding utf8 }
if ($Action -eq 'complete') { Remove-Item -LiteralPath $path -Force }
if ($Action -ne 'complete') { Get-Content -Raw -LiteralPath $path }