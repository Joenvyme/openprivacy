# Guide de création de la release Windows

Ce guide explique comment créer et publier une release Windows pour OpenPrivacy.

## Prérequis

- Le workflow GitHub Actions `release-windows.yml` doit être présent dans la branche `main`
- Une release GitHub doit déjà exister pour la version cible (ex: `v1.3.1`)

## Étapes pour créer la release Windows

### 1. Déclencher le workflow

1. Aller sur GitHub : https://github.com/Joenvyme/openprivacy/actions
2. Dans la liste des workflows à gauche, cliquer sur **"Build Windows Release"**
3. Cliquer sur le bouton **"Run workflow"** (en haut à droite)
4. Remplir les paramètres :
   - **version** : le numéro de version (ex: `1.3.1`)
   - **release_tag** : le tag de la release (ex: `v1.3.1`)
   - **update_latest** : cocher si c'est la version la plus récente
5. Cliquer sur **"Run workflow"** pour lancer le build

### 2. Suivi du build

Le workflow va :
- Builder l'application Windows avec PyInstaller (~10-20 minutes)
- Créer l'archive `OpenPrivacy-windows.zip`
- L'uploader sur la release GitHub existante
- Mettre à jour `website/versions.json` avec le lien de téléchargement
- Commiter les changements sur la branche `main`

Vous pouvez suivre la progression dans l'onglet Actions.

### 3. Vérification

Une fois le workflow terminé :

1. **Vérifier la release GitHub** : https://github.com/Joenvyme/openprivacy/releases/tag/v1.3.1
   - Le fichier `OpenPrivacy-windows.zip` doit être présent

2. **Vérifier le site web** : https://openprivacy.ch
   - Le bouton de téléchargement Windows doit être actif
   - Le texte doit afficher "Télécharger pour Windows" au lieu de "Bientôt — Windows"
   - La notice "Installateur Windows en cours de préparation" doit être masquée

3. **Vérifier versions.json** : https://github.com/Joenvyme/openprivacy/blob/main/website/versions.json
   - La propriété `downloads.windows` doit contenir l'URL de téléchargement

## Dépannage

### Le workflow échoue pendant le build

- Vérifier les logs dans l'onglet Actions
- Les erreurs courantes incluent :
  - Dépendances manquantes : vérifier `pyproject.toml`
  - Erreurs PyInstaller : vérifier `packaging/openprivacy.spec`

### Le fichier n'est pas uploadé sur la release

- Vérifier que la release existe déjà avec le bon tag
- Vérifier les permissions du token GitHub Actions

### Le site web ne montre pas le téléchargement Windows

- Vérifier que `versions.json` a été correctement mis à jour
- Vider le cache du navigateur
- Vérifier la console JavaScript pour des erreurs

## Build local (optionnel)

Pour tester le build localement sur une machine Windows :

```powershell
cd C:\chemin\vers\openprivacy
.\scripts\build-windows.ps1
```

Le résultat sera dans `dist\OpenPrivacy\OpenPrivacy.exe`.

Pour créer l'archive :

```powershell
Compress-Archive -Path dist\OpenPrivacy -DestinationPath OpenPrivacy-windows.zip
```
