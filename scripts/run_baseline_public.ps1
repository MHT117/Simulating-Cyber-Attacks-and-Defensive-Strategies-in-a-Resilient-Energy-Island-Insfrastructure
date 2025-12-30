param(
  [int]$Users = 50,
  [int]$SpawnRate = 5,
  [string]$RunTime = "2m"
)
& "$PSScriptRoot\run_experiment.ps1" `
  -Name "baseline_public_state" `
  -LocustFile "loadtests\locust_public_state.py" `
  -Users $Users `
  -SpawnRate $SpawnRate `
  -RunTime $RunTime `
  -UseMarkers `
  -DefensesOn:$false
