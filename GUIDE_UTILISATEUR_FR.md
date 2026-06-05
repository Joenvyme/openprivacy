# OpenPrivacy.ch — Guide utilisateur

**Version 1.3.0** · Anonymisation 100 % locale sur votre ordinateur

OpenPrivacy anonymise les données personnelles dans vos textes et documents Word : noms, e-mails, téléphones, adresses, dates, etc. **Pendant l’anonymisation, rien n’est envoyé sur Internet** — seul le traitement local s’effectue sur votre machine.

---

## Téléchargement

1. Rendez-vous sur **https://www.openprivacy.ch**
2. Cliquez sur **Télécharger pour Mac** (ou récupérez le fichier fourni par votre cabinet / votre DSI).
3. Conservez le fichier **`OpenPrivacy-mac.zip`** dans un dossier que vous retrouverez facilement (Bureau, Documents…).

---

## Autoriser l’application (Mac)

OpenPrivacy est distribué **sans certificat Apple payant** (pas de signature « développeur identifié »). macOS affiche donc un avertissement de sécurité : **c’est normal** et l’application reste sûre si vous l’avez obtenue depuis **openprivacy.ch** ou une source de confiance.

### Message « impossible d’ouvrir car le développeur ne peut pas être vérifié »

**Méthode recommandée (la plus simple)**

1. **Ne double-cliquez pas** sur l’icône la première fois.
2. **Clic droit** (ou Ctrl + clic) sur **`OpenPrivacy.app`** → **Ouvrir**.
3. Dans la boîte de dialogue, cliquez à nouveau sur **Ouvrir** (et non sur Annuler).

macOS enregistre votre choix : les lancements suivants se font par un simple double-clic.

### Si l’application est toujours bloquée

1. Ouvrez **Réglages Système** → **Confidentialité et sécurité**.
2. Faites défiler jusqu’à la section **Sécurité**.
3. Si le message *« OpenPrivacy.app a été bloqué »* apparaît, cliquez sur **Ouvrir quand même**.
4. Confirmez avec votre mot de passe administrateur si demandé.

### Extraire correctement le fichier ZIP

1. Double-cliquez sur **`OpenPrivacy-mac.zip`** pour l’extraire.
2. Déplacez **`OpenPrivacy.app`** dans le dossier **Applications** (recommandé) ou laissez-le dans Documents.
3. **Ne lancez pas** l’application directement depuis l’archive ZIP sans l’avoir extraite.

---

## Autoriser l’application (Windows)

*(Quand la version Windows sera disponible.)*

Windows affiche souvent **SmartScreen** (« Windows a protégé votre PC ») pour les logiciels non signés par un éditeur reconnu. Procédez ainsi **uniquement** si vous faites confiance à la source du fichier.

### Débloquer le fichier après téléchargement

1. Clic droit sur **`OpenPrivacy-windows.zip`** → **Propriétés**.
2. En bas de l’onglet **Général**, cochez **Débloquer** si la case est présente → **OK**.
3. Extrayez le ZIP (**Extraire tout…**) dans un dossier fixe, par ex. `Documents\OpenPrivacy`.

### Contourner SmartScreen au premier lancement

1. Double-cliquez sur **`OpenPrivacy.exe`**.
2. Si une fenêtre bleue SmartScreen s’affiche : cliquez sur **Informations complémentaires**.
3. Puis sur **Exécuter quand même**.

### Si l’antivirus bloque l’exécutable

Contactez votre **service informatique** : il pourra ajouter une exception pour le dossier `OpenPrivacy` ou vérifier l’intégrité du fichier téléchargé depuis openprivacy.ch.

---

## Premier lancement

### Activation (clé gratuite)

Au premier démarrage, une fenêtre demande votre **clé d’activation** (format `OP-…`).

- Obtenez une clé sur **https://www.openprivacy.ch** (section accès).
- **Seule la clé** est vérifiée en ligne — **jamais** le contenu de vos documents.
- Une fois validée, la clé est mémorisée localement (usage hors ligne possible pendant plusieurs jours).

### Téléchargement du moteur (~3 Go)

- Une **connexion Internet** est nécessaire **une seule fois** pour télécharger le modèle d’anonymisation.
- La barre de statut en bas de la fenêtre indique la progression (« téléchargement du modèle… » puis « Prêt »).
- Comptez **10 à 30 minutes** selon votre connexion. Les lancements suivants sont rapides (quelques secondes).
- Prévoyez au moins **5 Go d’espace disque libre**.

---

## Interface (version 1.3)

L’application affiche **deux panneaux** côte à côte :

| Zone | Rôle |
|------|------|
| **Source** (gauche) | Texte ou aperçu du document à traiter |
| **Résultat** (droite) | Texte anonymisé ou confirmation Word |

**Barre d’outils**

| Bouton | Action |
|--------|--------|
| **Anonymiser** | Lance le traitement local |
| **Ouvrir…** | Choisir un fichier `.txt`, `.md`, `.docx`… |
| **Enregistrer…** | Sauvegarder le résultat |
| **Effacer** | Vider les zones de texte |

Un **badge** en haut à droite indique le mode (**Texte** ou **Word**). Les messages d’erreur ou de succès apparaissent en **notification** en bas à droite.

---

## Utilisation quotidienne

1. Lancez **OpenPrivacy** (Applications ou raccourci).
2. Attendez le statut **« Prêt »** en bas de la fenêtre.
3. **Collez** votre texte dans le panneau **Source**, ou cliquez **Ouvrir…** pour charger un fichier.
4. Cliquez **Anonymiser**.
5. Consultez le panneau **Résultat** :
   - **Texte** : cliquez **Enregistrer…** pour exporter un fichier `.txt`.
   - **Word (.docx)** : un fichier **`Nom_du_fichier_anonymise.docx`** est créé à côté de l’original ; utilisez **Enregistrer…** pour le copier ailleurs si besoin.

### Exemple

| Avant | Après |
|-------|--------|
| Me Dupont, rue du Rhône 14, 1204 Genève. Contact : dupont@cabinet-ge.ch | Me [PRIVATE_PERSON], [PRIVATE_ADDRESS]. Contact : [PRIVATE_EMAIL] |

*(Les libellés exacts varient selon le type de donnée détectée.)*

### Fichiers Word

- Formats pris en charge : **`.docx`** uniquement.
- Les anciens fichiers **`.doc`** doivent être convertis en `.docx` dans Microsoft Word.
- La mise en forme (styles, tableaux, en-têtes) est en grande partie conservée.

---

## Questions fréquentes

**Pourquoi macOS ou Windows bloque-t-il l’application ?**  
Les systèmes d’exploitation font confiance en priorité aux logiciels signés par des éditeurs enregistrés. OpenPrivacy est distribué sans cette signature commerciale ; suivez la section **Autoriser l’application** ci-dessus.

**Mes données partent-elles sur Internet ?**  
Non, pendant l’anonymisation. Seuls le **premier téléchargement du modèle** et la **vérification de la clé d’activation** utilisent Internet.

**Puis-je travailler hors ligne ?**  
Oui, après le premier téléchargement du modèle et une activation réussie (cache local de la clé).

**L’outil garantit-il la conformité RGPD ?**  
Non. C’est une **aide** à la réduction des données personnelles. Une **relecture humaine** reste recommandée pour les dossiers sensibles.

**L’application ne démarre pas**  
Vérifiez : espace disque (5 Go+), autorisation macOS/Windows (sections ci-dessus), connexion Internet au premier lancement. Notez le message d’erreur affiché et contactez votre support.

**Le bouton Anonymiser reste grisé**  
Le moteur est encore en chargement : patientez jusqu’au statut **« Prêt »** en bas de la fenêtre.

---

## Support

- Site et clé d’activation : **https://www.openprivacy.ch**
- Guide PDF : **https://www.openprivacy.ch/GUIDE_UTILISATEUR_FR.pdf**
- Pour l’installation en entreprise : contactez la personne qui vous a fourni le logiciel (cabinet, DSI, éditeur).

---

*OpenPrivacy.ch · Traitement local · OpenAI Privacy Filter (Apache 2.0)*
