Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Get-Timestamp {
  return (Get-Date).ToString("yyyyMMdd_HHmmss")
}

function Ensure-Folder([string]$Path) {
  New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Write-TextFile([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if ($dir) { Ensure-Folder $dir }
  $Content | Set-Content -Path $Path -Encoding UTF8
}

function Try-CallMarker([string]$BaseUrl, [string]$Name) {
  try {
    Invoke-RestMethod -Uri "$BaseUrl/api/mark/" -Method POST -ContentType "application/json" -Body (@{name=$Name} | ConvertTo-Json) | Out-Null
    return $true
  } catch {
    return $false
  }
}

function PromQuery([string]$PromUrl, [string]$Query) {
  $q = [System.Uri]::EscapeDataString($Query)
  return Invoke-RestMethod -Uri "$PromUrl/api/v1/query?query=$q" -Method GET
}

function Wait-HttpOk([string]$Url, [int]$TimeoutSec = 25) {
  $start = Get-Date
  while ((Get-Date) -lt $start.AddSeconds($TimeoutSec)) {
    try {
      $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
      if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { return $true }
    } catch {}
    Start-Sleep -Milliseconds 500
  }
  throw "Timeout waiting for $Url"
}
