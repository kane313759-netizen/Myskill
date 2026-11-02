param([switch]$Apply)
if(-not $Apply){
  Write-Host "Dry-run only. Nothing removed."
  Write-Host "Use: .\clean.ps1 -Apply"
  exit 0
}

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $ScriptDir "../..")).Path
$Kit = Join-Path $Root ".hackathon-kit"
$Installed = Join-Path $Kit "run/INSTALLED_SKILLS.txt"

if(-not (Test-Path $Kit)){ Write-Host "No .hackathon-kit found."; exit 0 }

$backup = Join-Path $env:TEMP ("hackathon-kit-run-backup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$run = Join-Path $Kit "run"
if(Test-Path $run){ Copy-Item -Recurse -Force (Join-Path $run "*") $backup }

$names=@()
if(Test-Path $Installed){
  $names=@(Get-Content $Installed | Where-Object { $_ -ne "" })
  foreach($name in $names){
    $p=Join-Path $Root (".agents/skills/" + $name)
    if(Test-Path $p){ Remove-Item -Recurse -Force $p }
  }
}

try {
  git -C $Root rev-parse --git-dir *> $null
  if($LASTEXITCODE -eq 0){
    $exclude=(git -C $Root rev-parse --git-path info/exclude).Trim()
    if(Test-Path $exclude){
      $remove=@(".hackathon-kit/") + ($names | ForEach-Object { ".agents/skills/" + $_ + "/" })
      @(Get-Content $exclude | Where-Object { $remove -notcontains $_ }) | Set-Content -Encoding UTF8 $exclude
    }
  }
}catch{}

Remove-Item -Recurse -Force $Kit
Write-Host "Removed starter-kit helper files. Run-note backup: $backup"
