# Construit l'exécutable Windows pour utilisateurs finaux.
# À lancer sur une machine Windows avec Python 3.10+ installé.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = "py"
if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    $Python = "python"
}

Write-Host "==> Version Python"
& $Python --version

if (-not (Test-Path ".venv")) {
    & $Python -m venv .venv
}
& ".\.venv\Scripts\Activate.ps1"

pip install --upgrade pip
pip install -e ".[desktop]"
pip install pyinstaller

Write-Host "==> Compilation PyInstaller (10-20 min)..."
pyinstaller --noconfirm --clean packaging/openprivacy.spec

$OutDir = Join-Path $Root "dist\OpenPrivacy"
if (Test-Path $OutDir) {
    Write-Host ""
    Write-Host "Application creee : $OutDir"
    Write-Host "Lancez : $OutDir\OpenPrivacy.exe"
    Write-Host "Distribuez : Compress-Archive -> OpenPrivacy-windows.zip"
} else {
    throw "Compilation echouee : dossier $OutDir introuvable."
}
