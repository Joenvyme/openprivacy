#!/usr/bin/env bash
# Copie les guides PDF (racine) vers website/ pour le déploiement Vercel.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

copy_one() {
  local name="$1"
  local src="$ROOT/$name"
  local dst="$ROOT/website/$name"
  if [[ ! -f "$src" ]]; then
    echo "Fichier introuvable : $src" >&2
    exit 1
  fi
  cp "$src" "$dst"
  echo "✓ $name → website/ ($(du -h "$dst" | cut -f1))"
}

copy_one "GUIDE_UTILISATEUR_FR.pdf"
copy_one "USER_GUIDE_EN.pdf"
copy_one "GUIDE_BENUTZER_DE.pdf"
