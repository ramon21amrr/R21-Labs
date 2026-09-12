[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ApiEnvironmentPath,
    [Parameter(Mandatory)][string]$PdfArtifactsPath,
    [Parameter(Mandatory)][string]$StateDirectory,
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000,
    [switch]$ApiOnly,
    [switch]$SkipMigrations,
    [int]$ReadyTimeoutSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'LvfiLocal.Common.psm1') -Force
if ($ApiPort -lt 1 -or $ApiPort -gt 65535 -or $WebPort -lt 1 -or $WebPort -gt 65535) { throw 'Ports must be between 1 and 65535.' }
if ($ReadyTimeoutSeconds -lt 5 -or $ReadyTimeoutSeconds -gt 300) { throw 'ReadyTimeoutSeconds must be between 5 and 300.' }
$repositoryRoot = (git -C $PSScriptRoot rev-parse --show-toplevel 2>$null).Trim()
if (-not $repositoryRoot) { throw 'Start-Lvfi.ps1 must run from an LVFI Git checkout.' }
$apiRoot = Join-Path $repositoryRoot 'apps\api'
$webRoot = Join-Path $repositoryRoot 'apps\web'
$environmentFile = Resolve-LvfiLocalPath -Path $ApiEnvironmentPath -Label 'ApiEnvironmentPath'
if ((Get-Item -LiteralPath $environmentFile).PSIsContainer) { throw 'ApiEnvironmentPath must be a file.' }
$pdfRoot = Resolve-LvfiLocalPath -Path $PdfArtifactsPath -Label 'PdfArtifactsPath' -CreateDirectory
$state = Resolve-LvfiLocalPath -Path $StateDirectory -Label 'StateDirectory' -CreateDirectory
$stateFile = Join-Path $state 'lvfi-processes.json'
if (Test-Path -LiteralPath $stateFile) { throw 'LVFI process state already exists. Run Stop-Lvfi.ps1 or inspect the recorded processes before starting again.' }
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'uv was not found. Install the approved local toolchain and retry.' }
if (-not $ApiOnly -and -not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'npm was not found. Install the locked local web toolchain or use -ApiOnly.' }

function Write-LauncherFile {
    param([string]$Path, [string[]]$Lines)
    Set-Content -LiteralPath $Path -Value $Lines -Encoding ascii
}
function Start-LvfiChild {
    param([string]$LauncherPath, [string]$LogName)
    $stdout = Join-Path $state "$LogName.stdout.log"
    $stderr = Join-Path $state "$LogName.stderr.log"
    return Start-Process -FilePath $env:ComSpec -ArgumentList @('/d', '/c', $LauncherPath) -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
}

$apiLauncher = Join-Path $state 'run-api.cmd'
$migrationLauncher = Join-Path $state 'migrate-api.cmd'
$quotedApiRoot = '"' + $apiRoot.Replace('"', '""') + '"'
$quotedEnvironment = '"' + $environmentFile.Replace('"', '""') + '"'
Write-LauncherFile -Path $apiLauncher -Lines @(
    '@echo off', 'setlocal', ('for /f "usebackq tokens=1,* delims==" %%A in ({0}) do set "%%A=%%B"' -f $quotedEnvironment), ('set "LVFI_PDF_STORAGE_DIR={0}"' -f $pdfRoot), "cd /d $quotedApiRoot", "call uv run uvicorn lvfi_api.main:create_app --factory --host 127.0.0.1 --port $ApiPort"
)
Write-LauncherFile -Path $migrationLauncher -Lines @(
    '@echo off', 'setlocal', ('for /f "usebackq tokens=1,* delims==" %%A in ({0}) do set "%%A=%%B"' -f $quotedEnvironment), ('set "LVFI_PDF_STORAGE_DIR={0}"' -f $pdfRoot), "cd /d $quotedApiRoot", 'call uv run alembic upgrade head'
)
$started = @()
try {
    if (-not $SkipMigrations) {
        & $env:ComSpec /d /c $migrationLauncher
        if ($LASTEXITCODE -ne 0) { throw 'Database migration failed. The local application was not started.' }
    }
    $apiProcess = Start-LvfiChild -LauncherPath $apiLauncher -LogName 'api'
    $started += $apiProcess
    $webProcess = $null
    if (-not $ApiOnly) {
        $webLauncher = Join-Path $state 'run-web.cmd'
        Write-LauncherFile -Path $webLauncher -Lines @(
            '@echo off', 'setlocal', ('set "LVFI_API_URL=http://127.0.0.1:{0}"' -f $ApiPort), ('set "NEXT_PUBLIC_LVFI_API_URL=http://127.0.0.1:{0}"' -f $ApiPort), ('cd /d "{0}"' -f $webRoot), "call npm run dev -- --hostname 127.0.0.1 --port $WebPort"
        )
        $webProcess = Start-LvfiChild -LauncherPath $webLauncher -LogName 'web'
        $started += $webProcess
    }
    $deadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        try {
            & (Join-Path $PSScriptRoot 'Test-LvfiHealth.ps1') -ApiBaseUrl "http://127.0.0.1:$ApiPort" -TimeoutSeconds 5 | Out-Null
            $ready = $true
            break
        }
        catch { Start-Sleep -Seconds 1 }
    }
    if (-not $ready) { throw 'LVFI API did not become ready. Review the local logs without exposing configuration values.' }
    $processes = @($started | ForEach-Object { [ordered]@{ pid = $_.Id; started_at_unix_ms = ([DateTimeOffset]::new($_.StartTime.ToUniversalTime())).ToUnixTimeMilliseconds() } })
    [ordered]@{ schema = 'lvfi-local-processes/v1'; api_base_url = "http://127.0.0.1:$ApiPort"; web_url = if ($ApiOnly) { $null } else { "http://127.0.0.1:$WebPort" }; processes = $processes } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $stateFile -Encoding utf8NoBOM
    [pscustomobject]@{ api_url = "http://127.0.0.1:$ApiPort"; web_url = if ($ApiOnly) { $null } else { "http://127.0.0.1:$WebPort" }; state_file = $stateFile }
}
catch {
    foreach ($process in $started) { if (-not $process.HasExited) { & taskkill.exe /PID $process.Id /T /F | Out-Null } }
    throw
}
