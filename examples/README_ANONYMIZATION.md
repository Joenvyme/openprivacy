# Exemples d'Anonymisation

Ce dossier contient des exemples pratiques d'utilisation de la fonctionnalité d'anonymisation réversible.

## Script de démonstration

### `demo_anonymization.py`

Script complet démontrant toutes les fonctionnalités :

```bash
python3 examples/demo_anonymization.py
```

Ce script montre :
- Anonymisation basique
- Sauvegarde et chargement de mappings
- Gestion de multiples types de PII
- Comportement avec du texte sans PII

## Exemples rapides

### Exemple 1 : Usage basique

```python
from opf import anonymize, deanonymize

# Anonymiser
text = "Contact Alice at alice@example.com"
anonymized, mapping = anonymize(text)

print(f"Original: {text}")
print(f"Anonymisé: {anonymized}")

# Sauvegarder le mapping
mapping.save("example_map.json")

# Dé-anonymiser
from opf._core.anonymization_map import AnonymizationMap
loaded = AnonymizationMap.load("example_map.json")
restored = deanonymize(anonymized, loaded)

print(f"Restauré: {restored}")
```

### Exemple 2 : Avec la classe OPF

```python
from opf import OPF

# Créer un redactor avec options
opf = OPF(device="cpu", output_mode="typed")

# Anonymiser
text = "Bob works at bob@company.com, phone: 555-1234"
anonymized, mapping = opf.anonymize(text)

# Inspecter les spans détectés
print(f"Détecté {len(mapping.spans)} span(s):")
for span in mapping.spans:
    print(f"  - {span.label}: '{span.original_text}'")
```

### Exemple 3 : CLI

```bash
# Anonymiser depuis stdin
echo "Alice at alice@test.com" | python3 -m opf anonymize --map-output map.json

# Ou depuis un argument
python3 -m opf anonymize "Alice at alice@test.com" --map-output map.json

# Dé-anonymiser
python3 -m opf deanonymize "<PRIVATE_PERSON> at <PRIVATE_EMAIL>" --map-file map.json
```

### Exemple 4 : Pipeline complet

```bash
# 1. Anonymiser un fichier
python3 -m opf anonymize -f customer_data.txt --map-output customer_map.json > customer_anonymized.txt

# 2. Traiter les données anonymisées
process_data customer_anonymized.txt

# 3. Si besoin, restaurer
python3 -m opf deanonymize -f customer_anonymized.txt --map-file customer_map.json > customer_restored.txt
```

## Structure d'un mapping JSON

```json
{
  "map_id": "unique-uuid-here",
  "created_at": "2024-01-01T12:00:00.000000Z",
  "original_text": "Alice at alice@test.com",
  "anonymized_text": "<PRIVATE_PERSON> at <PRIVATE_EMAIL>",
  "spans": [
    {
      "label": "private_person",
      "original_text": "Alice",
      "placeholder": "<PRIVATE_PERSON>",
      "start": 0,
      "end": 5
    },
    {
      "label": "private_email",
      "original_text": "alice@test.com",
      "placeholder": "<PRIVATE_EMAIL>",
      "start": 9,
      "end": 23
    }
  ]
}
```

## Notes importantes

⚠️ **Sécurité** : Les fichiers de mapping contiennent les données sensibles originales !
- Stockez-les dans un emplacement sécurisé
- Ne les partagez jamais avec les données anonymisées
- Utilisez un chiffrement au repos

📖 **Documentation complète** : Voir [ANONYMIZATION.md](../ANONYMIZATION.md) pour plus de détails
