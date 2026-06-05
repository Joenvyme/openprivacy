# Corriger « Service indisponible »

## 1. Vérifier le diagnostic

Ouvrez : **https://www.openprivacy.ch/api/health**

Exemple si tout va bien :

```json
{
  "ok": true,
  "supabase_configured": true,
  "supabase_ok": true
}
```

Si `"supabase_ok": false` → table manquante ou mauvaise configuration Supabase.

Pour le code HTTP exact, appelez `/api/health` avec l’en-tête `X-Health-Token` égal à `HEALTH_ADMIN_TOKEN` (variable Vercel).

## 2. Variables Vercel

| Variable | Valeur correcte |
|----------|-----------------|
| `SUPABASE_URL` | `https://VOTRE_REF.supabase.co` — **sans** `/rest/v1` à la fin |
| `SUPABASE_SERVICE_ROLE_KEY` | Clé **service_role** (onglet API, pas « anon ») |

**Pas** l’URL `db.xxx.supabase.co` — uniquement `https://xxx.supabase.co`.

## 3. Migrations SQL

Supabase → **SQL Editor** → exécuter **dans l’ordre** :

1. `supabase/migrations/20260604_openprivacy_licenses.sql`
2. `supabase/migrations/20260605_openprivacy_rate_limits.sql`
3. `supabase/migrations/20260606_openprivacy_email_verify.sql`

## 4. Redeploy Vercel

Deployments → **Redeploy** (sans cache).

## 5. Téléchargements

Les installateurs Mac/Windows peuvent être hébergés sur GitHub Releases ; mettez à jour `website/config.js` en conséquence.
