param()
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $ScriptDir "../..")).Path
$Kit = Join-Path $Root ".hackathon-kit"
$Failed = $false

function Ok($m){ Write-Host "[OK] $m" }
function Warn($m){ Write-Warning $m }
function Bad($m){ Write-Host "[FAIL] $m"; $script:Failed=$true }

foreach($f in @("EXAM_POLICY.md","run/STATE.md","run/GRADER.md","run/BASELINE.md")){
  if(Test-Path (Join-Path $Kit $f)){ Ok "$f present" } else { Bad "$f missing" }
}

$state = Join-Path $Kit "run/STATE.md"
if(Test-Path $state){
  $txt = Get-Content $state -Raw
  if($txt -match '(?i)constraint_gate:\s*CLOSED'){ Ok "constraint gate CLOSED" } else { Warn "constraint gate not recorded CLOSED" }
}

$py = $null
if(Get-Command python3 -ErrorAction SilentlyContinue){ $py="python3" }
elseif(Get-Command python -ErrorAction SilentlyContinue){ $py="python" }
if($py){
  Ok "Python available: $py"
  & $py -m py_compile (Get-ChildItem (Join-Path $Kit "scripts/*.py") | ForEach-Object FullName)
  if($LASTEXITCODE -eq 0){ Ok "Python helper syntax valid" } else { Bad "Python helper syntax error" }
}else{ Warn "Python unavailable" }

$nested = Get-ChildItem $Root -Directory -Recurse -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -eq ".git" -and $_.FullName -ne (Join-Path $Root ".git") } |
  Select-Object -First 1
if($nested){ Warn ("nested .git found: " + $nested.FullName) } else { Ok "no nested .git detected" }

try {
  git -C $Root rev-parse --git-dir *> $null
  if($LASTEXITCODE -eq 0){
    Ok "Git worktree detected"
    Write-Host ""
    Write-Host "Task git status:"
    git -C $Root status --short
  }
}catch{ Warn "not a Git worktree" }

Write-Host ""
Write-Host "If helper files must be absent, run clean.ps1 -Apply only after final-explain."
if($Failed){ exit 1 }
