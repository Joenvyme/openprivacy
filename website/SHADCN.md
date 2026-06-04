# Site vitrine et shadcn/ui

## Stack actuelle

| Couche | Technologie |
|--------|-------------|
| Pages | HTML statique (`index.html`) |
| Styles | CSS (`styles.css`, variables type **shadcn zinc**) |
| Interactivité | JavaScript (`main.js`, `config.js`) |
| API | Vercel Serverless (`website/api/*.js`) |
| Hébergement | Vercel, dossier `website/` |

Ce n’est **pas** React ni Next.js.

## shadcn/ui, c’est quoi ?

**shadcn/ui** est une bibliothèque de composants pour **React** (souvent avec **Next.js** + **Tailwind CSS** + **TypeScript**). Ce ne sont pas des fichiers CSS à coller dans une page HTML : les composants sont copiés dans votre projet React.

Vous **ne pouvez pas** brancher shadcn tel quel sur le site actuel sans changer de stack.

## Options

1. **Rester en HTML/CSS** (actuel)  
   Variables **oklch** du thème shadcn (clair + sombre) dans `styles.css` — mode sombre via `prefers-color-scheme` ou classe `html.dark`.

2. **Migrer vers Next.js + shadcn** (recommandé si vous voulez le vrai shadcn)  
   - Créer `website-next/` ou remplacer `website/` par une app Next.js  
   - `npx shadcn@latest init` puis ajouter Button, Card, Accordion, etc.  
   - Garder les routes API Vercel (`/api/register`, …)  
   - Effort : refactor complet de la page, déploiement Vercel inchangé

3. **Astro + React islands**  
   Compromis : pages statiques + quelques composants shadcn en React.

Pour une migration Next + shadcn, demandez explicitement : on peut scaffolder l’app et reporter le contenu actuel.
