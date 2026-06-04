# Déploiement — OpenPrivacy

## Site en ligne (Vercel)

**URL de production :** https://openprivacy.vercel.app

Projet Vercel : `aptiq1s-projects/openprivacy` (déploiement depuis le dossier `website/`).

### Mettre à jour le site

```bash
cd website
npx vercel deploy --prod
```

---

## Dépôt GitHub privé

```bash
gh auth login
cd "/Users/weblaw/Joenvyme/privacy filter"
./scripts/publish-github-prive.sh openprivacy
```

Crée `https://github.com/VOTRE_COMPTE/openprivacy` (privé).

### Lier Vercel ↔ GitHub

1. [Vercel → openprivacy → Settings → Git](https://vercel.com/aptiq1s-projects/openprivacy/settings/git)
2. Dépôt `openprivacy`, **Root Directory** : `website`

---

## Installateurs desktop

| Plateforme | Fichier distribué |
|------------|-------------------|
| Mac | `OpenPrivacy-mac.zip` (contient `OpenPrivacy.app`) |
| Windows | `OpenPrivacy-windows.zip` (contient `OpenPrivacy.exe`) |

Placez les zip dans `website/downloads/` ou GitHub Releases, puis mettez à jour `website/config.js`.

## Guide utilisateur (PDF)

Le site propose **`website/GUIDE_UTILISATEUR_FR.pdf`** (plus simple qu’un fichier Markdown pour les utilisateurs).

Après modification de `GUIDE_UTILISATEUR_FR.md` à la racine :

```bash
source .venv/bin/activate
pip install fpdf2
python scripts/build-guide-pdf.py
```

Puis redéployez le site (push Git ou `npx vercel deploy --prod` depuis `website/`).
