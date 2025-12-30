param(
  [int]$Repeats = 3,
  [string]$TargetHost = $env:LOCUST_HOST,
  [string]$RunsDir = "$(Join-Path $PSScriptRoot "..\runs")"
)

if (-not $TargetHost) { $TargetHost = "http://127.0.0.1:8000" }

# Baseline (legitimate)
$baseline = @(
  @{ Scenario="baseline_public_state"; Condition="baseline"; Users=10; SpawnRate=2; Duration="2m" },
  @{ Scenario="secure_valid_only";      Condition="baseline"; Users=20; SpawnRate=5; Duration="2m" }
)

# Attacked (defenses OFF)
$attacked = @(
  @{ Scenario="secure_mixed_80_20"; Condition="attacked"; Users=50; SpawnRate=10; Duration="2m" },
  @{ Scenario="auth_login_storm";   Condition="attacked"; Users=80; SpawnRate=20; Duration="2m" }
)

$all = $baseline + $attacked

for ($r=1; $r -le $Repeats; $r++) {
  foreach ($cfg in $all) {
    .\run_one.ps1 -Scenario $cfg.Scenario -Condition $cfg.Condition -Users $cfg.Users -SpawnRate $cfg.SpawnRate -Duration $cfg.Duration -TargetHost $TargetHost -RunsDir $RunsDir -Repeat $r
    Start-Sleep -Seconds 10
  }
}
