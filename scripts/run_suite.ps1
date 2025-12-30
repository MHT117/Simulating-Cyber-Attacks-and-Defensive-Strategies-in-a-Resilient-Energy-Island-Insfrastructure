# Runs all scenarios back-to-back.
# Adjust numbers if your machine struggles.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

& "$PSScriptRoot\run_baseline_public.ps1" -Users 50 -SpawnRate 5 -RunTime "2m"
Start-Sleep -Seconds 5

& "$PSScriptRoot\run_jwt_mixed.ps1" -Users 80 -SpawnRate 8 -RunTime "3m"
Start-Sleep -Seconds 5

& "$PSScriptRoot\run_login_storm.ps1" -Users 40 -SpawnRate 10 -RunTime "2m"
