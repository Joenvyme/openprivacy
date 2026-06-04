# Lance l'interface graphique en mode developpement (Windows).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
& ".\.venv\Scripts\Activate.ps1"
python -m desktop.app_gui
