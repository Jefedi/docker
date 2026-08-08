# Feuille de Mission Journalière — Format & Extraction

## Types de feuilles

### 1. Feuille de Mission Journalière (par jour)
- Format horizontal A4
- Titre: "FEUILLE DE MISSION JOURNALIÈRE"
- Champs: DATE, OPÉRATEUR, NOM DU CLIENT, LIEU DE PRESTATION, ORDRE, VÉHICULE
- Grille centrale avec colonnes: LIEU DE PRESTATION, ORDRE, VÉHICULE, CODE-BARRES, N° DOSSIER, DESCRIPTION PRESTATION
- Colonnes inférieures: CAT EMBALLAGE, DÉMARRAGE, STAT, HEURES ESTIMÉES, TEMPS PASSÉ
- Footer: Visa du salarié, TOTAL DU JOUR
- Légende gauche: PANIER, conversions temps (0h15=0.25, 0h30=0.50, 0h45=0.75)
- Note: "FEUILLE À REDONNER IMPÉRATIVEMENT EN FIN DE JOURNÉE"

### 2. Feuille Hebdomadaire par Client (par semaine)
- Une feuille par client, remplie une fois par semaine
- Marquée par numéro de semaine (ex: "semaine 32"), pas de date précise
- Contient tous les jours travaillés chez ce client dans la semaine
- Exemple: feuille SKF semaine 32 = tous les jours chez SKF du 3 au 9 août 2026
- Il faut déduire les dates à partir du numéro de semaine (ISO week → date range)

## Structure d'une journée type (exemple réel)

Journée avec 2 clients (THA + SKF):

| Heure | Activité | Durée | Type |
|-------|----------|-------|------|
| 06:40 | Départ GCA → THA | 1h10 | Trajet conducteur (sup) |
| 07:50 | Travail chez THA | 1h25 | Client (normal) |
| 09:15 | Route THA → SKF | 0h45 | Trajet conducteur (sup) |
| 10:00 | Travail chez SKF | 2h00 | Client (normal) |
| 12:00 | Pause | 0h30 | Déduite |
| 12:30 | Reprise SKF | 4h45 | Client (normal) |
| 17:15 | Route SKF → GCA | 1h45 | Trajet conducteur (sup) |
| 19:00 | Déchargement GCA | 0h30 | Boîte (normal) |
| 19:30 | Fin | — | — |

Totaux: 3h40 route conducteur, 8h10 client, 0h30 déchargement boîte

## Défi d'extraction OCR

La feuille journalière ne contient que le **dernier trajet** de la journée (ex: départ 17h15, arrivée 20h). Les autres trajets (GCA→THA, THA→SKF) et les heures chez chaque client ne sont pas sur cette feuille.

- Les feuilles hebdomadaires par client contiennent les heures chez ce client
- Il faut **corrélérer** toutes les feuilles de la semaine pour reconstituer la journée complète
- Le système doit accumuler les feuilles et proposer un récap à valider

## Workflow d'extraction adapté

1. L'utilisateur envoie une ou plusieurs photos de feuilles (journalières ou hebdomadaires)
2. Le système OCR extrait ce qu'il peut de chaque feuille
3. Le système **demande à l'utilisateur de valider** le récap extrait
4. L'utilisateur confirme ou complète les infos manquantes (trajets, heures chez d'autres clients)
5. Le système recalcule avec les infos validées

## Prompt OCR à adapter

Le prompt doit:
- Reconnaître le format "FEUILLE DE MISSION JOURNALIÈRE"
- Extraire: date, opérateur, nom client, heure de départ, heure d'arrivée, durée, activité
- Gérer le format hebdomadaire (numéro de semaine + multi-jours)
- Demander à l'utilisateur de compléter les infos manquantes (autres trajets, autres clients)
- Ne PAS inventer des données absentes de la feuille