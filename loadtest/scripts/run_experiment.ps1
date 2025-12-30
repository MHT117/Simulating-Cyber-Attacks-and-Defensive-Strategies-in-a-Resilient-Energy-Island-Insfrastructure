param(
  [Parameter(Mandatory=$true)][string]$Name,
  [Parameter(Mandatory=$true)][string]$LocustFile,   # e.g. perf\locustfile.py
  [Parameter(Mandatory=$true)][int]$Users,
  [Parameter(Mandatory=$true)][int]$SpawnRate,
  [Parameter(Mandatory=$true)][string]$RunTime,      # e.g. 2m, 30s
  [string]$AppHost = "http://127.0.0.1:8000",
  [string]$PromUrl = "http://localhost:9090",
  [switch]$UseMarkers,
  [bool]$DefensesOn = $true
)

. "$PSScriptRoot\common.ps1"

$RepoRoot = Get-RepoRoot
$WebDir   = Join-Path $RepoRoot "web"
$RunRoot  = Join-Path $RepoRoot "research\runs"
$Stamp    = Get-Timestamp
$RunDir   = Join-Path $RunRoot ("{0}_{1}" -f $Stamp, $Name)

Ensure-Folder $RunDir

# --- Defense toggles (affect Django settings)
if ($DefensesOn) {
  $env:DEFENSES_ON = "1"
  $env:ABUSE_ALLOW_LOCAL = "0"
} else {
  $env:DEFENSES_ON = "0"
  $env:ABUSE_ALLOW_LOCAL = "1"
}

# --- Activate venv for this PowerShell session
$VenvActivate = Join-Path $RepoRoot "egisland\Scripts\Activate.ps1"
if (!(Test-Path $VenvActivate)) { throw "Venv not found: $VenvActivate" }
. $VenvActivate

# --- Save metadata early
$meta = [ordered]@{
  name       = $Name
  timestamp  = $Stamp
  host       = $AppHost
  users      = $Users
  spawn_rate = $SpawnRate
  run_time   = $RunTime
  locustfile = $LocustFile
  defenses_on = $DefensesOn
}
($meta | ConvertTo-Json -Depth 5) | Set-Content (Join-Path $RunDir "meta.json") -Encoding UTF8

# --- Ensure Docker stack up
Push-Location $RepoRoot
docker compose up -d | Out-Null
docker compose ps | Out-String | Set-Content (Join-Path $RunDir "docker_ps.txt") -Encoding UTF8
Pop-Location

# --- Start Daphne (ASGI) and log output
$DaphneOut = Join-Path $RunDir "daphne.log"
$DaphneErr = Join-Path $RunDir "daphne.err.log"
$DaphneArgs = "-m daphne -b 0.0.0.0 -p 8000 config.asgi:application"

Push-Location $WebDir
$py = (Get-Command python).Source
$daphneProc = Start-Process -FilePath $py -ArgumentList $DaphneArgs -RedirectStandardOutput $DaphneOut -RedirectStandardError $DaphneErr -NoNewWindow -PassThru
Pop-Location

# --- Wait for app readiness via Nginx front
Wait-HttpOk "$AppHost/api/state" 30 | Out-Null

# --- Snapshot env & code state
Push-Location $RepoRoot
git rev-parse HEAD 2>$null | Out-String | Set-Content (Join-Path $RunDir "git_commit.txt") -Encoding UTF8
git status --porcelain 2>$null | Out-String | Set-Content (Join-Path $RunDir "git_status.txt") -Encoding UTF8
python --version | Out-String | Set-Content (Join-Path $RunDir "python_version.txt") -Encoding UTF8
pip freeze | Out-String | Set-Content (Join-Path $RunDir "pip_freeze.txt") -Encoding UTF8

# Snapshot key configs (best effort)
Copy-Item -Force -ErrorAction SilentlyContinue (Join-Path $RepoRoot "infra\nginx.conf") (Join-Path $RunDir "nginx.conf")
Copy-Item -Force -ErrorAction SilentlyContinue (Join-Path $RepoRoot "infra\prometheus.yml") (Join-Path $RunDir "prometheus.yml")
Copy-Item -Force -ErrorAction SilentlyContinue (Join-Path $RepoRoot "web\config\settings.py") (Join-Path $RunDir "settings.py")
Copy-Item -Force -ErrorAction SilentlyContinue (Join-Path $RepoRoot "web\api\views.py") (Join-Path $RunDir "api_views.py")
Copy-Item -Force -ErrorAction SilentlyContinue (Join-Path $RepoRoot "web\api\urls.py") (Join-Path $RunDir "api_urls.py")
Pop-Location

# --- Prometheus snapshot (start)
try {
  $startSnap = [ordered]@{
    time = (Get-Date).ToString("o")
    rps_total = PromQuery $PromUrl "sum(rate(django_http_responses_total[1m]))"
    http_401  = PromQuery $PromUrl "sum(rate(django_http_responses_total{status=\"401\"}[1m]))"
    http_403  = PromQuery $PromUrl "sum(rate(django_http_responses_total{status=\"403\"}[1m]))"
    http_429  = PromQuery $PromUrl "sum(rate(django_http_responses_total{status=\"429\"}[1m]))"
  }
  ($startSnap | ConvertTo-Json -Depth 10) | Set-Content (Join-Path $RunDir "prom_start.json") -Encoding UTF8
} catch {
  "Prometheus start snapshot failed: $($_.Exception.Message)" | Set-Content (Join-Path $RunDir "prom_start_error.txt") -Encoding UTF8
}

# --- Marker: attack start (optional)
if ($UseMarkers) {
  $ok = Try-CallMarker $AppHost "attack_start"
  "marker attack_start: $ok" | Set-Content (Join-Path $RunDir "markers.txt") -Encoding UTF8
}

# --- Run Locust (headless) output into run folder
$CsvPrefix = Join-Path $RunDir "locust"
$LocustPath = Join-Path $RepoRoot $LocustFile
if (!(Test-Path $LocustPath)) { throw "Locust file not found: $LocustPath" }

$locustArgs = @(
  "-m", "locust",
  "-f", $LocustPath,
  "--host", $AppHost,
  "--users", $Users,
  "--spawn-rate", $SpawnRate,
  "--run-time", $RunTime,
  "--headless",
  "--csv", $CsvPrefix
)

$LocustOut = Join-Path $RunDir "locust.log"
$LocustErr = Join-Path $RunDir "locust.err.log"
$py = (Get-Command python).Source
$locProc = Start-Process -FilePath $py -ArgumentList $locustArgs -RedirectStandardOutput $LocustOut -RedirectStandardError $LocustErr -NoNewWindow -PassThru
$locProc.WaitForExit()

# --- Marker: attack end (optional)
if ($UseMarkers) {
  $ok2 = Try-CallMarker $AppHost "attack_end"
  Add-Content (Join-Path $RunDir "markers.txt") ("marker attack_end: {0}" -f $ok2)
}

# --- Prometheus snapshot (end)
try {
  $endSnap = [ordered]@{
    time = (Get-Date).ToString("o")
    rps_total = PromQuery $PromUrl "sum(rate(django_http_responses_total[1m]))"
    http_401  = PromQuery $PromUrl "sum(rate(django_http_responses_total{status=\"401\"}[1m]))"
    http_403  = PromQuery $PromUrl "sum(rate(django_http_responses_total{status=\"403\"}[1m]))"
    http_429  = PromQuery $PromUrl "sum(rate(django_http_responses_total{status=\"429\"}[1m]))"
  }
  ($endSnap | ConvertTo-Json -Depth 10) | Set-Content (Join-Path $RunDir "prom_end.json") -Encoding UTF8
} catch {
  "Prometheus end snapshot failed: $($_.Exception.Message)" | Set-Content (Join-Path $RunDir "prom_end_error.txt") -Encoding UTF8
}

# --- Stop Daphne
try {
  if (!$daphneProc.HasExited) { Stop-Process -Id $daphneProc.Id -Force }
} catch {}

# --- Create RUN.md summary template
$runMd = @"
# Run: $Name

- Timestamp: $Stamp
- Host: $AppHost
- Locust file: $LocustFile
- Users: $Users
- Spawn rate: $SpawnRate
- Duration: $RunTime
- Markers used: $UseMarkers
- Defenses ON: $DefensesOn

## What to paste into dissertation
- Put p50/p95/p99 from: locust_stats.csv
- Error breakdown from: locust_failures.csv (and Prometheus snapshots if available)
- Attach Grafana screenshots taken during run:
  - RPS
  - p95 latency
  - 401/403/429 rates
  - Nginx connections
  - Redis memory/health

## Notes
- Record whether defenses were ON (nginx zones + DRF scopes + abuse blocklist).
"@
$runMd | Set-Content (Join-Path $RunDir "RUN.md") -Encoding UTF8

Write-Host "DONE. Artifacts saved to: $RunDir"
