# Corriger « Service indisponible »

## 1. Vérifier le diagnostic

Ouvrez : **https://www.openprivacy.ch/api/health**

Exemple si tout va bien :

```json
{
  "supabase_ok": true,
  "supabase_host": "zzhhfwbmdisibyruuzmm.supabase.co"
}
```

Si `"supabase_ok": false` et `"supabase_status": 404` → la table n’existe pas sur **le projet indiqué par `supabase_host`**.

## 2. Variables Vercel (projet **openprivacy**)

| Variable | Valeur correcte |
|----------|-----------------|
| `SUPABASE_URL` | `https://VOTRE_REF.supabase.co` — **sans** `/rest/v1` à la fin |
| `SUPABASE_SERVICE_ROLE_KEY` | Clé **service_role** (onglet API, pas « anon ») |

**Pas** l’URL `db.xxx.supabase.co` — uniquement `https://xxx.supabase.co`.

## 3. Créer la table

Supabase → votre projet (même REF que `supabase_host`) → **SQL Editor** → coller le fichier :

`supabase/migrations/20260604_openprivacy_licenses.sql`

→ **Run**.

## 4. Redeploy Vercel

Deployments → **Redeploy** (sans cache).

## 5. Téléchargements

Les installateurs Mac/Windows ne sont pas encore en ligne volontairement. Message « Bientôt » sur le site = normal.
