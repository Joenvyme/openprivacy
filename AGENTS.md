# AGENTS.md

## Cursor Cloud specific instructions

### Produits dans ce dépôt

| Produit | Description | Commandes clés |
|---------|-------------|----------------|
| **OPF** (OpenAI Privacy Filter) | CLI/API Python de détection et masquage de PII | `opf`, `python -m opf` |
| **OpenPrivacy** | Distribution grand public : site statique, API licences Vercel, app bureau Tkinter | `openprivacy`, `./scripts/run-gui-dev.sh` |

### Prérequis système (une fois par VM)

- **Python 3.10+** avec le module venv : `sudo apt install python3.12-venv` (requis sur Ubuntu minimal si `python3 -m venv` échoue).
- **Node.js** (déjà présent) pour `npx vercel dev` dans `website/`.
- **Tkinter** (`python3-tk`) uniquement pour l’app bureau graphique ; absent sur les VM headless Cloud.

### Installation Python (automatique via update script)

```bash
source .venv/bin/activate   # après le premier setup
pip install -e ".[desktop]" # extra desktop = python-docx
```

Le modèle OPF (~2,8 Go) se télécharge automatiquement au premier `opf` ou `openprivacy` vers `~/.opf/privacy_filter`. Override : `OPF_CHECKPOINT=/chemin/vers/checkpoint`.

### Lint / tests

Pas de linter configuré (pas de ruff/mypy/pytest dans `pyproject.toml`).

| Commande | Rôle |
|----------|------|
| `python -m unittest desktop.test_docx_redact -v` | Tests unitaires docx (sans charger le modèle) |
| `opf --device cpu "texte avec PII"` | Smoke test redaction |
| `opf eval --device cpu examples/data/sample_eval_five_examples.jsonl` | Évaluation sur jeu d’exemple |

Utiliser `--device cpu` sur les VM sans GPU ; le défaut est `cuda` si disponible.

### Services à lancer manuellement

| Service | Commande | Port | Notes |
|---------|----------|------|-------|
| Site statique (preview) | `cd website && python3 -m http.server 8080` | 8080 | Pas d’API licences |
| API licences + site | `cd website && cp .env.example .env.local` puis `npx vercel dev` | 3000 | Nécessite `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY` |
| App bureau | `export OPENPRIVACY_API_URL=http://localhost:3000` puis `./scripts/run-gui-dev.sh` | — | Nécessite Tkinter + affichage |

### Variables d’environnement importantes

| Variable | Usage |
|----------|-------|
| `OPF_CHECKPOINT` | Chemin du checkpoint modèle |
| `OPENPRIVACY_API_URL` | URL de l’API licences (défaut prod : `https://www.openprivacy.ch`) |
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | API Vercel locale (`website/.env.local`) |

Voir `LICENSE_SETUP.md` et `README.md` pour le flux licence complet.

### Pièges connus

- Le premier lancement OPF télécharge ~2,8 Go depuis HuggingFace ; prévoir du temps et de l’espace disque.
- `scripts/run-gui-dev.sh` active `.venv` à la racine ; créer le venv avant de l’utiliser.
- Sans clés Supabase, `npx vercel dev` démarre mais `/api/register` et `/api/validate` échouent.
