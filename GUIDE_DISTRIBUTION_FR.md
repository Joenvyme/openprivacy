# Guide de distribution — pour l’équipe technique

Ce document explique comment **fabriquer** l’installateur pour des utilisateurs non techniques (avocats, etc.) sur **macOS** et **Windows**.

---

## Principe

| Composant | Rôle |
|-----------|------|
| `desktop/app_gui.py` | Interface graphique en français (tkinter) |
| `packaging/openprivacy.spec` | Configuration PyInstaller |
| `scripts/build-mac.sh` | Build `.app` sur Mac |
| `scripts/build-windows.ps1` | Build `.exe` sur Windows |

Le **modèle (~3 Go)** n’est pas inclus dans l’installateur : il est téléchargé automatiquement au **premier lancement** dans `~/.opf/privacy_filter` (Mac/Linux) ou `%USERPROFILE%\.opf\privacy_filter` (Windows).

---

## Prérequis développeur

- **Mac** : macOS, Python 3.10+, ~15 Go d’espace disque pour le build
- **Windows** : Windows 10/11, Python 3.10+, même espace disque
- Chaque plateforme se compile **sur la machine cible** (pas de cross-compile Windows depuis Mac).

---

## Build macOS

```bash
cd "/chemin/vers/privacy filter"
chmod +x scripts/build-mac.sh scripts/run-gui-dev.sh
./scripts/build-mac.sh
```

Résultat : `dist/OpenPrivacy.app`

Distribution :

```bash
cd dist
zip -r OpenPrivacy-mac.zip OpenPrivacy.app
```

Envoyez **`OpenPrivacy-mac.zip`** + **`GUIDE_UTILISATEUR_FR.md`**.

### Signature macOS (recommandé en production)

Pour éviter l’avertissement « développeur non identifié », signez avec un certificat **Developer ID** :

```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Votre Société" \
  dist/OpenPrivacy.app
```

Puis notarisez via `xcrun notarytool` (compte Apple Developer requis).

---

## Build Windows

Sur une machine Windows, dans PowerShell :

```powershell
cd "C:\chemin\vers\privacy filter"
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build-windows.ps1
```

Résultat : dossier `dist\OpenPrivacy\` contenant `OpenPrivacy.exe`.

Distribution : compressez tout le dossier :

```powershell
Compress-Archive -Path dist\OpenPrivacy -DestinationPath OpenPrivacy-windows.zip
```

### Signature Windows (recommandé)

Signez l’exe avec un certificat de code signing (Authenticode) pour limiter les alertes SmartScreen.

---

## Test en développement (sans build)

**Mac / Linux :**

```bash
./scripts/run-gui-dev.sh
```

**Windows :**

```powershell
.\scripts\run-gui-dev.ps1
```

---

## Publier sur GitHub Releases (optionnel)

1. Créez une release (ex. `v1.0.0`).
2. Uploadez `OpenPrivacy-mac.zip` et `OpenPrivacy-windows.zip`.
3. Joignez `GUIDE_UTILISATEUR_FR.md`.
4. Lien de téléchargement simple pour les utilisateurs finaux.

---

## Taille et attentes

| Élément | Taille approximative |
|---------|---------------------|
| Installateur (zip) | 200–500 Mo (PyTorch inclus) |
| Modèle (1er lancement) | ~3 Go |
| RAM recommandée | 8 Go+ |

Le premier lancement peut prendre **10–30 minutes** (téléchargement). Prévenez les utilisateurs dans le guide.

---

## Personnalisation

- Nom affiché : `desktop/app_gui.py` → `APP_TITLE` (OpenPrivacy)
- Identifiant Mac : `packaging/openprivacy.spec` → `bundle_identifier`
- Icône : ajoutez `packaging/icon.icns` (Mac) / `packaging/icon.ico` (Windows) et référencez-les dans le `.spec`
