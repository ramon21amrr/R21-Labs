[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)][ValidateNotNullOrEmpty()][string]$Question,
    [ValidateRange(800, 5000)][int]$Budget = 1200,
    [switch]$Dfs
)
$ErrorActionPreference = 'Stop'
$root = (git rev-parse --show-toplevel 2>$null).Trim()
if (-not $root) { throw 'Run inside a Git repository.' }
if (-not (Test-Path -LiteralPath (Join-Path $root 'graphify-out\graph.json'))) { throw 'Graph is absent. Use targeted rg search, then run the documented Graphify refresh.' }
$command = Get-Command graphify -ErrorAction SilentlyContinue
if ($command) { $executable = $command.Source } else { if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'Graphify is unavailable and uv was not found. Use targeted rg search.' }; $candidate = Join-Path ((& uv tool dir).Trim()) 'graphifyy\Scripts\graphify.exe'; if (-not (Test-Path -LiteralPath $candidate)) { throw 'Graphify is not installed. Run bootstrap-graphify.ps1, or use targeted rg search.' }; $executable = $candidate }
$arguments = @('query', $Question, '--budget', $Budget)
if ($Dfs) { $arguments += '--dfs' }
& $executable @arguments
exit $LASTEXITCODE