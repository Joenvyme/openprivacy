#!/usr/bin/env bash
# Publie ce projet sur un dépôt GitHub PRIVÉ sous votre compte.
# Prérequis : gh auth login (une seule fois)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v gh &>/dev/null; then
  echo "Installez GitHub CLI : brew install gh" >&2
  exit 1
fi

if ! gh auth status &>/dev/null; then
  echo "Connectez-vous à GitHub :"
  echo "  gh auth login"
  exit 1
fi

REPO_NAME="${1:-openprivacy}"
VISIBILITY="--private"

echo "==> Création du dépôt privé : $REPO_NAME"
if gh repo view "$REPO_NAME" &>/dev/null; then
  echo "    Le dépôt existe déjà sur votre compte."
else
  gh repo create "$REPO_NAME" $VISIBILITY \
    --description "OpenPrivacy — anonymisation locale des données personnelles (OpenCaslaw)" \
    --source=. --remote=origin --push
  echo "==> Dépôt créé et code poussé."
  exit 0
fi

# Dépôt existant : mettre à jour le remote et pousser
REMOTE_URL="$(gh repo view "$REPO_NAME" --json url -q .url).git"
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE_URL"
git push -u origin main
echo "==> Poussé vers $REMOTE_URL"
