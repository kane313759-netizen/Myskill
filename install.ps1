param(
  [string]$Target = "."
)

$ErrorActionPreference = "Stop"
$KitDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDst = Join-Path $Target ".agents/skills"
$KitDst = Join-Path $Target ".hackathon-kit"
$RunDst = Join-Path $KitDst "run"

New-Item -ItemType Directory -Force -Path $SkillsDst, $RunDst | Out-Null
$InstalledFile = Join-Path $RunDst "INSTALLED_SKILLS.txt"
if (-not (Test-Path $InstalledFile)) { New-Item -ItemType File -Path $InstalledFile | Out-Null }

Get-ChildItem (Join-Path $KitDir ".agents/skills") -Directory | ForEach-Object {
  $name = $_.Name
  $dst = Join-Path $SkillsDst $name
  if (Test-Path $dst) {
    Write-Warning "SKIP existing skill: $name"
  } else {
    Copy-Item -Recurse -Force $_.FullName $dst
    $known = @(Get-Content $InstalledFile -ErrorAction SilentlyContinue)
    if ($known -notcontains $name) { Add-Content -Path $InstalledFile -Value $name }
  }
}

foreach ($d in @("prompts","references","templates","scripts")) {
  $src = Join-Path $KitDir $d
  if (Test-Path $src) {
    $dst = Join-Path $KitDst $d
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    Copy-Item -Recurse -Force (Join-Path $src "*") $dst
  }
}

foreach ($f in @("EXAM_POLICY.md","BOOTSTRAP_PROMPT.md","CALLING.md","AGENTS.snippet.md")) {
  Copy-Item -Force (Join-Path $KitDir $f) (Join-Path $KitDst $f)
}

foreach ($f in @("STATE","BASELINE","GRADER","IMMUTABLES","SPEC_DRAFT","SYSTEM_MAP","CONSTRAINTS","DECISIONS","VERIFY","HANDOFF","HUMAN_JUDGMENT","EDGE_CASES","AI_FAILURES","LIMITATIONS","FOLLOWUP_CHEATSHEET")) {
  $src = Join-Path $KitDst ("templates/" + $f + ".md")
  $dst = Join-Path $RunDst ($f + ".md")
  if ((Test-Path $src) -and -not (Test-Path $dst)) { Copy-Item $src $dst }
}

$last = Join-Path $RunDst "LAST_10_MINUTES.md"
if (-not (Test-Path $last)) {
@"
# LAST 10 MINUTES

## Solved

## Changed

## Remaining risks

## Follow-up explanation points
"@ | Set-Content -Encoding UTF8 $last
}

try {
  git -C $Target rev-parse --git-dir *> $null
  if ($LASTEXITCODE -eq 0) {
    $exclude = (git -C $Target rev-parse --git-path info/exclude).Trim()
    if (-not [System.IO.Path]::IsPathRooted($exclude)) { $exclude = Join-Path (Resolve-Path $Target).Path $exclude }
    $excludeDir = Split-Path -Parent $exclude
    New-Item -ItemType Directory -Force -Path $excludeDir | Out-Null
    if (-not (Test-Path $exclude)) { New-Item -ItemType File -Path $exclude | Out-Null }
    $lines = @(Get-Content $exclude -ErrorAction SilentlyContinue)
    if ($lines -notcontains ".hackathon-kit/") { Add-Content $exclude ".hackathon-kit/" }
    Get-Content $InstalledFile | ForEach-Object {
      if ($_ -ne "") {
        $pattern = ".agents/skills/" + $_ + "/"
        $lines2 = @(Get-Content $exclude -ErrorAction SilentlyContinue)
        if ($lines2 -notcontains $pattern) { Add-Content $exclude $pattern }
      }
    }
  }
} catch {}

Write-Host "Installed AI Hackathon Starter Kit into: $Target"
Write-Host "Run notes: $RunDst"
Write-Host ""
Write-Host "Codex first prompt:"
Write-Host "Use the hackathon-orchestrator skill. Read .hackathon-kit/EXAM_POLICY.md first. Start from grader intake and baseline. Do not implement product logic until CP1 Spec Freeze closes the constraint gate."
