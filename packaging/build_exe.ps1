# Builds dist\CrumbsPicnicRun.exe: a single-file Windows executable with Python, the game and its fonts inside.
# Run from the project root:  powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

uv run python packaging\make_icon.py packaging\crumb.ico

uv run pyinstaller `
    --noconfirm --clean `
    --onefile --windowed `
    --name CrumbsPicnicRun `
    --icon packaging\crumb.ico `
    --add-data "src\crumb\assets;crumb\assets" `
    --collect-all sounddevice `
    --distpath dist --workpath build `
    packaging\run_crumb.py

Write-Host "Built dist\CrumbsPicnicRun.exe"
