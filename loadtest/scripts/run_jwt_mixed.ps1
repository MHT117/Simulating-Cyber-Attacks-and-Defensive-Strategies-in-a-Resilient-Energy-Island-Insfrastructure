param(
  [int]$Users = 80,
  [int]$SpawnRate = 8,
  [string]$RunTime = "3m"
)
& "$PSScriptRoot\run_experiment.ps1" `
  -Name "secure_mixed_80_20" `
  -LocustFile "loadtests\locust_secure_mixed_80_20.py" `
  -Users $Users `
  -SpawnRate $SpawnRate `
  -RunTime $RunTime `
  -UseMarkers `
  -DefensesOn:$false
