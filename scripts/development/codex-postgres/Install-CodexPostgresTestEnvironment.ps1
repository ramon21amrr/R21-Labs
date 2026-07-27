[CmdletBinding()]
param(
    [switch]$RotateCodexCredential
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$taskName = 'R21CodexPostgres16'
$displayName = 'R21 Codex PostgreSQL 16 Test'
$hostAddress = '127.0.0.1'
$port = 55432
$role = 'codex_test'
$binDirectory = 'C:\Program Files\PostgreSQL\16\bin'
$rootDirectory = 'C:\ProgramData\R21\CodexPostgres16'
$dataDirectory = Join-Path $rootDirectory 'data'
$credentialDirectory = Join-Path $rootDirectory 'credentials'
$administratorCredential = Join-Path $credentialDirectory 'administrator-postgres.xml'
$codexCredential = Join-Path $credentialDirectory 'codex-test-role.xml'

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Run this script from an elevated Administrator PowerShell session.'
    }
}

function New-UrlSafePassword {
    $bytes = [byte[]]::new(32)
    [Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    return [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}

function Assert-ResolvableSid {
    param(
        [Parameter(Mandatory)][Security.Principal.SecurityIdentifier]$Sid,
        [Parameter(Mandatory)][string]$Purpose
    )

    try {
        [void]$Sid.Translate([Security.Principal.NTAccount])
    }
    catch {
        throw "Required identity SID $($Sid.Value) for $Purpose cannot be resolved on this host."
    }
}

function Set-ExactDirectoryAcl {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][System.Collections.IDictionary]$Rights
    )

    $acl = [Security.AccessControl.DirectorySecurity]::new()
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($sid in $Rights.Keys) {
        if ($sid -isnot [Security.Principal.SecurityIdentifier]) {
            throw 'Directory ACL entries must use SecurityIdentifier objects.'
        }
        $rule = [Security.AccessControl.FileSystemAccessRule]::new(
            $sid,
            [Security.AccessControl.FileSystemRights]$Rights[$sid],
            [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',
            [Security.AccessControl.PropagationFlags]::None,
            [Security.AccessControl.AccessControlType]::Allow
        )
        [void]$acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $Path -AclObject $acl
}

function Set-ExactFileAcl {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][System.Collections.IDictionary]$Rights
    )

    $acl = [Security.AccessControl.FileSecurity]::new()
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($sid in $Rights.Keys) {
        if ($sid -isnot [Security.Principal.SecurityIdentifier]) {
            throw 'Credential ACL entries must use SecurityIdentifier objects.'
        }
        $rule = [Security.AccessControl.FileSystemAccessRule]::new(
            $sid,
            [Security.AccessControl.FileSystemRights]$Rights[$sid],
            [Security.AccessControl.AccessControlType]::Allow
        )
        [void]$acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $Path -AclObject $acl
}

function Save-ProtectedPassword {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Password,
        [Parameter(Mandatory)][System.Collections.IDictionary]$Rights
    )

    ConvertTo-SecureString -String $Password -AsPlainText -Force |
        Export-Clixml -LiteralPath $Path -Force
    Set-ExactFileAcl -Path $Path -Rights $Rights
}

function Read-ProtectedPassword {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'The protected administrator credential is absent; recover the isolated cluster before continuing.'
    }
    $secure = Import-Clixml -LiteralPath $Path
    if ($secure -isnot [Security.SecureString]) {
        throw 'The protected administrator credential has an invalid format.'
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

function Invoke-AdministratorPsql {
    param([Parameter(Mandatory)][string]$Sql)

    $psql = Join-Path $binDirectory 'psql.exe'
    $previous = $env:PGPASSWORD
    $hadPrevious = Test-Path Env:PGPASSWORD
    $env:PGPASSWORD = Read-ProtectedPassword -Path $administratorCredential
    try {
        $Sql | & $psql '-X' '-v' 'ON_ERROR_STOP=1' '-h' $hostAddress '-p' $port '-U' 'postgres' '-d' 'postgres' '-f' '-'
        if ($LASTEXITCODE -ne 0) {
            throw 'Administrative PostgreSQL bootstrap command failed.'
        }
    }
    finally {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
        if ($hadPrevious) {
            $env:PGPASSWORD = $previous
        }
    }
}

function Wait-ForService {
    $ready = Join-Path $binDirectory 'pg_isready.exe'
    for ($attempt = 1; $attempt -le 24; $attempt += 1) {
        & $ready '-h' $hostAddress '-p' $port '-d' 'postgres' | Out-Null
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Start-Sleep -Seconds 1
    }
    throw 'The isolated PostgreSQL service did not become ready on 127.0.0.1:55432.'
}

Assert-Administrator
foreach ($tool in @('initdb.exe', 'pg_ctl.exe', 'psql.exe', 'pg_isready.exe', 'createdb.exe', 'dropdb.exe')) {
    if (-not (Test-Path -LiteralPath (Join-Path $binDirectory $tool) -PathType Leaf)) {
        throw "PostgreSQL 16 executable is missing: $tool. Install PostgreSQL 16 before retrying."
    }
}

$administratorsSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
$systemSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
$operatorIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$operatorSid = $operatorIdentity.User
$operatorName = $operatorIdentity.Name
if ($null -eq $operatorSid -or [string]::IsNullOrWhiteSpace($operatorName)) {
    throw 'The current Windows user SID is unavailable; refuse to configure protected credentials.'
}
foreach ($requiredIdentity in @(
    @{ Sid = $administratorsSid; Purpose = 'local administrators' },
    @{ Sid = $systemSid; Purpose = 'SYSTEM recovery' },
    @{ Sid = $operatorSid; Purpose = 'current Codex user credential access and PostgreSQL process ownership' }
)) {
    Assert-ResolvableSid -Sid $requiredIdentity.Sid -Purpose $requiredIdentity.Purpose
}
# No optional AppContainer SID is added: the verified Codex execution token uses
# the current user SID and has no S-1-15 AppContainer group. Granting an
# unverified package principal would expand access without proving necessity.
$rootRights = [ordered]@{
    $administratorsSid = 'FullControl'
    $systemSid = 'FullControl'
    $operatorSid = 'Traverse, Synchronize'
}
$credentialRights = [ordered]@{
    $administratorsSid = 'FullControl'
    $systemSid = 'FullControl'
    $operatorSid = 'ReadAndExecute'
}
$dataRights = [ordered]@{
    $administratorsSid = 'FullControl'
    $systemSid = 'FullControl'
    $operatorSid = 'FullControl'
}
New-Item -ItemType Directory -Path $rootDirectory, $credentialDirectory -Force | Out-Null
$newCluster = -not (Test-Path -LiteralPath (Join-Path $dataDirectory 'PG_VERSION') -PathType Leaf)
if ($newCluster) {
    if (Test-Path -LiteralPath $dataDirectory) {
        if ((Get-ChildItem -LiteralPath $dataDirectory -Force | Measure-Object).Count -ne 0) {
            throw 'The intended isolated data directory is nonempty but is not a PostgreSQL cluster; refuse to overwrite it.'
        }
    }
    else {
        New-Item -ItemType Directory -Path $dataDirectory -Force | Out-Null
    }
}
Set-ExactDirectoryAcl -Path $dataDirectory -Rights $dataRights
Set-ExactDirectoryAcl -Path $credentialDirectory -Rights $credentialRights
Set-ExactDirectoryAcl -Path $rootDirectory -Rights $rootRights

if ($newCluster) {
    # initdb accepts an empty target directory; preparing its owner ACL first
    # avoids creating through the intentionally traversal-only parent ACL.
    $temporaryPasswordFile = New-TemporaryFile
    try {
        $postgresPassword = New-UrlSafePassword
        Set-Content -LiteralPath $temporaryPasswordFile -Value $postgresPassword -NoNewline -Encoding ascii
        $initdb = Join-Path $binDirectory 'initdb.exe'
        & $initdb '-D' $dataDirectory '--username=postgres' '--encoding=UTF8' '--auth-host=scram-sha-256' '--auth-local=trust' "--pwfile=$temporaryPasswordFile"
        if ($LASTEXITCODE -ne 0) {
            throw 'initdb failed for the isolated Codex PostgreSQL cluster.'
        }
        Save-ProtectedPassword -Path $administratorCredential -Password $postgresPassword -Rights $credentialRights
    }
    finally {
        Remove-Item -LiteralPath $temporaryPasswordFile -Force -ErrorAction SilentlyContinue
        Remove-Variable postgresPassword -ErrorAction SilentlyContinue
    }
}

$postgresqlConf = @"
# R21-DEV-002 isolated Codex PostgreSQL test cluster.
listen_addresses = '$hostAddress'
port = $port
password_encryption = 'scram-sha-256'
ssl = off
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_statement = 'none'
"@
Set-Content -LiteralPath (Join-Path $dataDirectory 'postgresql.conf') -Value $postgresqlConf -Encoding ascii
$hbaConf = @"
# R21-DEV-002: loopback-only SCRAM authentication.
host all all 127.0.0.1/32 scram-sha-256
host all all ::1/128 reject
host all all 0.0.0.0/0 reject
host all all ::0/0 reject
"@
Set-Content -LiteralPath (Join-Path $dataDirectory 'pg_hba.conf') -Value $hbaConf -Encoding ascii

$legacyService = Get-CimInstance Win32_Service -Filter "Name='$taskName'" -ErrorAction SilentlyContinue
if ($null -ne $legacyService) {
    if ($legacyService.PathName -notlike "*$dataDirectory*") {
        throw 'A service with the Codex task name points to another data directory; refuse to remove it.'
    }
    if ((Get-Service -Name $taskName).Status -ne 'Stopped') {
        Stop-Service -Name $taskName -Force
    }
    & sc.exe delete $taskName | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to remove the failed legacy PostgreSQL service.'
    }
}

$postgres = Join-Path $binDirectory 'postgres.exe'
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($null -eq $existingTask) {
    $action = New-ScheduledTaskAction -Execute $postgres -Argument "-D `"$dataDirectory`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $operatorName
    $principal = New-ScheduledTaskPrincipal -UserId $operatorName -LogonType Interactive
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew -StartWhenAvailable
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
}
else {
    $taskAction = $existingTask.Actions | Select-Object -First 1
    if ($null -eq $taskAction -or $taskAction.Execute -ne $postgres -or $taskAction.Arguments -notlike "*$dataDirectory*") {
        throw 'An existing Codex PostgreSQL task has another command or data directory; refuse to modify it.'
    }
    try {
        $taskAccountSid = ([Security.Principal.NTAccount]::new($existingTask.Principal.UserId)).Translate([Security.Principal.SecurityIdentifier])
    }
    catch {
        throw 'The existing Codex PostgreSQL task user cannot be translated to a SID.'
    }
    if ($taskAccountSid.Value -ne $operatorSid.Value) {
        throw 'The existing Codex PostgreSQL task is not owned by the current user; refuse to modify it.'
    }
}
if ((Get-ScheduledTask -TaskName $taskName).State -ne 'Running') {
    Start-ScheduledTask -TaskName $taskName
}
Wait-ForService

if (-not (Test-Path -LiteralPath $codexCredential -PathType Leaf) -or $RotateCodexCredential) {
    $codexPassword = New-UrlSafePassword
    try {
        $bootstrapSql = @"
DO `$`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$role') THEN
        CREATE ROLE $role LOGIN NOSUPERUSER NOCREATEROLE CREATEDB NOREPLICATION NOBYPASSRLS;
    END IF;
END
`$`$;
ALTER ROLE $role NOSUPERUSER NOCREATEROLE CREATEDB NOREPLICATION NOBYPASSRLS LOGIN PASSWORD '$codexPassword';
REVOKE ALL ON DATABASE postgres FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE postgres TO $role;
"@
        Invoke-AdministratorPsql -Sql $bootstrapSql
        Save-ProtectedPassword -Path $codexCredential -Password $codexPassword -Rights $credentialRights
    }
    finally {
        Remove-Variable codexPassword -ErrorAction SilentlyContinue
    }
}
else {
    Invoke-AdministratorPsql -Sql "ALTER ROLE $role NOSUPERUSER NOCREATEROLE CREATEDB NOREPLICATION NOBYPASSRLS LOGIN; REVOKE ALL ON DATABASE postgres FROM PUBLIC; GRANT CONNECT, TEMPORARY ON DATABASE postgres TO $role;"
}

Write-Output 'R21 Codex PostgreSQL test environment is ready on 127.0.0.1:55432.'