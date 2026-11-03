param([string]$Target = ".", [switch]$AllowInternalSource)
$ErrorActionPreference = "Stop"
$KitDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $Python) { Write-Error "Python 3.8+ is required; nothing installed."; exit 2 }
$InstallArgs = @("-B", (Join-Path $KitDir "scripts/kit_lifecycle.py"), "install", "--source", $KitDir, "--target", $Target)
if ($AllowInternalSource) { $InstallArgs += "--allow-internal-source" }
& $Python.Source @InstallArgs
exit $LASTEXITCODE
