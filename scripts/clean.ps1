param([switch]$Apply)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $Python) { Write-Error "Python 3.8+ is required for safe cleanup."; exit 2 }
$CleanArgs = @("-B", (Join-Path $ScriptDir "kit_lifecycle.py"), "clean", "--kit", (Join-Path $ScriptDir ".."))
if ($Apply) { $CleanArgs += "--apply" }
& $Python.Source @CleanArgs
exit $LASTEXITCODE
