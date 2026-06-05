# Politique de sécurité — OpenPrivacy

## Signaler une vulnérabilité

Pour les composants **OpenPrivacy** (site, API licences, application bureau, packaging) :

- Ouvrez une issue **privée** sur le dépôt si vous y avez accès, ou contactez le mainteneur du dépôt.
- Décrivez les étapes de reproduction, l’impact et la version concernée.

Pour le moteur **OpenAI Privacy Filter** en amont :

- [Bugcrowd OpenAI](https://bugcrowd.com/openai) ou [disclosure@openai.com](mailto:disclosure@openai.com)
- [Politique de divulgation coordonnée OpenAI](https://openai.com/policies/coordinated-vulnerability-disclosure-policy/)

## Périmètre

| Composant | Données sensibles |
|-----------|-------------------|
| Application bureau / CLI `opf` | Documents traités **localement** |
| API Vercel `/api/register`, `/api/validate` | E-mail, clé `OP-…`, version app uniquement |
| Supabase `openprivacy_licenses` | Registre de clés (pas de contenu utilisateur) |

## Bonnes pratiques déploiement

- Ne jamais committer `SUPABASE_SERVICE_ROLE_KEY`, `.env.local`, certificats.
- Exécuter les trois migrations SQL du dossier `supabase/migrations/`.
- Activer **Turnstile** et **vérification e-mail (Resend)** en production (`LICENSE_SETUP.md`).
- Signer les binaires Mac (notarisation) et Windows (Authenticode) avant distribution large.
- Publier les releases sur un canal officiel unique ; vérifier les hash si vous les publiez.

## Limitations connues (hors périmètre « faille »)

- L’anonymisation ML peut laisser passer ou sur-masquer des données (voir README).
- Cache licence hors ligne : jusqu’à 7 jours après révocation.
- Sans `RESEND_API_KEY`, la clé est affichée immédiatement à l’inscription (comportement legacy).

## Historique

Consultez les releases et le changelog du dépôt pour les correctifs de sécurité publiés.
