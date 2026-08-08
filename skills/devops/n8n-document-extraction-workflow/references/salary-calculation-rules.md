# Règles de Calcul Salaire — Timesheet Automation

## Taux Horaire (par période)

| Période | Taux horaire |
|---|---|
| Avant juillet 2026 | 12,50 €/h |
| Juillet 2026 | 12,80 €/h |
| À partir du 3 août 2026 | 13,00 €/h |

Reste à 13€ jusqu'à changement communiqué par l'utilisateur.

## Trajets

- **Conducteur** → payé au taux route (= taux horaire × 1,25, majoration 25%)
- **Passager** → payé au taux horaire normal (pas de majoration)
- Aller-retour client/chantier = payé (cumulé, total sur la feuille)
- Les feuilles précisent toujours heures conducteur vs heures passager
- Pas de règle de "3e trajet" — tous les trajets sont payés dès le premier

## Taux Route / Heures Sup / Conducteur

Le taux route = taux normal × 1,25 (majoration 25%). C'est le MÊME taux pour :
- Heures de trajet conducteur
- Heures supplémentaires (au-delà de 35h/semaine)

| Période | Taux normal | Taux route/sup (+25%) |
|---------|-------------|----------------------|
| Avant juillet 2026 | 12,50 € | 15,63 € |
| Juillet 2026 | 12,80 € | 16,00 € |
| Dès 3 août 2026 | 13,00 € | 16,25 € |

## Prime de 13e Mois

- **1,07 €** par heure normale (fixe)
- Calculée sur les heures normales uniquement (pas sur les heures de route)
- Exemple : 35h normales × 1,07€ = 37,45€

## Panier (indemnité de repas)

- **19 €** par jour chez le client uniquement
- Pas de panier quand on est à la boîte

## Ticket Restaurant

- Uniquement à la boîte
- Montant exact à confirmer avec l'utilisateur

## Types de Journée

1. **Journée boîte** — travail à l'entreprise, pas de panier, ticket resto
2. **Journée client** — travail chez un client, panier 19€, trajets conducteur/passager
3. **Journée mixte** — boîte le matin + déplacement client + retour boîte

## Format Récap (comme appli boîte)

```
Semaine du [date] au [date]
- Heures de route : [h_cond] × [taux_sup]€ = [montant]€
- Heures normales : [h_normales] × [taux_normal]€ = [montant]€
- Heures supp. 25% : [h_sup_equivalent] × [taux_sup]€ = [montant]€
- Prime de 13e mois : [h_normales] × 1,07€ = [montant]€
Total brut : [total]€
```

## Calcul Quotidien

```
taux = getTauxHoraire(date)  // selon période
tauxSup = taux × 1,25
hNormal = h_boite + h_client
salaireRoute = h_conducteur × tauxSup
salairePassager = h_passager × taux
salaireNormal = hNormal × taux
hSupEquivalent = max(0, (hNormal - 35)) × 1,25  // heures sup au-delà de 35h/semaine
salaireSup = hSupEquivalent × tauxSup
panier = (type_journee !== 'boîte') ? 19 : 0
prime13e = hNormal × 1,07
salaireTotal = salaireNormal + salaireRoute + salairePassager + salaireSup + panier + prime13e
```

Note: Le calcul des heures sup dépend du cumul hebdomadaire. Pour la v1, simplifier en traitant tout trajet conducteur comme des heures à 25%. Affiner avec le cumul semaine en v2.

## Workflow de Confirmation

1. L'utilisateur envoie la photo de la feuille
2. Le système extrait les données via OCR
3. Le système affiche les données extraites et demande confirmation
4. L'utilisateur confirme ou corrige
5. Les données confirmées sont stockées et archivées

## Notes

- Le nom de la boîte apparaît sur les feuilles journalières
- L'utilisateur précise au fur et à mesure les détails (nom client, etc.)
- Certaines feuilles peuvent ne pas avoir toutes les infos — le système demande à l'utilisateur de compléter
- L'écriture peut être difficile à lire — la confirmation humaine est obligatoire
- Output souhaité: résumé quotidien (pas mensuel)

## Règles de Pointage Manuel (dictation → calcul)

L'utilisateur dicte souvent ses heures de la semaine verbalement. Règles de calcul depuis dictation:

1. **Arrivée boîte ≠ temps boîte** — si l'utilisateur arrive à la boîte et repart immédiatement vers un client, ce temps n'est PAS du temps boîte. C'est du transit. Seul le chargement/déchargement à la boîte compte comme heures boîte.
2. **Trajet maison→boîte NON payé** — le trajet domicile→boîte n'est JAMAIS compté comme temps de travail.
3. **Fin de journée = arrivée boîte** — la journée se termine quand l'utilisateur arrive à la boîte au retour, pas quand il arrive chez lui.
4. **Journée sans client** — si aucun client n'a été visité (pas de `start_route`/`arrivee_client`), tout le temps à la boîte compte comme hBoite.
5. **Pause légale obligatoire** — minimum 30 min à midi. Si l'utilisateur dit "j'ai pris mon heure le midi", déduire 1h. Si aucune pause mentionnée, déduire 30 min minimum.
6. **Prime 13e** calculée sur les heures normales uniquement (hBoite + hClient), PAS sur les heures de route.
7. **Panier** (19€) uniquement si l'utilisateur a visité un client ce jour-là.
8. **Plusieurs clients par jour** — le trajet entre clients compte comme heures route. Le temps chez chaque client compte comme heures client.
9. **Déchargement à la boîte** — compte comme hBoite (taux normal), PAS comme route/sup.
10. **Pause réglementaire** — si l'utilisateur travaille pendant une pause légale obligatoire (ex: pas de pause pointée mais légalement requise), le récap doit quand même la déduire.

## Exemple de calcul semaine (session 07/08/2026)

Semaine du 4 au 8 août 2026:

| Jour | Route | Client | Boîte | Pause | Total | Salaire |
|------|-------|--------|-------|-------|-------|---------|
| Lundi | — | — | 7h45 | 1h00 | 7h45 | 109,04€ |
| Mardi | 2h30 | 7h00 | — | 1h00 | 9h30 | 158,12€ |
| Mercredi | 3h30 | 7h00 | 1h25 | 1h00 | 12h25 | 193,94€ |
| Jeudi | 3h55 | 7h55 | 0h30 | 0h30 | 12h50 | 200,73€ |
| Vendredi | 2h50 | 7h15 | — | 1h15 | 10h05 | 166,64€ |
| **Semaine** | **12h45** | **29h10** | **10h10** | — | **52h35** | **828,47€** |

Notes:
- Lundi: travaillé à la boîte uniquement (7h30→11h30 + 12h30→15:45), pas de panier, pas de route
- Mardi: chez SKF (8h→12h + 13h→16h), départ 6h45 (déduit de 1h15 route), retour 16h→17h15 (1h15 route)
- Mercredi: chez SKF (8h→12h + 13h→16h), retour 16h→18h15 (2h15 route), puis préparatifs Thalès à la boîte 18h15→19h40 (1h25 boîte)
- Jeudi: Thalès (8h→9h15) + SKF (10h05→12h30 + 13h→17h15), déchargement boîte 19h→19h30
- Vendredi: chez client (8h→10h + 10h15→13h + 14h→16h30), pause légale midi 13h→14h déduite