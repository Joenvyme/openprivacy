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

Le site peut proposer **`website/GUIDE_UTILISATEUR_FR.pdf`**.

Après modification de `GUIDE_UTILISATEUR_FR.md` à la racine :

```bash
source .venv/bin/activate
pip install fpdf2
python scripts/build-guide-pdf.py
```

Puis redéployez le site (push Git ou `npx vercel deploy --prod` depuis `website/`).
