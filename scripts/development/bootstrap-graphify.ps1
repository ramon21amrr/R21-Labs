[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [string]$ExpectedVersion = '0.9.25'
)

$ErrorActionPreference = 'Stop'
function Get-InstalledGraphifyVersion {
    $listing = & uv tool list 2>&1
    if ($LASTEXITCODE -ne 0) { throw "uv tool list failed: $listing" }
    $match = [regex]::Match(($listing -join "`n"), '(?m)^graphifyy v(?<version>\S+)')
    if ($match.Success) { return $match.Groups['version'].Value }
    return $null
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'uv was not found. Install uv before bootstrapping Graphify.' }
$installed = Get-InstalledGraphifyVersion
if ($installed -eq $ExpectedVersion) { [pscustomobject]@{ status='ready'; version=$installed; changed=$false } | ConvertTo-Json -Compress; exit 0 }
if ($CheckOnly) { $actual = if ($installed) { $installed } else { 'not installed' }; throw "Graphify $ExpectedVersion is required; found $actual. Run without -CheckOnly to install it in uv's isolated tool environment." }
& uv tool install "graphifyy==$ExpectedVersion"
if ($LASTEXITCODE -ne 0) { throw 'Graphify installation failed.' }
$installed = Get-InstalledGraphifyVersion
if ($installed -ne $ExpectedVersion) { throw "Graphify verification failed; expected $ExpectedVersion, found $installed." }
[pscustomobject]@{ status='ready'; version=$installed; changed=$true } | ConvertTo-Json -Compress