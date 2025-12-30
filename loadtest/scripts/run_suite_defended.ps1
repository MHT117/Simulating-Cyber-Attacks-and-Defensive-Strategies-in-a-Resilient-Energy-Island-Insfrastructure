param(
  [int]$Repeats = 3,
  [string]$TargetHost = $env:LOCUST_HOST,
  [string]$RunsDir = "$(Join-Path $PSScriptRoot "..\runs")"
)

if (-not $TargetHost) { $TargetHost = "http://127.0.0.1:8000" }

# Defended (defenses ON in backend)
$defended = @(
  @{ Scenario="secure_mixed_80_20"; Condition="defended"; Users=50; SpawnRate=10; Duration="2m" },
  @{ Scenario="auth_login_storm";   Condition="defended"; Users=80; SpawnRate=20; Duration="2m" }
)

for ($r=1; $r -le $Repeats; $r++) {
  foreach ($cfg in $defended) {
    .\run_one.ps1 -Scenario $cfg.Scenario -Condition $cfg.Condition -Users $cfg.Users -SpawnRate $cfg.SpawnRate -Duration $cfg.Duration -TargetHost $TargetHost -RunsDir $RunsDir -Repeat $r
    Start-Sleep -Seconds 10
  }
}
