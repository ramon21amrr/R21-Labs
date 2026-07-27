[CmdletBinding()]
param(
    [string]$ApiPath = (Join-Path $PSScriptRoot '..\..\..\apps\api'),
    [switch]$SkipApiTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'CodexPostgresTest.psm1') -Force

function Test-Port5432Blocked {
    $credentialPath = 'C:\ProgramData\R21\CodexPostgres16\credentials\codex-test-role.xml'
    $secure = Import-Clixml -LiteralPath $credentialPath
    $pointer = [IntPtr]::Zero
    try {
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        $previous = $env:PGPASSWORD
        $hadPrevious = Test-Path Env:PGPASSWORD
        $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
        try {
            & 'C:\Program Files\PostgreSQL\16\bin\psql.exe' '-X' '-v' 'ON_ERROR_STOP=1' '-h' '127.0.0.1' '-p' '5432' '-U' 'codex_test' '-d' 'postgres' '-c' 'SELECT 1;' 2>$null | Out-Null
            return $LASTEXITCODE -ne 0
        }
        finally {
            Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
            if ($hadPrevious) { $env:PGPASSWORD = $previous }
        }
    }
    finally {
        if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    }
}

$database = "codex_task_validation_$([Guid]::NewGuid().ToString('N').Substring(0, 12))"
$resolvedApiPath = (Resolve-Path -LiteralPath $ApiPath).Path
$created = $false
try {
    if (-not (Test-CodexPostgresService)) { throw 'Codex PostgreSQL service is not ready on 127.0.0.1:55432.' }
    New-CodexPostgresTaskDatabase -Database $database
    $created = $true
    Invoke-CodexPostgresMigration -Database $database -Target 'head' -ApiPath $resolvedApiPath
    [void](Invoke-CodexPostgresPsql -Database $database -Query 'SELECT current_database(), current_user;')
    Invoke-CodexPostgresDowngrade -Database $database -Target '20260724_01' -ApiPath $resolvedApiPath
    Invoke-CodexPostgresMigration -Database $database -Target 'head' -ApiPath $resolvedApiPath
    $roleCreationExitCode = Invoke-CodexPostgresPsql -Database $database -Query 'CREATE ROLE codex_must_not_create_roles;' -AllowFailure -SuppressOutput
    if ($roleCreationExitCode -eq 0) { throw 'The Codex test role unexpectedly created a PostgreSQL role.' }
    if (-not (Test-Port5432Blocked)) { throw 'The Codex test credential unexpectedly accessed PostgreSQL on port 5432.' }
    if (-not $SkipApiTests) {
        $previous = $env:LVFI_DATABASE_URL
        $hadPrevious = Test-Path Env:LVFI_DATABASE_URL
        $env:LVFI_DATABASE_URL = Get-CodexPostgresConnectionString -Database $database
        try {
            Push-Location -LiteralPath $resolvedApiPath
            try {
                & uv run pytest -q
                if ($LASTEXITCODE -ne 0) { throw 'API test suite failed against the isolated Codex task database.' }
            }
            finally { Pop-Location }
        }
        finally {
            Remove-Item Env:LVFI_DATABASE_URL -ErrorAction SilentlyContinue
            if ($hadPrevious) { $env:LVFI_DATABASE_URL = $previous }
        }
    }
}
finally {
    if ($created) { Remove-CodexPostgresTaskDatabase -Database $database }
}
if (-not (Test-CodexPostgresNoTaskDatabases)) { throw 'Residual Codex task databases remain after validation.' }
Write-Output 'Codex PostgreSQL validation passed: loopback 55432, migrations, rollback, role limits, port isolation, and cleanup.'
