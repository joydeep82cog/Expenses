$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$mainFile = Join-Path $projectRoot "main.py"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Missing virtual environment interpreter at $pythonExe"
    Write-Output "Create it with Python 3.12:"
    Write-Output "  python -m venv .venv"
    exit 1
}

if (-not (Test-Path $mainFile)) {
    Write-Error "Could not find $mainFile"
    exit 1
}

# Use ANGLE by default to avoid OpenGL 2.0 driver issues on some Windows setups.
if (-not $env:KIVY_GL_BACKEND) {
    $env:KIVY_GL_BACKEND = "angle_sdl2"
}

& $pythonExe $mainFile
exit $LASTEXITCODE
