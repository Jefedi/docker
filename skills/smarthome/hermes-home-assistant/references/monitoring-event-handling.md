# Gestion des événements de monitoring HA

Ce document décrit comment traiter les flux d'événements de monitoring Home Assistant (sondes de type Uptime Kuma / Beszel / certificate expiry / response time).

## Distinguer une vraie panne d'un glitch de monitoring

### Signaux d'un glitch de monitoring (inaction requis)

Quand des entités de monitoring passent à `unavailable` SIMULTANÉMENT :

```
Certificate expiration: 80d → unavailabled
Response time Ø (30 days): Xms → unavailablems
Type de moniteur: ping → unavailable
```

**Vérifier les entités coeur** (Freebox uptime, jTower, etc.) :
- Si elles continuent de s'incrémenter normalement → **monitoring fault**, pas les services
- Si elles aussi sont figées → vérifier le serveur

**Diagnostic rapide :**
```bash
df -h / && free -h && uptime
docker ps -q 2>&1
```

### Signaux d'une vraie panne

- Entités coeur figées ou en erreur
- Serveur CPU/Disk/Mem saturé
- Plusieurs services inaccessibles DIRECTEMENT (pas via le moniteur)

## Réponse aux flux d'événements

### Variations normales — réponse minimale

Ces événements ne nécessitent **aucune action** et une **réponse minimale** :

- Consommation électrique (variations de quelques W)
- Temps de réponse (variations <200ms)
- Courant, tension, uptime (variations infimes)
- Heure appareil, ping, bandwidth

**Réponse type :** « Rien à signaler. » — ou simplement « RAS. »

### Monitoring integration fault — réponse synthétique

Quand des événements unavailable simultanés sont détectés :
1. Vérifier rapidement le serveur/santé
2. Identifier le pattern (même chose que la dernière fois)
3. Communiquer le diagnostic : c'est la couche de monitoring, pas les services

**Réponse type :**
```
[Courte synthèse du pattern détecté]
Diagnostic : monitoring fault, les vrais services tournent.
X déjà revenus, les autres suivent.
```

### Vraie panne — réponse détaillée

Action immédiate, investigation, escalade.

## Signal fort : le type de moniteur lui-même devient unavailable

Quand des entrées comme `Type de moniteur: docker → unavailable` ou `Type de moniteur: ping → unavailable` apparaissent, c'est un signe encore plus fort que le monitoring lui-même est en panne — pas juste les valeurs, mais la **définition de la sonde** dans l'intégration (souvent Beszel ou Uptime Kuma) qui perd sa connexion.

## Ordre de rétablissement typique

Après une cascade unavailable, le retour à la normale suit généralement cet ordre :

1. **Certificats** : `unavailabled → 80d` (premiers à revenir)
2. **Temps de réponse** : `unavailablems → Xms`
3. **Types de moniteur** : `unavailable → docker / http / ping`
4. **Uptimes** : `unavailable% → X%` (derniers à revenir)

Si les certificats et temps de réponse reviennent mais pas les uptimes, patienter — le rétablissement complet peut prendre quelques minutes.

## Gestion des floods d'événements

Quand l'utilisateur reçoit une pluie d'événements unavailable :

1. **Réponse synthétique immédiate** : identifier le pattern, donner le diagnostic
2. **Proposer d'attendre** : « Je te préviens quand tout sera revenu »
3. **Ne pas accuser réception de chaque retour individuel** — attendre que la vague passe
4. **Annoncer la fin** : « Monitoring rétabli, tout est stable. »

## Vagues d'oscillation cycliques (monitoring flapping)

Parfois la couche monitoring (Beszel/Uptime Kuma) entre dans un cycle d'oscillation : unavailable → rétabli → unavailable → rétabli, répété plusieurs fois à intervalles réguliers (~5-10 min).

### Signaux d'une vague en cours

- Plusieurs vagues d'`unavailable` / spikes simultanés avec rétablissement spontané entre chaque
- Les services réels (Freebox uptime, jTower, F1 horloge) continuent de s'incrémenter normalement pendant les vagues
- Les certificats et monitors cyclent 80d → unavailable → 80d à chaque vague
- Les temps de réponse des services passent par des spikes (souvent x10-x50) mais reviennent à la normale quelques minutes après la fin de la vague

### Amplitude observée

Jusqu'à **8+ vagues** consécutives peuvent survenir dans une même session, s'étalant sur 2-3 heures. Chaque vague dure environ 5-10 minutes avec résorption spontanée entre les vagues. Il n'y a pas de dégradation progressive entre les vagues — la Nième vague n'est pas plus longue ni plus sévère que la première.

### Conduite à tenir

- **Numéroter les vagues** : « 7e vague monitoring — même motif. » Cela rassure l'utilisateur (nous suivons, c'est le même schéma récurrent).
- Identifier la vague dès les signes (cycle d'oscillation, pas de dégradation progressive)
- Ne pas déclarer "c'est fini" après un rétablissement — attendre un cycle complet sans nouvelle oscillation
- Documenter : vague N observée, heure, durée, spike max
- Les vagues se résorbent spontanément sans intervention — aucune action recommandée
- Quand la vague se résorbe, l'annoncer brièvement : « Résorption bien engagée — Shop LG, n8n, ntfy certificats revenus à 80d ✅. »

## Spikes sans unavailable (sous-seuil d'oscillation)

Tous les spikes ne sont pas des vagues complètes. Parfois un seul service présente un pic isolé (ex: `pangolin: home.jefe.al 84→1535ms`) sans que d'autres entités suivent ni que le monitoring ne devienne unavailable.

**Conduite à tenir :**
- Si un seul service spike sans unavailable autour : noter et surveiller, ne pas diagnostiquer "vague monitoring"
- Si 2-3 services spike simultanément (Seerr + ntfy + n8n par ex.) : c'est probablement le début d'une vague
- Un spike isolé qui se résout spontanément en 1-2 minutes n'est pas une vague

## Distinguer monitoring flapping d'autres causes d'unavailable

Toutes les entités `unavailable` ne sont pas des vagues monitoring. Certaines intégrations peuvent tomber indépendamment :

### PSN / PlayStation Network
- L'intégration PSN peut perdre l'accès au profil utilisateur, rendant tous les trophées (niveau, platine, or, argent, bronze) et l'abonnement `unavailable`
- **Indices distinctifs** : uniquement les entités PSN sont touchées — le reste de l'infrastructure reste stable. Aucun certificat, monitor Docker, ou temps de réponse ne bascule en unavailable simultanément.
- **Causes possibles** : session API expirée, abonnement PS Plus résilié, indisponibilité PSN côté Sony
- **Réponse** : si l'ensemble des trophées PS est unavailable sans autre entité impactée, mentionner que c'est spécifique à l'intégration PSN, pas une vague monitoring

### Comparatif rapide

| Pattern | Entités touchées | Rétablissement | Cause |
|---------|-----------------|----------------|-------|
| Vague monitoring (8+) | DNS, certifs, uptimes, response times, types de moniteur (tout sauf physiques) | Spontané ~5-10 min | Couche Beszel/Uptime Kuma |
| PSN indisponible | Trophées, niveau, abonnement uniquement | Heures/jours | API PSN, abonnement |
| Vrai service down | Un service + ses dépendances | Jusqu'à intervention | Bug, mise à jour, panne |

## Éviter le bruit

- Ne pas répondre à chaque événement individuel dans un flux
- Attendre 1-2 cycles pour voir si le monitoring se rétablit
- Grouper par pattern, pas par entité
- Reconnaître les motifs récurrents de la même session
- Pendant une vague : réponse synthétique unique, pas d'accusé de réception pour chaque retour individuel
- Quand une entité spike isolée se résout d'elle-même en moins de 2 minutes : ne pas la mentionner dans la réponse suivante
