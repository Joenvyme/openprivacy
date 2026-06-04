#!/usr/bin/env bash
# Construit l'application macOS (.app) pour distribution aux utilisateurs finaux.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3.10}"
if ! command -v "$PYTHON" &>/dev/null; then
  PYTHON=python3
fi

echo "==> Environnement Python : $($PYTHON --version)"

if [[ ! -d .venv ]]; then
  "$PYTHON" -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate

pip install --upgrade pip
pip install -e ".[desktop]"
pip install pyinstaller

echo "==> Compilation PyInstaller (peut prendre 10–20 min)…"
pyinstaller --noconfirm --clean packaging/openprivacy.spec

APP="dist/OpenPrivacy.app"
if [[ -d "$APP" ]]; then
  echo ""
  echo "✓ Application créée : $ROOT/$APP"
  echo "  Pour tester : open \"$APP\""
  echo "  Pour distribuer : zip -r OpenPrivacy-mac.zip OpenPrivacy.app"
else
  echo "Erreur : $APP introuvable après la compilation." >&2
  exit 1
fi
