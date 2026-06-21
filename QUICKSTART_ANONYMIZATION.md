# Quick Start : Anonymisation Réversible

Guide de démarrage rapide pour utiliser l'anonymisation réversible en 5 minutes.

## 🚀 Installation

```bash
cd /workspace
pip install -e .
```

## ⚡ Premier test (30 secondes)

### Python

```python
from opf import anonymize, deanonymize

# 1. Anonymiser
text = "Contact Alice at alice@example.com"
anonymized, mapping = anonymize(text)

print(f"Original:   {text}")
print(f"Anonymisé:  {anonymized}")

# 2. Sauvegarder le mapping
mapping.save("my_mapping.json")

# 3. Restaurer
from opf._core.anonymization_map import AnonymizationMap
loaded = AnonymizationMap.load("my_mapping.json")
restored = deanonymize(anonymized, loaded)

print(f"Restauré:   {restored}")
```

### CLI

```bash
# 1. Anonymiser
echo "Alice works at alice@test.com" | \
  python3 -m opf anonymize --map-output map.json > anonymized.txt

# 2. Voir le résultat
cat anonymized.txt
# Output: <PRIVATE_PERSON> works at <PRIVATE_EMAIL>

# 3. Restaurer
cat anonymized.txt | python3 -m opf deanonymize --map-file map.json
# Output: Alice works at alice@test.com
```

## 💡 Cas d'usage communs

### 1. Partager des données sensibles

```python
from opf import anonymize
from pathlib import Path

# Lire et anonymiser
data = Path("customer_data.txt").read_text()
anonymized, mapping = anonymize(data)

# Partager les données anonymisées
Path("customer_data_safe.txt").write_text(anonymized)

# Garder le mapping en sécurité (NE PAS PARTAGER!)
mapping.save("/secure/mappings/customer_map.json")
```

### 2. Tests avec données réelles

```python
from opf import OPF

opf = OPF(device="cpu")

# Anonymiser les données de prod
prod_data = get_production_data()
test_data, mapping = opf.anonymize(prod_data)

# Tester
run_tests(test_data)

# Déboguer si nécessaire
if test_failed:
    from opf import deanonymize
    original = deanonymize(test_data, mapping)
    debug(original)
```

### 3. Pipeline de données

```bash
#!/bin/bash

# 1. Extraire les données
extract_data > raw_data.txt

# 2. Anonymiser
python3 -m opf anonymize -f raw_data.txt \
  --map-output maps/$(date +%Y%m%d).json \
  > anonymized_data.txt

# 3. Traiter
process_anonymized_data anonymized_data.txt > results.txt

# 4. Si besoin, restaurer certaines données
python3 -m opf deanonymize -f results.txt \
  --map-file maps/$(date +%Y%m%d).json \
  > final_results.txt
```

## 🔑 Commandes essentielles

### API Python

```python
# Import
from opf import anonymize, deanonymize
from opf._core.anonymization_map import AnonymizationMap

# Anonymiser
anonymized_text, mapping = anonymize("votre texte")

# Sauvegarder
mapping.save("mapping.json")

# Charger
mapping = AnonymizationMap.load("mapping.json")

# Restaurer
original = deanonymize(anonymized_text, mapping)

# Inspecter
print(f"Map ID: {mapping.map_id}")
print(f"Spans: {len(mapping.spans)}")
for span in mapping.spans:
    print(f"  {span.label}: {span.original_text}")
```

### CLI

```bash
# Aide
python3 -m opf anonymize --help
python3 -m opf deanonymize --help

# Anonymiser depuis texte
python3 -m opf anonymize "text" --map-output map.json

# Anonymiser depuis fichier
python3 -m opf anonymize -f input.txt --map-output map.json

# Anonymiser depuis stdin
echo "text" | python3 -m opf anonymize --map-output map.json

# Restaurer
python3 -m opf deanonymize "anon_text" --map-file map.json

# Restaurer depuis fichier
python3 -m opf deanonymize -f anon.txt --map-file map.json
```

## 📊 Inspecter un mapping

### Python

```python
from opf._core.anonymization_map import AnonymizationMap
import json

# Charger
mapping = AnonymizationMap.load("mapping.json")

# Afficher les informations
print(f"ID: {mapping.map_id}")
print(f"Créé: {mapping.created_at}")
print(f"Spans: {len(mapping.spans)}")

# Détails des spans
for i, span in enumerate(mapping.spans, 1):
    print(f"\nSpan {i}:")
    print(f"  Type: {span.label}")
    print(f"  Original: {span.original_text}")
    print(f"  Placeholder: {span.placeholder}")
    print(f"  Position: {span.start}-{span.end}")

# JSON complet
print("\n" + "="*50)
print(mapping.to_json(indent=2))
```

### Ligne de commande

```bash
# Lire le mapping avec jq
cat mapping.json | jq '.'

# Voir seulement les spans
cat mapping.json | jq '.spans'

# Compter les spans par type
cat mapping.json | jq '.spans | group_by(.label) | map({label: .[0].label, count: length})'
```

## ⚠️ Sécurité - 3 règles essentielles

### 1. Protéger les mappings

```bash
# BON ✅
/secure/mappings/        # Accès restreint
chmod 700 /secure/mappings
mapping.save("/secure/mappings/map.json")

# MAUVAIS ❌
/public/data/map.json    # Accessible à tous
```

### 2. Séparer données et mappings

```bash
# BON ✅
/data/anonymized/        # Données anonymisées
/secure/mappings/        # Mappings séparés

# MAUVAIS ❌
/data/both/              # Tout ensemble
```

### 3. Supprimer les anciens mappings

```python
# BON ✅
if not needed_anymore:
    Path("mapping.json").unlink()

# MAUVAIS ❌
# Garder tous les mappings indéfiniment
```

## 🐛 Dépannage

### Problème : Import error

```python
# Erreur
ImportError: No module named 'opf'

# Solution
cd /workspace
pip install -e .
```

### Problème : Model not found

```bash
# Erreur
FileNotFoundError: Checkpoint directory not found

# Solution : Le modèle sera téléchargé automatiquement
# Ou spécifier le chemin :
python3 -m opf anonymize "text" \
  --checkpoint /path/to/model \
  --map-output map.json
```

### Problème : Mapping file not found

```python
# Erreur
FileNotFoundError: /path/to/map.json

# Solution : Vérifier le chemin
from pathlib import Path
map_path = Path("map.json")
if map_path.exists():
    mapping = AnonymizationMap.load(map_path)
else:
    print(f"File not found: {map_path.absolute()}")
```

## 📚 Pour aller plus loin

- **Guide complet** : [ANONYMIZATION.md](ANONYMIZATION.md)
- **Design technique** : [TECHNICAL_DESIGN_ANONYMIZATION.md](TECHNICAL_DESIGN_ANONYMIZATION.md)
- **Exemples** : [examples/demo_anonymization.py](examples/demo_anonymization.py)
- **Tests** : [tests/test_anonymization.py](tests/test_anonymization.py)

## 🎯 Checklist rapide

Avant de déployer en production :

- [ ] Tests effectués avec vos données
- [ ] Mappings stockés en lieu sûr
- [ ] Accès aux mappings restreint
- [ ] Documentation lue et comprise
- [ ] Plan de rotation des mappings
- [ ] Backup des mappings importants
- [ ] Équipe formée à l'utilisation

## 🚀 Vous êtes prêt !

Vous savez maintenant :
- ✅ Anonymiser du texte
- ✅ Sauvegarder des mappings
- ✅ Restaurer les données
- ✅ Sécuriser les mappings
- ✅ Utiliser l'API et le CLI

**Bon anonymisation ! 🎉**
