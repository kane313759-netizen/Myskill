param([switch]$PreSubmit)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $Python) { Write-Error "Python 3.8+ is required for doctor."; exit 2 }
$DoctorArgs = @("-B", (Join-Path $ScriptDir "kit_lifecycle.py"), "doctor", "--kit", (Join-Path $ScriptDir ".."))
if ($PreSubmit) { $DoctorArgs += "--pre-submit" }
& $Python.Source @DoctorArgs
exit $LASTEXITCODE
