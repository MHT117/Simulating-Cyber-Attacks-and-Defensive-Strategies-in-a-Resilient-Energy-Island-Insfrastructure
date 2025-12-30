param(
  [int]$Users = 20,
  [int]$SpawnRate = 2,
  [string]$RunTime = "2m"
)
& "$PSScriptRoot\run_experiment.ps1" `
  -Name "secure_valid_only_defended" `
  -LocustFile "loadtests\locust_secure_valid_only.py" `
  -Users $Users `
  -SpawnRate $SpawnRate `
  -RunTime $RunTime `
  -UseMarkers `
  -DefensesOn:$true
