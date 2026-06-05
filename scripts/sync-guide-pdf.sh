#!/usr/bin/env bash
# Copie le guide PDF source (racine) vers website/ pour le déploiement Vercel.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/GUIDE_UTILISATEUR_FR.pdf"
DST="$ROOT/website/GUIDE_UTILISATEUR_FR.pdf"

if [[ ! -f "$SRC" ]]; then
  echo "Fichier introuvable : $SRC" >&2
  exit 1
fi

cp "$SRC" "$DST"
echo "✓ Guide copié : website/GUIDE_UTILISATEUR_FR.pdf ($(du -h "$DST" | cut -f1))"
