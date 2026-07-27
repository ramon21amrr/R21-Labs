Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:CodexPostgres = [ordered]@{
    Host = '127.0.0.1'
    Port = 55432
    Role = 'codex_test'
    TaskName = 'R21CodexPostgres16'
    BinDirectory = 'C:\Program Files\PostgreSQL\16\bin'
    RootDirectory = 'C:\ProgramData\R21\CodexPostgres16'
    CredentialPath = 'C:\ProgramData\R21\CodexPostgres16\credentials\codex-test-role.xml'
}

function Get-CodexPostgresConfiguration {
    [OutputType([hashtable])]
    param()

    $copy = [ordered]@{}
    foreach ($entry in $script:CodexPostgres.GetEnumerator()) {
        $copy[$entry.Key] = $entry.Value
    }
    return $copy
}

function Assert-CodexPostgresTaskDatabaseName {
    param([Parameter(Mandatory)][string]$Database)

    if ($Database -notmatch '^codex_task_[a-z0-9_]{1,40}$') {
        throw 'Database must match ^codex_task_[a-z0-9_]{1,40}$.'
    }
}

function Get-CodexPostgresPassword {
    [OutputType([string])]
    param()

    $credentialPath = $script:CodexPostgres.CredentialPath
    if (-not (Test-Path -LiteralPath $credentialPath -PathType Leaf)) {
        throw "Codex PostgreSQL credential is unavailable at its protected local path. Run the approved installation script first."
    }

    $secure = Import-Clixml -LiteralPath $credentialPath
    if ($secure -isnot [System.Security.SecureString]) {
        throw 'The protected Codex PostgreSQL credential has an invalid format.'
    }

    $pointer = [IntPtr]::Zero
    try {
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    }
    finally {
        if ($pointer -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
        }
    }
}

function Invoke-WithCodexPostgresPassword {
    param([Parameter(Mandatory)][scriptblock]$Action)

    $previous = $env:PGPASSWORD
    $hadPrevious = Test-Path Env:PGPASSWORD
    $env:PGPASSWORD = Get-CodexPostgresPassword
    try {
        & $Action
    }
    finally {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
        if ($hadPrevious) {
            $env:PGPASSWORD = $previous
        }
    }
}

function Get-CodexPostgresExecutable {
    [OutputType([string])]
    param([Parameter(Mandatory)][ValidateSet('psql.exe', 'pg_isready.exe', 'createdb.exe', 'dropdb.exe')][string]$Name)

    $path = Join-Path $script:CodexPostgres.BinDirectory $Name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required PostgreSQL 16 executable is unavailable: $Name."
    }
    return $path
}

function Get-CodexPostgresConnectionString {
    [OutputType([string])]
    param([Parameter(Mandatory)][string]$Database)

    Assert-CodexPostgresTaskDatabaseName -Database $Database
    $password = [Uri]::EscapeDataString((Get-CodexPostgresPassword))
    return "postgresql+asyncpg://$($script:CodexPostgres.Role):$password@$($script:CodexPostgres.Host):$($script:CodexPostgres.Port)/$Database"
}

function Set-CodexPostgresLvfiTestEnvironment {
    param([Parameter(Mandatory)][string]$Database)

    return [ordered]@{
        LVFI_DATABASE_URL = Get-CodexPostgresConnectionString -Database $Database
        LVFI_ENVIRONMENT = 'test'
        LVFI_APP_NAME = 'lvfi-codex-postgres-test'
    }
}

function Invoke-WithCodexPostgresLvfiTestEnvironment {
    param(
        [Parameter(Mandatory)][string]$Database,
        [Parameter(Mandatory)][scriptblock]$Action
    )

    $values = Set-CodexPostgresLvfiTestEnvironment -Database $Database
    $previous = @{}
    foreach ($name in $values.Keys) {
        $previous[$name] = [ordered]@{
            Present = Test-Path "Env:$name"
            Value = [Environment]::GetEnvironmentVariable($name, 'Process')
        }
        Set-Item -Path "Env:$name" -Value $values[$name]
    }
    try {
        & $Action
    }
    finally {
        foreach ($name in $values.Keys) {
            Remove-Item -Path "Env:$name" -ErrorAction SilentlyContinue
            if ($previous[$name].Present) {
                Set-Item -Path "Env:$name" -Value $previous[$name].Value
            }
        }
    }
}
function Invoke-CodexPostgresPsql {
    [OutputType([int])]
    param(
        [Parameter(Mandatory)][string]$Database,
        [Parameter(Mandatory)][string]$Query,
        [switch]$AllowFailure,
        [switch]$SuppressOutput
    )

    $psql = Get-CodexPostgresExecutable -Name 'psql.exe'
    $arguments = @('-X', '-v', 'ON_ERROR_STOP=1', '-h', $script:CodexPostgres.Host, '-p', $script:CodexPostgres.Port, '-U', $script:CodexPostgres.Role, '-d', $Database, '-c', $Query)
    $result = Invoke-WithCodexPostgresPassword {
        if ($SuppressOutput) {
            & $psql @arguments 2>$null | Out-Null
            return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Rows = @() }
        }
        $rows = @(& $psql @arguments)
        return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Rows = $rows }
    }
    if (-not $SuppressOutput) {
        $result.Rows | Write-Output
    }
    if (-not $AllowFailure -and $result.ExitCode -ne 0) {
        throw "PostgreSQL command failed with exit code $($result.ExitCode)."
    }
    return [int]$result.ExitCode
}
function Test-CodexPostgresService {
    [OutputType([bool])]
    param()

    $ready = Get-CodexPostgresExecutable -Name 'pg_isready.exe'
    & $ready '-h' $script:CodexPostgres.Host '-p' $script:CodexPostgres.Port '-d' 'postgres' | Out-Null
    return $LASTEXITCODE -eq 0
}

function New-CodexPostgresTaskDatabase {
    param([Parameter(Mandatory)][string]$Database)

    Assert-CodexPostgresTaskDatabaseName -Database $Database
    if (-not (Test-CodexPostgresService)) {
        throw 'The Codex PostgreSQL test service is not ready on 127.0.0.1:55432.'
    }
    $createdb = Get-CodexPostgresExecutable -Name 'createdb.exe'
    Invoke-WithCodexPostgresPassword {
        & $createdb '-h' $script:CodexPostgres.Host '-p' $script:CodexPostgres.Port '-U' $script:CodexPostgres.Role '-T' 'template0' $Database
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to create isolated task database $Database."
        }
    }
}

function Stop-CodexPostgresTaskSessions {
    param([Parameter(Mandatory)][string]$Database)

    Assert-CodexPostgresTaskDatabaseName -Database $Database
    $query = "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$Database' AND pid <> pg_backend_pid();"
    [void](Invoke-CodexPostgresPsql -Database 'postgres' -Query $query -AllowFailure -SuppressOutput)
}

function Remove-CodexPostgresTaskDatabase {
    param([Parameter(Mandatory)][string]$Database)

    Assert-CodexPostgresTaskDatabaseName -Database $Database
    Stop-CodexPostgresTaskSessions -Database $Database
    $dropdb = Get-CodexPostgresExecutable -Name 'dropdb.exe'
    Invoke-WithCodexPostgresPassword {
        & $dropdb '--if-exists' '--force' '-h' $script:CodexPostgres.Host '-p' $script:CodexPostgres.Port '-U' $script:CodexPostgres.Role $Database
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to remove isolated task database $Database."
        }
    }
}

function Invoke-CodexPostgresMigration {
    param(
        [Parameter(Mandatory)][string]$Database,
        [Parameter(Mandatory)][ValidatePattern('^(head|base|[0-9]{8}_[0-9]{2})$')][string]$Target,
        [Parameter(Mandatory)][string]$ApiPath
    )

    Assert-CodexPostgresTaskDatabaseName -Database $Database
    Invoke-WithCodexPostgresLvfiTestEnvironment -Database $Database -Action {
        Push-Location -LiteralPath $ApiPath
        try {
            & uv run alembic upgrade $Target
            if ($LASTEXITCODE -ne 0) {
                throw "Alembic upgrade to $Target failed."
            }
        }
        finally {
            Pop-Location
        }
    }
}

function Invoke-CodexPostgresDowngrade {
    param(
        [Parameter(Mandatory)][string]$Database,
        [Parameter(Mandatory)][ValidatePattern('^(base|[0-9]{8}_[0-9]{2})$')][string]$Target,
        [Parameter(Mandatory)][string]$ApiPath
    )

    Assert-CodexPostgresTaskDatabaseName -Database $Database
    Invoke-WithCodexPostgresLvfiTestEnvironment -Database $Database -Action {
        Push-Location -LiteralPath $ApiPath
        try {
            & uv run alembic downgrade $Target
            if ($LASTEXITCODE -ne 0) {
                throw "Alembic downgrade to $Target failed."
            }
        }
        finally {
            Pop-Location
        }
    }
}

function Test-CodexPostgresNoTaskDatabases {
    [OutputType([bool])]
    param()

    $psql = Get-CodexPostgresExecutable -Name 'psql.exe'
    $arguments = @('-X', '-A', '-t', '-v', 'ON_ERROR_STOP=1', '-h', $script:CodexPostgres.Host, '-p', $script:CodexPostgres.Port, '-U', $script:CodexPostgres.Role, '-d', 'postgres', '-c', "SELECT datname FROM pg_database WHERE datname LIKE 'codex_task_%';")
    $result = Invoke-WithCodexPostgresPassword {
        $rows = @(& $psql @arguments 2>$null)
        [pscustomobject]@{ ExitCode = $LASTEXITCODE; Rows = $rows }
    }
    if ($result.ExitCode -ne 0) {
        throw 'Unable to inspect residual Codex task databases.'
    }
    return @($result.Rows | Where-Object { $_.Trim().Length -gt 0 }).Count -eq 0
}
Export-ModuleMember -Function @(
    'Get-CodexPostgresConfiguration',
    'Get-CodexPostgresConnectionString',
    'Invoke-WithCodexPostgresLvfiTestEnvironment',
    'Test-CodexPostgresNoTaskDatabases',
    'Invoke-CodexPostgresPsql',
    'Test-CodexPostgresService',
    'New-CodexPostgresTaskDatabase',
    'Stop-CodexPostgresTaskSessions',
    'Remove-CodexPostgresTaskDatabase',
    'Invoke-CodexPostgresMigration',
    'Invoke-CodexPostgresDowngrade'
)
