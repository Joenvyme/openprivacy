#!/usr/bin/env bash
# Lance l'interface graphique en mode développement.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source .venv/bin/activate
python -m desktop.app_gui
