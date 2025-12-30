param(
  [Parameter(Mandatory=$true)][string]$Scenario,
  [Parameter(Mandatory=$true)][ValidateSet("baseline","attacked","defended")][string]$Condition,
  [int]$Users = 20,
  [int]$SpawnRate = 5,
  [string]$Duration = "2m",
  [string]$Host = $env:LOCUST_HOST,
  [string]$RunsDir = "$(Join-Path $PSScriptRoot "..\runs")",
  [int]$Repeat = 1
)

if (-not $Host) { $Host = "http://127.0.0.1:8000" }

$ts = (Get-Date).ToString("yyyyMMdd_HHmmss")
$runId = "${Scenario}__${Condition}__r{0:D2}__${ts}" -f $Repeat
$runPath = Join-Path $RunsDir $runId
New-Item -ItemType Directory -Force -Path $runPath | Out-Null

$meta = @{
  run_id    = $runId
  scenario  = $Scenario
  condition = $Condition
  repeat    = $Repeat
  host      = $Host
  users     = $Users
  spawn_rate= $SpawnRate
  duration  = $Duration
  started_at= (Get-Date).ToString("o")
} | ConvertTo-Json -Depth 5
Set-Content -Path (Join-Path $runPath "meta.json") -Value $meta -Encoding UTF8

Write-Host "Run: $runId"
Write-Host "Host: $Host"
Write-Host "Users: $Users  SpawnRate: $SpawnRate  Duration: $Duration"
Write-Host "Output: $runPath"

$csvPrefix = Join-Path $runPath "locust"

# Locust writes multiple files: locust_stats.csv, locust_failures.csv, locust_stats_history.csv, locust_exceptions.csv
locust -f (Join-Path $PSScriptRoot "..\locustfile.py") `
  --headless `
  --host $Host `
  --users $Users `
  --spawn-rate $SpawnRate `
  --run-time $Duration `
  --tags $Scenario `
  --csv $csvPrefix `
  --csv-full-history `
  2>&1 | Tee-Object -FilePath (Join-Path $runPath "locust.log")
