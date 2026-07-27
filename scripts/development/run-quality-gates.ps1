[CmdletBinding()]
param([ValidateSet('docs','api','pricing','full')][string]$Profile='docs',[switch]$DryRun)
$ErrorActionPreference = 'Stop'
$root=(git rev-parse --show-toplevel).Trim(); $artifact=Join-Path $root '.r21-artifacts\quality'; New-Item -ItemType Directory -Path $artifact -Force | Out-Null; $log=Join-Path $artifact ("gates-{0:yyyyMMdd-HHmmss}-{1}.log" -f (Get-Date),$Profile)
function Invoke-Gate([string]$Name,[scriptblock]$Command) { "[$Name]" | Tee-Object -FilePath $log -Append; if($DryRun){'dry-run' | Tee-Object -FilePath $log -Append; return}; & $Command *>&1 | Tee-Object -FilePath $log -Append; if($LASTEXITCODE -ne 0){throw "$Name failed; full log: $log"} }
Invoke-Gate 'powershell-parser' { $errors=$null; Get-ChildItem -LiteralPath (Join-Path $root 'scripts') -Recurse -Filter '*.ps1' | ForEach-Object {[void][System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$null,[ref]$errors); if($errors){$errors | ForEach-Object {throw $_}}} }
Invoke-Gate 'git-diff-check' { git diff --check }
if($Profile -in @('docs','full')) { Invoke-Gate 'markdown-local-links' { $missing=@(); Get-ChildItem -LiteralPath (Join-Path $root 'docs') -Recurse -Filter '*.md' | ForEach-Object {$base=$_.DirectoryName; foreach($m in [regex]::Matches((Get-Content -Raw $_.FullName),'\]\((?!https?://|mailto:|#)([^)#]+)')){$candidate=Join-Path $base $m.Groups[1].Value; if(-not(Test-Path -LiteralPath $candidate)){$missing+="$($_.FullName):$($m.Groups[1].Value)"}}}; if($missing){throw "Missing local links: $($missing -join '; ')"} } }
if($Profile -in @('api','full')) { Invoke-Gate 'api-tests' { Push-Location (Join-Path $root 'apps\api'); try {uv run pytest -q} finally {Pop-Location} } }
if($Profile -in @('pricing','full')) { Invoke-Gate 'pricing-tests' { Push-Location (Join-Path $root 'packages\pricing-engine'); try {uv run pytest -q} finally {Pop-Location} } }
"passed profile=$Profile log=$log"