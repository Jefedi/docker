# Divergence uptime 1d vs 30d/365d en recovery de vague

## Le pattern

Pendant et juste apres une vague monitoring, les uptimes **1 jour** et
**30 jours / 365 jours** divergent significativement :

| Metrique | Impact typique par vague |
|----------|------------------------|
| Uptime 1d | -0.07% a -0.2% (baisse visible en temps reel) |
| Uptime 30d | -0.001% a -0.004% (a peine perceptible) |
| Uptime 365d | -0.0001% a -0.002% (souvent invisible) |

## Pourquoi

- **Uptime 1d** : la fenetre est courte (~24h). Une panne monitoring de
  3-5 min sur cette fenetre represente ~0.2-0.35% du temps. C'est la
  metrique la plus reactive.
- **Uptime 30d** : la meme panne est diluee dans ~720h de donnees.
  L'impact est ~0.002%-0.004% — souvent masque par le bruit normal.
- **Uptime 365d** : completement noye dans 8760h. Impact souvent
  inexistant ou <0.001%.

## Signes distinctifs de cette divergence

1. **Uptime 1d baisse** (ex: jellyfin 98.33% → 98.27%) pendant qu'un
   **uptime 30d du meme service monte** (ex: anonaddy 99.988245% →
   99.988246%)
2. La baisse 1d est toujours **10-50× plus forte** que la baisse 30d
3. Les 30d peuvent meme montrer une **micro-augmentation** (+0.000001%)
   si un ancien downtime sort de la fenetre glissante en meme temps

## Conduite

RAS direct — ces deux metriques disent la meme chose a deux echelles
differentes. Toujours preferer l'uptime 30d/365d pour juger de la sante
reelle d'un service. L'uptime 1d reflete juste l'impact transitoire de
la vague monitoring.
