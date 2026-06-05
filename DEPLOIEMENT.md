# Déploiement — OpenPrivacy

## Site en ligne (Vercel)

Déployez le dossier `website/` sur Vercel (Git ou CLI).

### Mettre à jour le site

```bash
cd website
npx vercel deploy --prod
```

Variables et migrations : voir `LICENSE_SETUP.md`.

---

## Dépôt GitHub

```bash
gh auth login
cd /chemin/vers/votre-clone
./scripts/publish-github-prive.sh openprivacy
```

Crée `https://github.com/VOTRE_COMPTE/openprivacy` (privé si vous utilisez ce script).

### Lier Vercel ↔ GitHub

1. Vercel → votre projet → **Settings → Git**
2. Dépôt `openprivacy`, **Root Directory** : `website`

---

## Installateurs desktop

| Plateforme | Fichier distribué |
|------------|-------------------|
| Mac | `OpenPrivacy-mac.zip` (contient `OpenPrivacy.app`) |
| Windows | `OpenPrivacy-windows.zip` (contient `OpenPrivacy.exe`) |

Placez les zip dans `website/downloads/` ou GitHub Releases, puis mettez à jour `website/config.js`.

## Guides utilisateur (PDF)

Fichiers source à la racine (édition manuelle) :

| Langue | Fichier |
|--------|---------|
| Français | `GUIDE_UTILISATEUR_FR.pdf` |
| English | `USER_GUIDE_EN.pdf` |
| Deutsch | `GUIDE_BENUTZER_DE.pdf` |

Pour publier sur le site :

```bash
./scripts/sync-guide-pdf.sh
git add GUIDE_*.pdf USER_GUIDE_EN.pdf website/*.pdf
git commit -m "Mise à jour guides utilisateur PDF"
git push origin main
```

Le site affiche le PDF selon la langue (FR / EN / DE).
