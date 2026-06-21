# Design Technique : Anonymisation Réversible

## Vue d'ensemble

Ce document décrit l'architecture technique de la fonctionnalité d'anonymisation réversible ajoutée à OpenAI Privacy Filter.

## Architecture

### Composants principaux

```
┌─────────────────────────────────────────────────────────────┐
│                         API Publique                        │
│  anonymize(), deanonymize(), OPF.anonymize()               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     Core Runtime                            │
│  predict_text() → DetectedSpan[]                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  AnonymizationMap                           │
│  - Stockage des mappings                                    │
│  - Sérialisation JSON                                       │
│  - Logique de restauration                                  │
└─────────────────────────────────────────────────────────────┘
```

## Flux de données

### Anonymisation

```
Texte Original
    │
    ▼
[Privacy Filter Model] ──► DetectedSpan[]
    │                         │
    │                         ├─ label
    │                         ├─ start/end
    │                         ├─ text
    │                         └─ placeholder
    │
    ▼
Texte Anonymisé ◄────────── _redact_text()
    │
    ▼
AnonymizationMap {
  map_id: UUID
  original_text: string
  anonymized_text: string
  spans: SpanMapping[]
}
```

### Dé-anonymisation

```
Texte Anonymisé + AnonymizationMap
    │
    ▼
deanonymize_text()
    │
    ├─ Trie les spans (ordre inverse)
    │
    ├─ Pour chaque span:
    │   ├─ Cherche le placeholder
    │   └─ Remplace par original_text
    │
    ▼
Texte Original Restauré
```

## Structures de données

### AnonymizationMap

```python
@dataclass
class AnonymizationMap:
    map_id: str              # UUID unique
    created_at: str          # ISO 8601 timestamp
    original_text: str       # Texte complet original
    anonymized_text: str     # Texte complet anonymisé
    spans: list[SpanMapping] # Liste des spans détectés
```

### SpanMapping

```python
@dataclass
class SpanMapping:
    label: str          # Type de PII (ex: "private_email")
    original_text: str  # Valeur originale (ex: "alice@test.com")
    placeholder: str    # Placeholder utilisé (ex: "<PRIVATE_EMAIL>")
    start: int          # Position de début dans le texte original
    end: int            # Position de fin dans le texte original
```

### RedactionResult (étendu)

```python
@dataclass(frozen=True)
class RedactionResult:
    # ... champs existants ...
    anonymization_map: AnonymizationMap | None = None  # Nouveau champ
```

## API

### Fonctions publiques

#### `anonymize(text: str) -> tuple[str, AnonymizationMap]`

Anonymise du texte et retourne le mapping réversible.

**Paramètres:**
- `text`: Texte à anonymiser

**Retourne:**
- Tuple de (texte_anonymisé, mapping)

**Exemple:**
```python
anonymized, mapping = anonymize("Alice at alice@test.com")
```

#### `deanonymize(anonymized_text: str, mapping: AnonymizationMap) -> str`

Restaure le texte original depuis un texte anonymisé.

**Paramètres:**
- `anonymized_text`: Texte anonymisé
- `mapping`: Mapping d'anonymisation

**Retourne:**
- Texte original restauré

**Exemple:**
```python
original = deanonymize("<PRIVATE_PERSON> at <PRIVATE_EMAIL>", mapping)
```

### Méthodes de classe

#### `OPF.anonymize(text: str, *, decode: DecodeOptions | None = None) -> tuple[str, AnonymizationMap]`

Version méthode de l'anonymisation avec options de configuration.

**Paramètres:**
- `text`: Texte à anonymiser
- `decode`: Options de décodage optionnelles

**Retourne:**
- Tuple de (texte_anonymisé, mapping)

### Sérialisation

#### `AnonymizationMap.save(path: str | Path) -> None`

Sauvegarde le mapping dans un fichier JSON.

#### `AnonymizationMap.load(path: str | Path) -> AnonymizationMap`

Charge un mapping depuis un fichier JSON.

#### `AnonymizationMap.to_json(*, indent: int | None = 2) -> str`

Sérialise en JSON string.

#### `AnonymizationMap.from_json(json_str: str) -> AnonymizationMap`

Désérialise depuis JSON string.

## CLI

### Commande `anonymize`

```bash
opf anonymize [TEXT] --map-output FILE [OPTIONS]
```

**Arguments:**
- `TEXT`: Texte à anonymiser (optionnel, peut venir de stdin)
- `--map-output FILE`: Chemin du fichier de mapping (requis)
- `-f FILE`: Lire depuis un fichier
- Options standard de redaction (--device, --checkpoint, etc.)

### Commande `deanonymize`

```bash
opf deanonymize [TEXT] --map-file FILE [OPTIONS]
```

**Arguments:**
- `TEXT`: Texte anonymisé (optionnel, peut venir de stdin)
- `--map-file FILE`: Chemin du fichier de mapping (requis)
- `-f FILE`: Lire depuis un fichier

## Algorithme de dé-anonymisation

### Approche

L'algorithme de dé-anonymisation utilise une stratégie de remplacement en ordre inverse pour éviter les problèmes de décalage d'offset :

```python
def deanonymize_text(anonymized_text: str, mapping: AnonymizationMap) -> str:
    # 1. Trier les spans par position de départ (ordre inverse)
    sorted_spans = sorted(mapping.spans, key=lambda s: s.start, reverse=True)
    
    result = anonymized_text
    
    # 2. Remplacer chaque placeholder par l'original
    for span in sorted_spans:
        placeholder_pos = result.find(span.placeholder)
        if placeholder_pos != -1:
            result = (
                result[:placeholder_pos] 
                + span.original_text 
                + result[placeholder_pos + len(span.placeholder):]
            )
    
    return result
```

### Avantages de cette approche

1. **Simple et robuste** : Pas besoin de recalculer les offsets
2. **Ordre inverse** : Évite les problèmes de décalage lors des remplacements
3. **Recherche de placeholder** : Trouve le placeholder même si les positions ont changé
4. **Gestion d'erreurs** : Continue même si un placeholder n'est pas trouvé

### Limitations

1. **Modifications du texte** : Si le texte anonymisé est modifié, la restauration peut échouer
2. **Placeholders ambigus** : Si le même placeholder apparaît plusieurs fois, seule la première occurrence est remplacée
3. **Ordre important** : L'ordre inverse est crucial pour la correction

## Considérations de sécurité

### Stockage des mappings

⚠️ **CRITIQUE** : Les mappings contiennent les données sensibles originales !

**Bonnes pratiques :**

1. **Chiffrement au repos**
   ```python
   # Bon : Utiliser un système de fichiers chiffré
   mapping.save("/secure/encrypted/mappings/map.json")
   ```

2. **Contrôle d'accès**
   ```python
   import os
   from pathlib import Path
   
   # Permissions restrictives
   map_dir = Path("/secure/mappings")
   map_dir.mkdir(mode=0o700, exist_ok=True)
   ```

3. **Séparation des données**
   ```bash
   # Bon : Séparer les données et les mappings
   /data/anonymized/     # Données anonymisées
   /secure/mappings/     # Mappings (accès restreint)
   
   # Mauvais : Tout ensemble
   /data/both/          # ❌ Ne jamais faire ça
   ```

4. **Rotation et expiration**
   ```python
   # Supprimer les anciens mappings
   if mapping_age > MAX_AGE:
       mapping_file.unlink()
   ```

### Audit trail

Le champ `created_at` permet de tracer quand un mapping a été créé :

```python
mapping = AnonymizationMap.load("map.json")
print(f"Mapping créé le : {mapping.created_at}")
```

## Tests

### Structure des tests

```
tests/test_anonymization.py
├─ TestAnonymizationMap
│  ├─ test_create_empty_map()
│  ├─ test_add_span()
│  ├─ test_to_dict()
│  ├─ test_to_json()
│  ├─ test_from_dict()
│  ├─ test_from_json()
│  └─ test_save_and_load()
│
├─ TestAnonymizationAPI
│  ├─ test_anonymize_simple_text()
│  ├─ test_deanonymize_text()
│  └─ test_opf_anonymize_method()
│
└─ TestEndToEndAnonymization
   ├─ test_full_anonymize_deanonymize_cycle()
   ├─ test_multiple_spans()
   └─ test_no_pii_text()
```

### Exécution des tests

```bash
# Tous les tests d'anonymisation
pytest tests/test_anonymization.py -v

# Test spécifique
pytest tests/test_anonymization.py::TestAnonymizationMap::test_save_and_load -v
```

## Performance

### Complexité

- **Anonymisation** : O(n) où n = longueur du texte
  - Dépend du modèle Privacy Filter
  - Pas de surcharge significative

- **Dé-anonymisation** : O(m × p) où :
  - m = nombre de spans
  - p = longueur moyenne du texte
  - Généralement très rapide pour un usage normal

### Optimisations possibles

1. **Cache de mappings** : Pour éviter de recharger
2. **Batch processing** : Traiter plusieurs textes en parallèle
3. **Index de placeholders** : Pour recherche plus rapide

## Extensions futures

### Fonctionnalités envisageables

1. **Chiffrement intégré**
   ```python
   mapping.save_encrypted("map.json", key=encryption_key)
   mapping = AnonymizationMap.load_encrypted("map.json", key=encryption_key)
   ```

2. **Versioning des mappings**
   ```python
   mapping_v1 = AnonymizationMap(version="1.0")
   mapping_v2 = mapping_v1.evolve(version="2.0")
   ```

3. **Multiples formats d'export**
   ```python
   mapping.to_csv()
   mapping.to_xml()
   mapping.to_parquet()
   ```

4. **Statistiques et métriques**
   ```python
   stats = mapping.get_statistics()
   # {
   #   "total_spans": 5,
   #   "by_label": {"private_email": 2, "private_person": 3},
   #   "avg_span_length": 12.4
   # }
   ```

## Compatibilité

### Backward compatibility

✅ **100% compatible** avec l'API existante :
- `redact()` fonctionne comme avant
- `RedactionResult` accepte `anonymization_map=None`
- Pas de breaking changes

### Forward compatibility

- Le format JSON est extensible
- Nouveaux champs peuvent être ajoutés sans casser la compatibilité
- Versioning possible via le champ `schema_version`

## Références

- [ANONYMIZATION.md](ANONYMIZATION.md) - Guide utilisateur
- [README.md](README.md) - Documentation principale
- [tests/test_anonymization.py](tests/test_anonymization.py) - Suite de tests
- [examples/demo_anonymization.py](examples/demo_anonymization.py) - Démos
