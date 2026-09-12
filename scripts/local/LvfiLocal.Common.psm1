Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-LvfiLocalPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Label,
        [switch]$CreateDirectory
    )

    if ([string]::IsNullOrWhiteSpace($Path)) { throw "$Label is required." }
    if ($CreateDirectory -and -not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
    if (-not (Test-Path -LiteralPath $Path)) { throw "$Label does not exist." }
    return (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
}

function Get-LvfiLocalRelativePath {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Root, [Parameter(Mandatory)][string]$Path)

    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $pathFull = [IO.Path]::GetFullPath($Path)
    $prefix = "$rootFull$([IO.Path]::DirectorySeparatorChar)"
    if (-not $pathFull.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'A backup file escaped its expected root.'
    }
    return $pathFull.Substring($prefix.Length).Replace('\', '/')
}

function Join-LvfiLocalSafePath {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Root, [Parameter(Mandatory)][string]$RelativePath)

    if ([IO.Path]::IsPathRooted($RelativePath) -or $RelativePath -match '(^|[\\/])\.\.([\\/]|$)') {
        throw 'The manifest contains an unsafe relative path.'
    }
    $candidate = [IO.Path]::GetFullPath((Join-Path $Root $RelativePath))
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $prefix = "$rootFull$([IO.Path]::DirectorySeparatorChar)"
    if (-not $candidate.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'The manifest path escaped the backup bundle.'
    }
    return $candidate
}

function Assert-LvfiLocalOutsidePaths {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Candidate, [Parameter(Mandatory)][string[]]$ActiveDataPath)

    $candidateFull = [IO.Path]::GetFullPath($Candidate).TrimEnd('\', '/')
    foreach ($activePath in $ActiveDataPath) {
        $activeFull = [IO.Path]::GetFullPath($activePath).TrimEnd('\', '/')
        $activePrefix = "$activeFull$([IO.Path]::DirectorySeparatorChar)"
        $candidatePrefix = "$candidateFull$([IO.Path]::DirectorySeparatorChar)"
        if ($candidateFull.Equals($activeFull, [StringComparison]::OrdinalIgnoreCase) -or
            $candidateFull.StartsWith($activePrefix, [StringComparison]::OrdinalIgnoreCase) -or
            $activeFull.StartsWith($candidatePrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'BackupRoot must be outside every declared active data path.'
        }
    }
}

function Assert-LvfiLocalRestoreTarget {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RestoreRoot,
        [Parameter(Mandatory)][string]$Candidate,
        [Parameter(Mandatory)][string]$BackupPath,
        [Parameter(Mandatory)][string]$Label
    )

    $rootFull = [IO.Path]::GetFullPath($RestoreRoot).TrimEnd('\', '/')
    $candidateFull = [IO.Path]::GetFullPath($Candidate).TrimEnd('\', '/')
    $backupFull = [IO.Path]::GetFullPath($BackupPath).TrimEnd('\', '/')
    $rootPrefix = "$rootFull$([IO.Path]::DirectorySeparatorChar)"
    $backupPrefix = "$backupFull$([IO.Path]::DirectorySeparatorChar)"
    if ($candidateFull -eq $rootFull -or -not $candidateFull.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label must be a child of the explicit RestoreRoot."
    }
    if ($candidateFull -eq $backupFull -or $candidateFull.StartsWith($backupPrefix, [StringComparison]::OrdinalIgnoreCase) -or $backupFull.StartsWith("$candidateFull$([IO.Path]::DirectorySeparatorChar)", [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label must not overlap the backup bundle."
    }
}

function Copy-LvfiLocalRecoveryContent {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Source, [Parameter(Mandatory)][string]$Destination)

    $excluded = @('cache', 'caches', '.cache', '__pycache__', 'log', 'logs', 'build', 'builds', '.next', 'node_modules', 'session', 'sessions')
    $sourceRoot = [IO.Path]::GetFullPath($Source).TrimEnd('\', '/')
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceRoot -Force -Recurse -File | ForEach-Object {
        $relative = Get-LvfiLocalRelativePath -Root $sourceRoot -Path $_.FullName
        if (@($relative.Split('/') | Where-Object { $excluded -contains $_.ToLowerInvariant() }).Count -gt 0 -or $_.Extension -ieq '.log') { return }
        $target = Join-LvfiLocalSafePath -Root $Destination -RelativePath $relative
        New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $target -Force
    }
}

function Get-LvfiLocalFileManifestEntries {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Root)

    return @(
        Get-ChildItem -LiteralPath $Root -Recurse -File | Sort-Object FullName | ForEach-Object {
            [ordered]@{
                path = Get-LvfiLocalRelativePath -Root $Root -Path $_.FullName
                bytes = [int64]$_.Length
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        }
    )
}

function Test-LvfiLocalManifest {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$BackupPath)

    $manifestPath = Join-Path $BackupPath 'manifest.json'
    $manifestHashPath = Join-Path $BackupPath 'manifest.sha256'
    if (-not (Test-Path -LiteralPath $manifestPath) -or -not (Test-Path -LiteralPath $manifestHashPath)) {
        throw 'Backup manifest or its SHA-256 file is missing.'
    }
    $expectedManifestHash = ((Get-Content -LiteralPath $manifestHashPath -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
    $actualManifestHash = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($expectedManifestHash -ne $actualManifestHash) { throw 'Backup manifest SHA-256 does not match.' }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifest.schema -ne 'lvfi-local-backup/v1') { throw 'Unsupported backup manifest schema.' }
    foreach ($entry in @($manifest.files)) {
        $filePath = Join-LvfiLocalSafePath -Root $BackupPath -RelativePath $entry.path
        if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) { throw "Backup file is missing: $($entry.path)" }
        $actualHash = (Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $entry.sha256.ToLowerInvariant()) { throw "Backup file hash does not match: $($entry.path)" }
    }
    return $manifest
}

Export-ModuleMember -Function Resolve-LvfiLocalPath, Get-LvfiLocalRelativePath, Join-LvfiLocalSafePath, Assert-LvfiLocalOutsidePaths, Assert-LvfiLocalRestoreTarget, Copy-LvfiLocalRecoveryContent, Get-LvfiLocalFileManifestEntries, Test-LvfiLocalManifest
