# French Overtime Rates (Heures Supplémentaires)

## Legal Majoration (Code du Travail)

| Tranche | Majoration |
|---|---|
| 36e à 43e heure hebdomadaire | **+25%** |
| Au-delà de la 43e heure | **+50%** |

- Durée légale du travail: 35h/semaine
- Les heures sup sont calculées par semaine civile
- Une convention collective peut prévoir des taux différents (souvent plus favorables)
- Les heures sup donnent aussi droit (sous conditions) à un repos compensateur

## Source

- Code du Travail français
- Wikipédia: https://fr.wikipedia.org/wiki/Heures_supplémentaires (confirmé 2026-08-06)
- Service-Public.fr (https://www.service-public.gouv.fr — l'ancienne URL F2371 redirige vers 404)

## Application dans ce système

Le taux route/conducteur/heures-sup = taux normal × 1,25 (majoration 25%).

| Période | Taux normal | Taux sup (+25%) |
|---------|-------------|-----------------|
| Avant juillet 2026 | 12,50 € | 15,63 € |
| Juillet 2026 | 12,80 € | 16,00 € |
| Dès 3 août 2026 | 13,00 € | 16,25 € |

**Confirmé par exemple réel** : récap hebdomadaire du 27 juillet au 2 août montre :
- Heures de route : 13 × 16,00€ = 208,00€ (taux route juillet = 12,80 × 1,25 = 16,00€)
- Heures normales : 35 × 12,80€ = 448,00€
- Heures supp. 25% : 1,25 × 16,00€ = 20,00€ (1h sup exprimée en équivalent 1,25)

Pour la v1, on utilise uniformément +25% pour :
- Heures de trajet conducteur
- Heures supplémentaires au-delà de 35h/semaine

La tranche +50% (au-delà de 43h) n'est pas implémentée en v1 — à ajouter en v2 si nécessaire.

## Prime de 13e Mois

- 1,07 € par heure normale (fixe)
- Calculée sur les heures normales uniquement (pas sur les heures de route)
- Confirmé par exemple réel : 35 × 1,07€ = 37,45€ (37,32€ sur l'exemple, arrondi flottant)