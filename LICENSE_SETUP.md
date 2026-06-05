# OpenPrivacy — configuration licences (Supabase + Vercel)

## Ce qui est stocké

| Stocké (Supabase) | Jamais stocké |
|-------------------|---------------|
| E-mail | Texte à anonymiser |
| Clé `OP-XXXXXXXX-XXXXXXXX` | Fichiers ouverts |
| Plan (`free` / `pro`) | Résultats d’anonymisation |
| Statut, dates | Noms détectés |

## Base Supabase

1. Créez un projet sur [supabase.com](https://supabase.com).
2. Exécutez **dans l’ordre** les fichiers SQL sous `supabase/migrations/` :
   - `20260604_openprivacy_licenses.sql`
   - `20260605_openprivacy_rate_limits.sql`
   - `20260606_openprivacy_email_verify.sql`
3. RLS activée, **aucune** policy publique (accès via clé `service_role` uniquement).

## Variables Vercel (obligatoires)

Dans votre projet Vercel → **Settings → Environment Variables** :

| Variable | Valeur |
|----------|--------|
| `SUPABASE_URL` | `https://VOTRE_REF.supabase.co` (sans `/rest/v1`) |
| `SUPABASE_SERVICE_ROLE_KEY` | Clé **service_role** (Supabase → Project Settings → API) |
| `PUBLIC_SITE_URL` | URL publique du site (ex. `https://www.openprivacy.ch`) |

Ne commitez **jamais** la `service_role` dans git.

### Recommandé (production)

| Variable | Rôle |
|----------|------|
| `TURNSTILE_SECRET_KEY` | Secret Cloudflare Turnstile (anti-bot sur `/api/register`) |
| `RESEND_API_KEY` + `EMAIL_FROM` | Confirmation e-mail avant affichage de la clé |
| `HEALTH_ADMIN_TOKEN` | Détail optionnel sur `/api/health` (en-tête `X-Health-Token`) |

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

Variable optionnelle (développement uniquement) :

```bash
export OPENPRIVACY_ALLOW_API_OVERRIDE=1
export OPENPRIVACY_API_URL=https://votre-preview.vercel.app
```

## API

- `POST /api/register` — `{ "email": "...", "turnstile_token": "..." }` (si Turnstile activé)
- `GET /api/verify-email?token=...` — confirmation e-mail (si Resend activé)
- `POST /api/validate` — `{ "license_key": "OP-...", "app_version": "1.2.0" }` → `{ "valid": true, "cache_days": 7 }`
