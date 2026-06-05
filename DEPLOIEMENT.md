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

## Guide utilisateur (PDF)

Fichier source : **`GUIDE_UTILISATEUR_FR.pdf`** à la racine du dépôt (version éditée manuellement).

Pour publier sur le site :

```bash
./scripts/sync-guide-pdf.sh
git add GUIDE_UTILISATEUR_FR.pdf website/GUIDE_UTILISATEUR_FR.pdf
git commit -m "Mise à jour guide utilisateur PDF"
git push origin main
```

Le site sert **`website/GUIDE_UTILISATEUR_FR.pdf`** (copie synchronisée).
