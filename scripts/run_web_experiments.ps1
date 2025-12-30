Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$env:LOCUST_USER = "locust"
$env:LOCUST_PASS = "1234"
$env:VALID_RATIO = "0.8"

function Stop-DaphneProcesses {
  Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*daphne*config.asgi:application*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
}

function Start-Daphne([bool]$DefensesOn) {
  $env:DEFENSES_ON = if ($DefensesOn) { "1" } else { "0" }
  $env:ABUSE_ALLOW_LOCAL = if ($DefensesOn) { "0" } else { "1" }
  $env:ABUSE_MAX_401 = if ($DefensesOn) { "3" } else { "15" }
  $env:ABUSE_WINDOW_SECONDS = "60"
  $env:ABUSE_BLOCK_SECONDS = "600"

  $repo = (Get-Location).Path
  Push-Location .\web
  $py = (Get-Command python).Source
  $stdout = Join-Path $repo "daphne_manual.log"
  $stderr = Join-Path $repo "daphne_manual.err.log"
  Start-Process -FilePath $py -ArgumentList "-m daphne -b 0.0.0.0 -p 8000 config.asgi:application" -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow | Out-Null
  Pop-Location
  Start-Sleep -Seconds 2
}

function Run-Locust([string]$Scenario, [string]$DefenseLabel, [int]$Users, [int]$SpawnRate, [string]$RunTime) {
  $stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
  $runName = "{0}__{1}__{2}__rep1" -f $stamp, $Scenario, $DefenseLabel
  $runDir = Join-Path "web\experiments\runs" $runName
  New-Item -ItemType Directory -Force -Path $runDir | Out-Null
  $env:SCENARIO = $Scenario
  Write-Host "Running $Scenario ($DefenseLabel) -> $runName"
  locust -f .\web\locustfile.py --headless -H http://127.0.0.1:8000 -u $Users -r $SpawnRate -t $RunTime --csv "$runDir\locust"
}

Stop-DaphneProcesses
Write-Host "Starting Daphne with defenses OFF..."
Start-Daphne $false

Run-Locust "baseline_public_state" "baseline" 10 2 "2m"
Run-Locust "auth_login_storm" "attacked" 10 2 "2m"
Run-Locust "secure_valid_only" "baseline" 10 2 "2m"
Run-Locust "secure_valid_only" "attacked" 10 2 "2m"
Run-Locust "secure_mixed" "baseline" 10 2 "2m"
Run-Locust "secure_mixed" "attacked" 10 2 "2m"

Stop-DaphneProcesses
Write-Host "Starting Daphne with defenses ON..."
Start-Daphne $true

$redisName = docker ps --format "{{.Names}}" | rg redis-1
if ($redisName) { docker exec $redisName redis-cli -n 1 FLUSHDB | Out-Null }

Run-Locust "secure_valid_only" "defended" 10 2 "2m"
Run-Locust "secure_mixed" "defended" 10 2 "2m"

Write-Host "Runs complete."
