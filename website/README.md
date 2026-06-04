# OpenPrivacy — page web

Site vitrine statique pour présenter **OpenPrivacy** et proposer les téléchargements Mac / Windows.

## Prévisualisation locale

```bash
cd website
python3 -m http.server 8080
```

Ouvrez [http://localhost:8080](http://localhost:8080).

## Fichiers de téléchargement

Après avoir compilé les installateurs (`scripts/build-mac.sh` et `scripts/build-windows.ps1`), copiez les zip ici :

```
website/downloads/OpenPrivacy-mac.zip
website/downloads/OpenPrivacy-windows.zip
```

## Publier en ligne

### GitHub Pages (gratuit)

1. Poussez le dépôt sur GitHub.
2. **Settings → Pages → Source** : branche `main`, dossier `/website`.
3. Le site sera disponible à `https://VOTRE_USER.github.io/VOTRE_REPO/`.

Pour les gros fichiers zip (>100 Mo), utilisez **GitHub Releases** et mettez à jour `config.js` :

```javascript
window.SITE_CONFIG = {
  downloadMac:
    "https://github.com/VOTRE_ORG/privacy-filter/releases/latest/download/OpenPrivacy-mac.zip",
  downloadWindows:
    "https://github.com/VOTRE_ORG/privacy-filter/releases/latest/download/OpenPrivacy-windows.zip",
  releasesPage:
    "https://github.com/VOTRE_ORG/privacy-filter/releases",
};
```

### Autres hébergeurs

- **Netlify / Vercel** : déployez le dossier `website/` en site statique.
- **Hébergement cabinet** : uploadez le contenu de `website/` + le dossier `downloads/`.

## Personnalisation

| Fichier | Contenu |
|---------|---------|
| `index.html` | Textes, structure |
| `styles.css` | Apparence |
| `config.js` | URLs de téléchargement |
