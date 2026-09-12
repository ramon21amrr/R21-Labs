[CmdletBinding()]
param(
    [Parameter(Mandatory)][uri]$ApiBaseUrl,
    [int]$TimeoutSeconds = 10
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($TimeoutSeconds -lt 1 -or $TimeoutSeconds -gt 60) { throw 'TimeoutSeconds must be between 1 and 60.' }
$base = $ApiBaseUrl.AbsoluteUri.TrimEnd('/')
function Invoke-LvfiProbe {
    param([string]$Path)
    try {
        $response = Invoke-WebRequest -Uri "$base$Path" -UseBasicParsing -TimeoutSec $TimeoutSeconds
    }
    catch {
        throw "LVFI $Path probe failed. Confirm that the local application is running and review its local logs."
    }
    if ($response.StatusCode -ne 200) { throw "LVFI $Path probe returned an unexpected HTTP status." }
    try { $body = $response.Content | ConvertFrom-Json } catch { throw "LVFI $Path probe returned invalid JSON." }
    return $body
}
$health = Invoke-LvfiProbe -Path '/health'
if ($health.status -ne 'ok') { throw 'LVFI health response was not ok.' }
$ready = Invoke-LvfiProbe -Path '/ready'
if ($ready.status -ne 'ready') { throw 'LVFI readiness response was not ready.' }
[pscustomobject]@{ health = $health.status; readiness = $ready.status; version = $ready.version }
