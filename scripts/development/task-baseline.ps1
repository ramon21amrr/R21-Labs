[CmdletBinding()]
param([switch]$AsJson)
$ErrorActionPreference = 'Stop'
$root = (git rev-parse --show-toplevel).Trim(); $branch = (git branch --show-current).Trim(); $head = (git rev-parse HEAD).Trim(); $originMain = (git rev-parse origin/main).Trim()
$counts = (git rev-list --left-right --count HEAD...origin/main).Trim() -split '\s+'
$changes = @(git diff --name-only origin/main...HEAD; git diff --name-only; git ls-files --others --exclude-standard) | Where-Object { $_ } | Sort-Object -Unique
$areas = @(); if ($changes | Where-Object { $_ -like 'docs/*' -or $_ -like '*.md' }) { $areas += 'docs' }; if ($changes | Where-Object { $_ -like 'apps/api/*' }) { $areas += 'api' }; if ($changes | Where-Object { $_ -like 'packages/pricing-engine/*' }) { $areas += 'pricing' }; if (-not $areas) { $areas = @('docs') }
$result = [ordered]@{ repository=$root; branch=$branch; head=$head; origin_main=$originMain; ahead=[int]$counts[0]; behind=[int]$counts[1]; working_tree=if ((git status --porcelain)) {'dirty'} else {'clean'}; changed_areas=$changes; recommended_gate_profiles=$areas }
if ($AsJson) { $result | ConvertTo-Json -Depth 4 -Compress } else { $result.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value -join ',')" } }