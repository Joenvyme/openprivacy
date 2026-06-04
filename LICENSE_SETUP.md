# OpenPrivacy — configuration licences (Supabase + Vercel)

## Ce qui est stocké

| Stocké (Supabase) | Jamais stocké |
|-------------------|---------------|
| E-mail | Texte à anonymiser |
| Clé `OP-XXXXXXXX-XXXXXXXX` | Fichiers ouverts |
| Plan (`free` / `pro`) | Résultats d’anonymisation |
| Statut, dates | Noms détectés |

## Base Supabase

Migration appliquée sur le projet **Aptiq's Project** (`zzhhfwbmdisibyruuzmm`) :

- Table : `public.openprivacy_licenses`
- RLS activée, **aucune** policy publique (accès via clé service uniquement)

Fichier local : `supabase/migrations/20260604_openprivacy_licenses.sql`

## Variables Vercel (obligatoires)

Dans [Vercel → openprivacy → Settings → Environment Variables](https://vercel.com/aptiq1s-projects/openprivacy/settings/environment-variables) :

| Variable | Valeur |
|----------|--------|
| `SUPABASE_URL` | `https://zzhhfwbmdisibyruuzmm.supabase.co` (sans `/rest/v1`) |
| `SUPABASE_SERVICE_ROLE_KEY` | Clé **service_role** (Supabase → Project Settings → API) |

Ne commitez **jamais** la service role dans git.

Puis redéployez :

```bash
cd website
npx vercel deploy --prod
```

## Test local du site + API

```bash
cd website
cp .env.example .env.local   # remplir les clés
npx vercel dev
```

## Test de l’app

```bash
./scripts/run-gui-dev.sh
```

Au premier lancement : fenêtre **Activation** → coller la clé obtenue sur le site.

Variable optionnelle :

```bash
export OPENPRIVACY_API_URL=https://openprivacy.vercel.app
```

## API

- `POST /api/register` — body `{ "email": "..." }` → `{ "license_key": "OP-..." }`
- `POST /api/validate` — body `{ "license_key": "OP-...", "app_version": "1.0" }` → `{ "valid": true, "cache_days": 7 }`
