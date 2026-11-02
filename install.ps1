param(
  [string]$Target = "."
)

$ErrorActionPreference = "Stop"
$KitDir = Split-Path -Parent $MyInvocation.MyCommand.Path

New-Item -ItemType Directory -Force -Path (Join-Path $Target ".agents/skills") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Target ".hackathon-kit") | Out-Null

Copy-Item -Recurse -Force (Join-Path $KitDir ".agents/skills/*") (Join-Path $Target ".agents/skills")

foreach ($d in @("prompts","references","templates","scripts")) {
  $src = Join-Path $KitDir $d
  if (Test-Path $src) {
    $dst = Join-Path $Target (".hackathon-kit/" + $d)
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    Copy-Item -Recurse -Force (Join-Path $src "*") $dst
  }
}

Copy-Item -Force (Join-Path $KitDir "BOOTSTRAP_PROMPT.md") (Join-Path $Target ".hackathon-kit/BOOTSTRAP_PROMPT.md")
Copy-Item -Force (Join-Path $KitDir "CALLING.md") (Join-Path $Target ".hackathon-kit/CALLING.md")
Copy-Item -Force (Join-Path $KitDir "AGENTS.snippet.md") (Join-Path $Target ".hackathon-kit/AGENTS.snippet.md")

Write-Host "Installed AI Hackathon Starter Kit into: $Target"
Write-Host ""
Write-Host "Codex first prompt:"
Write-Host "Use the hackathon-orchestrator skill. Start from Phase 0. Keep Terra as orchestrator, create one persistent Sol 6.1 MAIN BUILDER, and let that MAIN own specification through implementation. Do not implement until the constraint gate is complete."
