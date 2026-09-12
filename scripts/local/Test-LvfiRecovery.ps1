[CmdletBinding()]
param(
    [Parameter(Mandatory)][uri]$ApiBaseUrl,
    [Parameter(Mandatory)][string]$SnapshotId,
    [Parameter(Mandatory)][Security.SecureString]$AdminPassword,
    [int]$TimeoutSeconds = 15
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($TimeoutSeconds -lt 1 -or $TimeoutSeconds -gt 60) { throw 'TimeoutSeconds must be between 1 and 60.' }
$base = $ApiBaseUrl.AbsoluteUri.TrimEnd('/')
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$bstr = [IntPtr]::Zero
$temporaryPdf = $null
& (Join-Path $PSScriptRoot 'Test-LvfiHealth.ps1') -ApiBaseUrl $ApiBaseUrl -TimeoutSeconds $TimeoutSeconds | Out-Null
try {
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($AdminPassword)
    $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    $login = Invoke-WebRequest -Uri "$base/auth/login" -Method Post -WebSession $session -ContentType 'application/json' -Body (@{ password = $password } | ConvertTo-Json -Compress) -UseBasicParsing -TimeoutSec $TimeoutSeconds
}
catch {
    throw 'Local administrator authentication failed during recovery validation.'
}
finally {
    if ($bstr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
    $password = $null
}
if ($login.StatusCode -ne 200) { throw 'Local administrator authentication returned an unexpected status.' }
try {
    $snapshot = Invoke-WebRequest -Uri "$base/analysis-snapshots/$SnapshotId" -WebSession $session -UseBasicParsing -TimeoutSec $TimeoutSeconds
    if ($snapshot.StatusCode -ne 200) { throw 'snapshot status' }
    $artifactsResponse = Invoke-WebRequest -Uri "$base/analysis-snapshots/$SnapshotId/pdfs" -WebSession $session -UseBasicParsing -TimeoutSec $TimeoutSeconds
    $artifacts = ($artifactsResponse.Content | ConvertFrom-Json).artifacts
    if (@($artifacts).Count -lt 1) { throw 'no artifacts' }
    $artifact = @($artifacts)[0]
    if ([string]::IsNullOrWhiteSpace($artifact.artifact_id) -or [string]::IsNullOrWhiteSpace($artifact.sha256)) { throw 'invalid artifact metadata' }
    $temporaryPdf = [IO.Path]::GetTempFileName()
    $download = Invoke-WebRequest -Uri "$base/analysis-pdfs/$($artifact.artifact_id)/download" -WebSession $session -UseBasicParsing -TimeoutSec $TimeoutSeconds -OutFile $temporaryPdf
    $pdfBytes = (Get-Item -LiteralPath $temporaryPdf).Length
    $downloadHash = (Get-FileHash -LiteralPath $temporaryPdf -Algorithm SHA256).Hash.ToLowerInvariant()
    $downloadStatus = $download.PSObject.Properties['StatusCode']
    if (($null -ne $downloadStatus -and $downloadStatus.Value -ne 200) -or $pdfBytes -lt 5 -or $downloadHash -ne $artifact.sha256.ToLowerInvariant()) { throw 'download validation' }
}
catch {
    throw 'Restored snapshot or PDF artifact could not be consulted and downloaded.'
}
finally {
    if ($temporaryPdf -and (Test-Path -LiteralPath $temporaryPdf)) { Remove-Item -LiteralPath $temporaryPdf -Force }
}
[pscustomobject]@{ snapshot_id = $SnapshotId; artifact_id = $artifact.artifact_id; artifact_sha256 = $artifact.sha256; pdf_bytes = $pdfBytes; restored_api_validation = 'passed' }
