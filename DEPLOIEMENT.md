# Déploiement — GitHub privé + Vercel

## Site en ligne (Vercel)

**URL de production :** https://website-six-flame-48.vercel.app

Projet Vercel : `aptiq1s-projects/website` (déploiement depuis le dossier `website/` uniquement).

### Mettre à jour le site

```bash
cd website
npx vercel deploy --prod
```

### Nom de domaine plus parlant (optionnel)

Dans le [tableau de bord Vercel](https://vercel.com/aptiq1s-projects/website/settings/domains), ajoutez un alias du type `filtre-confidentialite.vercel.app` (si disponible sur votre compte).

---

## Dépôt GitHub privé

Le dépôt local pointe encore vers `openai/privacy-filter` en remote. Pour publier **sur votre compte en privé** :

### 1. Connexion GitHub (une fois)

```bash
gh auth login
```

Choisissez : GitHub.com → HTTPS → Oui pour Git Credential Manager → connexion navigateur.

### 2. Publication

```bash
cd "/Users/weblaw/Joenvyme/privacy filter"
./scripts/publish-github-prive.sh filtre-confidentialite
```

Cela crée `https://github.com/VOTRE_COMPTE/filtre-confidentialite` (privé) et y pousse le code.

### 3. Lier Vercel ↔ GitHub (optionnel)

1. [Vercel → website → Settings → Git](https://vercel.com/aptiq1s-projects/website/settings/git)
2. Connectez votre dépôt privé `filtre-confidentialite`
3. **Root Directory** : `website`
4. Chaque `git push` redéploiera le site automatiquement

---

## Fichiers volumineux

Ne commitez **pas** les zip d’installateurs (>100 Mo). Utilisez [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) et mettez à jour `website/config.js`.
