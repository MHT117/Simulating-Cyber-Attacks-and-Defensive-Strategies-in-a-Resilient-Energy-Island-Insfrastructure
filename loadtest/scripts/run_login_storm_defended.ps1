param(
  [int]$Users = 40,
  [int]$SpawnRate = 10,
  [string]$RunTime = "2m"
)
& "$PSScriptRoot\run_experiment.ps1" `
  -Name "auth_login_storm_defended" `
  -LocustFile "loadtests\locust_auth_login_storm.py" `
  -Users $Users `
  -SpawnRate $SpawnRate `
  -RunTime $RunTime `
  -UseMarkers `
  -DefensesOn:$true
