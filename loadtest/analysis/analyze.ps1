param(
  [string]$RunsDir = "$(Join-Path $PSScriptRoot "..\runs")",
  [string]$OutDir  = "$(Join-Path $PSScriptRoot "..\exports")"
)

python (Join-Path $PSScriptRoot "build_results.py") --runs-dir $RunsDir --out $OutDir
python (Join-Path $PSScriptRoot "make_plots.py") --in (Join-Path $OutDir "results_summary.csv") --out $OutDir
Write-Host "Done. See: $OutDir"
