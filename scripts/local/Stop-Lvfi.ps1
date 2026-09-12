[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'Medium')]
param([Parameter(Mandatory)][string]$StateDirectory)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'LvfiLocal.Common.psm1') -Force
$state = Resolve-LvfiLocalPath -Path $StateDirectory -Label 'StateDirectory'
$stateFile = Join-Path $state 'lvfi-processes.json'
if (-not (Test-Path -LiteralPath $stateFile -PathType Leaf)) { throw 'No LVFI process state exists in StateDirectory.' }
$recordRaw = Get-Content -LiteralPath $stateFile -Raw
$record = $recordRaw | ConvertFrom-Json -AsHashtable
if ($record['schema'] -ne 'lvfi-local-processes/v1') { throw 'Unsupported LVFI process state schema.' }
foreach ($entry in @($record['processes'])) {
    $process = Get-Process -Id $entry['pid'] -ErrorAction SilentlyContinue
    if (-not $process) { continue }
    $actualStart = ([DateTimeOffset]::new($process.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds()
    if ($entry.ContainsKey('started_at_unix_ms')) {
        if ($actualStart -ne $entry['started_at_unix_ms']) { throw 'A recorded PID was reused; refusing to stop an unrelated process.' }
    }
    else {
        $legacy = [regex]::Match($recordRaw, '"pid"\s*:\s*' + [regex]::Escape([string]$entry['pid']) + '\s*,\s*"started_at_utc"\s*:\s*"([^"]+)"')
        if (-not $legacy.Success) { throw 'LVFI process state is missing its original start timestamp.' }
        $expectedStart = [DateTimeOffset]::ParseExact($legacy.Groups[1].Value, 'o', [Globalization.CultureInfo]::InvariantCulture).ToUnixTimeMilliseconds()
        if ($actualStart -ne $expectedStart) { throw 'A recorded PID was reused; refusing to stop an unrelated process.' }
    }
    if ($PSCmdlet.ShouldProcess("PID $($entry['pid'])", 'stop LVFI process tree')) {
        & taskkill.exe /PID $entry['pid'] /T /F | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'LVFI process stop failed. Inspect the local process state and logs.' }
    }
}
if ($PSCmdlet.ShouldProcess($stateFile, 'remove stopped LVFI process state')) { Remove-Item -LiteralPath $stateFile -Force }
[pscustomobject]@{ stopped = $true; api_url = $record['api_base_url'] }
