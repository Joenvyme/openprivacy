# Guide d'Anonymisation Réversible

Ce guide explique comment utiliser les fonctionnalités d'**anonymisation** et de **dé-anonymisation** du Privacy Filter pour protéger les informations sensibles tout en conservant la possibilité de les restaurer.

## Vue d'ensemble

L'anonymisation réversible vous permet de :

1. **Anonymiser** du texte en remplaçant les informations sensibles par des placeholders
2. **Sauvegarder un mapping** qui associe chaque placeholder à sa valeur originale
3. **Dé-anonymiser** le texte ultérieurement en utilisant le mapping

Cette approche est idéale pour :
- Partager des données avec des tiers tout en conservant la capacité de restauration
- Auditer et vérifier les résultats d'anonymisation
- Créer des pipelines de traitement de données réversibles
- Tester des systèmes avec des données réalistes mais anonymisées

## Installation

Assurez-vous que le package est installé :

```bash
pip install -e .
```

## Utilisation via l'API Python

### Anonymisation basique

```python
from opf import anonymize, deanonymize

# Anonymiser du texte
text = "Contact Alice at alice@example.com or call 555-1234."
anonymized_text, mapping = anonymize(text)

print(anonymized_text)
# Output: "Contact <PRIVATE_PERSON> at <PRIVATE_EMAIL> or call <PRIVATE_PHONE>."

print(mapping.map_id)
# Output: "550e8400-e29b-41d4-a716-446655440000" (UUID unique)
```

### Sauvegarde et chargement du mapping

```python
from opf import anonymize, deanonymize
from opf._core.anonymization_map import AnonymizationMap

# Anonymiser
text = "My name is Bob and I live at 123 Main St."
anonymized_text, mapping = anonymize(text)

# Sauvegarder le mapping
mapping.save("mapping.json")

# Plus tard, charger le mapping
loaded_mapping = AnonymizationMap.load("mapping.json")

# Dé-anonymiser
original_text = deanonymize(anonymized_text, loaded_mapping)
print(original_text)
# Output: "My name is Bob and I live at 123 Main St."
```

### Utilisation avancée avec la classe OPF

```python
from opf import OPF

# Créer un redactor avec options personnalisées
opf = OPF(
    device="cpu",  # ou "cuda" pour GPU
    output_mode="typed",  # conserve les types de PII détectés
)

# Anonymiser
text = "Email: alice@company.com, Phone: +1-555-0123"
anonymized_text, mapping = opf.anonymize(text)

# Inspecter le mapping
print(f"Map ID: {mapping.map_id}")
print(f"Spans détectés: {len(mapping.spans)}")

for span in mapping.spans:
    print(f"  - {span.label}: '{span.original_text}' -> '{span.placeholder}'")

# Sauvegarder
mapping.save("email_phone_map.json")
```

### Format du mapping JSON

Le fichier de mapping contient toutes les informations nécessaires pour la restauration :

```json
{
  "map_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00.000000Z",
  "original_text": "Contact Alice at alice@example.com",
  "anonymized_text": "Contact <PRIVATE_PERSON> at <PRIVATE_EMAIL>",
  "spans": [
    {
      "label": "private_person",
      "original_text": "Alice",
      "placeholder": "<PRIVATE_PERSON>",
      "start": 8,
      "end": 13
    },
    {
      "label": "private_email",
      "original_text": "alice@example.com",
      "placeholder": "<PRIVATE_EMAIL>",
      "start": 17,
      "end": 34
    }
  ]
}
```

## Utilisation via la ligne de commande (CLI)

### Commande `anonymize`

Anonymiser du texte et sauvegarder le mapping :

```bash
# Depuis un argument
opf anonymize "Contact Alice at alice@test.com" --map-output mapping.json

# Depuis un fichier
opf anonymize -f input.txt --map-output mapping.json

# Depuis stdin
cat input.txt | opf anonymize --map-output mapping.json
```

Options disponibles :
- `--map-output` (requis) : Chemin du fichier où sauvegarder le mapping
- `--checkpoint` : Chemin vers un checkpoint personnalisé
- `--device` : cpu ou cuda (défaut: cuda)
- `-f, --text-file` : Lire depuis un fichier

### Commande `deanonymize`

Restaurer le texte original depuis un texte anonymisé :

```bash
# Depuis un argument
opf deanonymize "<PRIVATE_PERSON> works here" --map-file mapping.json

# Depuis un fichier
opf deanonymize -f anonymized.txt --map-file mapping.json

# Depuis stdin
cat anonymized.txt | opf deanonymize --map-file mapping.json
```

Options :
- `--map-file` (requis) : Chemin vers le fichier de mapping
- `-f, --text-file` : Lire depuis un fichier

### Exemple complet en CLI

```bash
# 1. Anonymiser
echo "Alice lives at 123 Main St and her email is alice@test.com" | \
  opf anonymize --map-output alice_map.json > anonymized.txt

# 2. Vérifier le résultat anonymisé
cat anonymized.txt
# Output: <PRIVATE_PERSON> lives at <PRIVATE_ADDRESS> and her email is <PRIVATE_EMAIL>

# 3. Dé-anonymiser
cat anonymized.txt | opf deanonymize --map-file alice_map.json
# Output: Alice lives at 123 Main St and her email is alice@test.com
```

## Cas d'usage

### 1. Partage de données avec des partenaires

```python
from opf import anonymize
from pathlib import Path

# Anonymiser des données sensibles avant partage
customer_data = Path("customer_feedback.txt").read_text()
anonymized_data, mapping = anonymize(customer_data)

# Partager les données anonymisées
Path("customer_feedback_anonymized.txt").write_text(anonymized_data)

# Conserver le mapping en sécurité
mapping.save("mappings/customer_feedback_map.json")
```

### 2. Audit et vérification

```python
from opf import anonymize, deanonymize
from opf._core.anonymization_map import AnonymizationMap

# Anonymiser pour audit
incident_report = "User john@company.com reported issue from IP 192.168.1.1"
anon_report, mapping = anonymize(incident_report)

# Envoyer le rapport anonymisé pour audit externe
send_to_auditor(anon_report)

# Plus tard, restaurer pour investigation interne
if requires_full_investigation():
    mapping = AnonymizationMap.load("audit_mappings/incident_123.json")
    full_report = deanonymize(anon_report, mapping)
    investigate(full_report)
```

### 3. Tests avec données de production

```python
from opf import OPF

opf = OPF(device="cpu")

# Anonymiser les données de production
prod_data = load_production_data()
test_data, mapping = opf.anonymize(prod_data)

# Utiliser les données anonymisées pour les tests
run_tests_with(test_data)

# Si un test échoue, restaurer pour déboguer
if test_failed:
    original = deanonymize(test_data, mapping)
    debug(original)
```

## Sécurité et bonnes pratiques

### Protection des mappings

⚠️ **IMPORTANT** : Les fichiers de mapping contiennent les données originales sensibles !

1. **Stockage sécurisé** : Conservez les mappings dans un emplacement sécurisé (chiffré)
2. **Contrôle d'accès** : Limitez l'accès aux mappings aux personnes autorisées uniquement
3. **Rotation** : Supprimez les anciens mappings quand ils ne sont plus nécessaires
4. **Séparation** : Ne stockez jamais les mappings avec les données anonymisées

```python
import os
from pathlib import Path

# Bon : sauvegarder dans un répertoire sécurisé
secure_dir = Path("/secure/mappings")
secure_dir.mkdir(mode=0o700, exist_ok=True)
mapping.save(secure_dir / "mapping_001.json")

# Bon : utiliser des variables d'environnement pour les chemins
mapping_dir = Path(os.environ.get("SECURE_MAPPING_DIR", "/secure/mappings"))
```

### Validation

Validez toujours que la dé-anonymisation fonctionne correctement :

```python
from opf import anonymize, deanonymize

original = "Alice works at alice@company.com"
anonymized, mapping = anonymize(original)
restored = deanonymize(anonymized, mapping)

# Vérifier que la restauration est identique
assert restored == original or restored == mapping.original_text
```

### Gestion des erreurs

```python
from opf import deanonymize
from opf._core.anonymization_map import AnonymizationMap
from pathlib import Path

def safe_deanonymize(anonymized_text, map_path):
    """Dé-anonymiser avec gestion d'erreurs."""
    try:
        if not Path(map_path).exists():
            raise FileNotFoundError(f"Mapping file not found: {map_path}")
        
        mapping = AnonymizationMap.load(map_path)
        return deanonymize(anonymized_text, mapping)
    
    except Exception as e:
        print(f"Error during deanonymization: {e}")
        return None
```

## Limitations

1. **Modifications du texte anonymisé** : Si le texte anonymisé est modifié après l'anonymisation, la dé-anonymisation peut ne pas fonctionner correctement.

2. **Ordre des placeholders** : L'algorithme de dé-anonymisation recherche les placeholders dans l'ordre inverse pour éviter les problèmes de décalage.

3. **Placeholders ambigus** : Si le même placeholder apparaît plusieurs fois, seule la première occurrence sera remplacée.

## Support et contribution

Pour signaler des bugs ou suggérer des améliorations :
- Ouvrez une issue sur le dépôt GitHub
- Consultez la [documentation principale](README.md)
- Référez-vous au [guide utilisateur](GUIDE_UTILISATEUR_FR.md)

## Licence

Cette fonctionnalité fait partie d'OpenAI Privacy Filter et est distribuée sous la licence Apache 2.0.
