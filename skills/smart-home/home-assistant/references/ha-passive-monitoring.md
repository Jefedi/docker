# Triage passif des notifications HA (Infrastructure Watch)

Workflow pour répondre aux événements Home Assistant qui arrivent en temps réel — notifications de changement d'état de sondes, capteurs, moniteurs.

## Contexte

L'utilisateur reçoit des notifications HA continues (Freebox, jTower, services Docker, monitoring Pangolin) et les relaye à l'agent. Le rôle est de les trier rapidement :

- **Tout va bien** → accusé réception concis (1 ligne)
- **Anomalie probable** → investiguer puis rapporter
- **Anomalie déjà connue** → rappeler le contexte et confirmer

## Principe général

99 % des événements sont normaux. La plupart sont :
- Incréments de compteurs (uptime, temps de fonctionnement, consommation kWh)
- Micro-recalculs d'uptime (99.92xxx% → 99.92yyy%, variations < 0.001 %)
- Variations DNS de 1 à 3 ms
- Changements de temps de réponse de 1 à 5 ms (sauf si pic > 10× la valeur de base)
- Variations de mesure (température, tension, courant, puissance, signal dBm)
- Ticks d'horloge (+5s, +30s)
- Changements de trafic réseau mineurs

## Réponse standard

**Toujours en français**, très concis. Deux formats acceptés :

**Format par service :**
```
**Service** — Valeur. RAS. ✓
```

**Format par groupe (tableau) :**
```
| Service | Valeur | Statut |
|---|---|---|
| **X** | 42 ms | ✅ |
```

**Format condensé (multi-événements, préféré pour les salves) :**
```
RAS. +2ms DNS, -0.3V jTower — bruit de fond normal.
```

Ou encore plus court pour des événements totalement triviaux :
```
RAS, +0.05% disque — rien de notable.
```

Le format condensé est recommandé quand 2-5 événements arrivent en même temps et sont tous normaux. Un simple « RAS. ✓ » ou « Rien à signaler. » suffit quand tout est nominal. Ne pas expliquer ce qui est normal — la confiance de l'utilisateur est déjà établie.

## Pattern : sondes de monitoring qui flappent

Symptôme : plusieurs entités passent simultanément à unavailable. Trois variantes selon le type de sonde :
| Type de sonde | Valeur unavailable |
|---|---|
| Certificats | `unavailabled` |
| Uptimes Docker/Pangolin | `unavailable%` |
| Temps de réponse | `unavailablems` |
| Tags Docker | `unavailabletags` |
| Trophées PSN | `unavailabletrophies` |
| Type de moniteur | `unavailable` |
| DNS / Ping | `unavailablems` ou `unavailable` |

**Diagnostic** : ce ne sont PAS les services qui sont en panne. Les sondes de monitoring (Uptime Kuma / Beszel / Pangolin internal probes) perdent pied temporairement. Preuve, par ordre de fiabilité :

1. **Beszel-agent lui-même en `unavailable%`** — si le conteneur de monitoring est listé comme unavailable, alors toutes les autres sondes Beszel sont invalides par définition. C'est le confirmateur n°1.
2. **Les services sous-jacents continuent de répondre normalement** (vérifier les temps de réponse réels indépendants comme n8n, Freebox uptime, jTower mesures électriques)
3. **Plusieurs sondes flappent en même temps** — statistiquement impossible si c'était de vraies pannes individuelles, mais parfaitement normal si c'est la plateforme de monitoring qui vacille
4. **Les sondes reviennent spontanément après quelques minutes**

**Action** : ne rien faire. Signaler que c'est la même vague de monitoring, pas un vrai problème.

**Piège** : ne pas alerter l'utilisateur inutilement. Ces vagues se produisent par cycles (observé : vagues de 2-3 minutes, séparées de 5-10 minutes, puis tout se stabilise). Peuvent se produire plusieurs fois dans une heure puis disparaître complètement.

**Observation annexe : pics de bande passante** — Pendant les vagues de flapping, la bande passante Pangolin peut bondir (ex: 0.09 → 5.76 MB/s, notamment le trafic sortant). Probablement lié aux sondes qui refrappent toutes les cibles simultanément lors de la reprise. C'est normal et transitoire.

**Vague typique observée** : 3-9+ vagues rapprochées (certificats → DNS → Docker uptimes → temps de réponse → Pangolin statuts), puis accalmie. Chaque vague dure 2-5 minutes. Les vagues peuvent s'étaler sur plus de **2h30** (observé : jusqu'à 9+ vagues en ~2h du début de la 1ère à la résorption de la 9e). Les services réels (vérifiés via leurs latences) ne montrent aucun signe de panne pendant ces épisodes.

**Numérotation des vagues** : l'utilisateur apprécie le suivi par numéro de vague (« 8e vague monitoring ») — ça donne confiance que l'agent reconnaît le pattern et suit l'évolution. Commencer à numéroter dès la 2e occurrence, incrémenter à chaque nouvelle vague, et marquer la résorption (« 8e vague résorbée ✅ »).

**Numérotation des vagues** : quand les vagues se succèdent, les compter explicitement (`1ère vague`, `2e vague`, ..., `8e vague`). Cela permet :
- À l'utilisateur de suivre l'évolution en un coup d'œil
- D'éviter de ré-expliquer le diagnostic à chaque vague (`Même motif, 8e vague` suffit)
- De détecter si le nombre de vagues dépasse le pattern habituel (alerte alors)

**Quand une vague est identifiée comme la Nième récurrence** : sauter l'investigation. Pas de vérification des ressources système, pas de vérification des services sous-jacents — accuser réception brièvement et continuer. L'investigation n'est faite que pour la 1ère vague (ou si le pattern change).

**Réponse intra-vague (cookie-cutter)** : une fois qu'une vague est numérotée et en cours, ne pas ré-expliquer. Utiliser un pattern répétable :

- Vague encore active avec de nouveaux entrants : « Vague monitoring toujours en cours. Résorption imminente. »
- Vague qui s'éternise : « Vague monitoring toujours en cours. Résorption dans les minutes à venir. »
- Résorption confirmée : « Résorption confirmée — certificats retour à 80d. RAS ✓ »
- Vague résorbée+nouvelle vague : « 9e vague monitoring résorbée. 10e vague en cours. »

Ce pattern fonctionne même avec 30+ événements consécutifs pendant une vague. L'utilisateur ne corrige pas — il lit les numéros pour savoir si on progresse vers la fin.

**Oscilloscope intra-vague** : pendant une même vague, les entités ne tombent et ne reviennent pas toutes en bloc — elles oscillent **par strates**. Une entité qui revient à la normale ne signifie pas que la vague est finie :

```ascii
Los Galactique Panel certif:  80d → unavailabled → 80d
Shop LG certif:               80d → unavailabled
Seerr certif:                 80d → unavailabled
n8n certif:                   80d → unavailabled
...(1 min)...
Los Galactique certif:                80d (confirmé)
...(30s)...
Shop LG certif:                               unavailabled → 80d
Seerr certif:                                 unavailabled → 80d
```

**Marqueur de vague active** : quand au moins 3 entités de types différents (certificat, Docker uptime, temps de réponse, Pangolin statut, DNS) sont en `unavailable` simultanément, la vague est encore en cours. Tant que ce critère tient, ne pas déclarer la vague terminée.

**Heartbeat du serveur** : pendant une vague, vérifier rapidement que le socle tient :
- **Freebox v8 Temps de fonctionnement** : tick de +30s réguliers → HA tourne, Freebox répond.
- **jTower Heure de l'appareil** : tick de +5s → jTower (hôte HA ou monitor) est éveillé.
- **F1 Race Track time** : tick de +1min → capteurs HA de base actifs.
- **jTower mesures électriques** : consommation, tension, courant continuent de varier normalement.
Si ces indicateurs tickent pendant que les sondes Beszel/Pangolin/Uptime Kuma flappent, c'est une confirmation quasi-certaine que seule la couche monitoring est impactée.

**Piège : vague vs vraie panne** — les vagues monitoring peuvent inclure des changements d'état comme `down → unavailable` (ex: hermes.jefe.al Statut). Un service déjà `down` passé en `unavailable` ne change rien au diagnostic — c'est la même oscillation. Ne pas le traiter comme un événement distinct.

**Note : uptimes 365 jours** — même les capteurs d'uptime sur 365 jours passent à `unavailable%`. Ce n'est pas l'uptime réel qui change, c'est la sonde qui ne peut plus lire la valeur et la déclare manquante dès qu'elle se re-synchronise.

**Note : plateforme Beszel entière** — `docker:beszel Uptime (1 day)`, `docker:beszel Uptime (365 days)`, `docker:beszel-agent`, tous les `docker:xxx Response time` passent unavailable en bloc. C'est le pattern signature d'une panne Beszel plutôt que d'une panne service individuel.

## Pattern : spikes de latence isolés

Symptôme : un seul service voit son temps de réponse bondir (ex: n8n 46→2615ms, FreshRSS 111→1413ms) sans que les autres soient affectés en même temps.

**Diagnostic** : même si le pic est isolé, le motif est souvent identique aux spikes multiples — monitoring qui flappe sur une sonde individuelle, ou micro-latence réseau transitoire. Si le service revient à la normale dans les 1-3 minutes (confirmé par un événement HA suivant), c'est un faux-positif.

**Contrainte 403** : si l'entité concernée est protégée par 403 (ex: `sensor.n8n_temps_de_rponse` inaccessible), il est impossible de vérifier l'état en direct. **Solution** : ne pas bloquer — continuer à observer le flux d'événements HA. L'utilisateur reçoit les événements en temps réel ; le retour à la normale arrivera comme un événement HA subséquent. Laisser le flux d'événements servir de sondage passif.

**Action** : signaler le pic, guetter le retour. Si plusieurs spikes isolés se produisent sur différents services dans un court intervalle, les reclasser comme « spikes multiples simultanés » (cf. section ci-dessous).

## Pattern : spikes de latence multiples

Symptôme : 2-3 services voient leur temps de réponse monter en flèche en même temps (ex: FreshRSS 128→2265ms, Immich 205→1176ms, LibreTranslate 50→744ms).

**Diagnostic** :
1. Ne pas paniquer — souvent transitoire
2. Vérifier les ressources système via terminal :
   - `free -h` → RAM
   - `top -bn1 | head -5` → CPU, load, iowait
   - `df -h` → disque (si pertinent)
3. Un iowait élevé (>5%) ou un load > coeurs CPU peut expliquer des latences partagées (ex: backup, I/O disque)
4. Si les ressources sont OK, attendre le prochain tick — les latences retombent généralement seules

**Action** : vérifier les ressources, rapporter le diagnostic succinctement, proposer d'investiguer plus si ça persiste.

## Pattern : uptime anormalement bas

Symptôme : un service a un uptime 30j significativement bas (ex: FreshRSS à 79,9 %).

**Réponse** : signaler le fait (sans alarme excessive), proposer de vérifier l'état actuel du conteneur et ses logs. Utile uniquement si l'utilisateur montre de l'intérêt — sinon, noter et passer.

## Contraintes d'environnement

- **Docker daemon inaccessible** : `/var/run/docker.sock` n'est pas monté. Impossible d'utiliser `docker ps`, `docker stats`, `docker logs`.
- Les vérifications système passent par les commandes shell de base (`free`, `top`, `df`, `uptime`, `curl`).
- L'API HA MCP est disponible (via `ha_get_state`, `ha_eval_template`, etc.) pour vérifier l'état des entités.

## Triggers pour escalade

Les situations qui justifient une investigation active (pas juste un accusé réception) :

1. **Plusieurs services latences simultanément** → vérifier ressources système
2. **Un service reste anormalement haut sur plusieurs ticks consécutifs** (pas un spike isolé)
3. **Un uptime 30j descend sous 95 %** → noter, proposer d'investiguer
4. **Des entités deviennent `unavailable` ET les services sous-jacents ne répondent plus** (à distinguer du pattern « monitoring flap » ci-dessus)
5. **Disque plein ou RAM saturée** → alerter immédiatement

## Pattern : profil PSN (Zef__59) indisponible

Symptôme : les capteurs PSN (Zef__59) — niveau, trophées platine/or/argent, next level — passent simultanément à `unavailabletrophies` ou `unavailable%`.

**Diagnostic** : peut être :
- **Abonnement PS Plus résilié/expiré** (`Subscribed to PlayStation Plus: cleared`). L'intégration PSN perd alors l'accès au profil complet.
- La vague monitoring classique (si d'autres entités non-PSN flappent aussi)

**Action** : ne pas s'alarmer. Si `PS Plus: cleared` a précédé l'événement, c'est attendu. L'intégration peut se rétablir seule (les capteurs reviennent avec des valeurs à 0 après 1-2 ticks). Proposer de reconfigurer ou supprimer l'intégration PSN si l'utilisateur n'a plus l'abonnement.

**Séquence de récupération typique :**
1. `Subscribed to PlayStation Plus: cleared` — abonnement expiré/résilié (peut être antérieur)
2. `Trophy level: N → unavailable`, `Platinum trophies: N → unavailabletrophies`, etc. — toute la section PSN tombe
3. Après 1-5 minutes, les capteurs reviennent un par un : `Next level: unavailable% → 0%`, `Platinum trophies: unavailabletrophies → 0trophies`
4. Ils restent à 0 (profil PSN accessible mais sans accès aux données réelles)

**Diagnostic** : si SEULS les capteurs PSN passent unavailable (pas de vague monitoring large), c'est bien l'intégration PSN qui a perdu sa session, pas la couche monitoring. La récupération à 0 confirme le diagnostic _a posteriori_.

## Pattern : changement de mappage de ports Freebox

Symptôme : `Freebox v8 (r1) Nombre d'entrées de mappage de port (IPv4): changed from N to N+1`.

**Diagnostic** : un nouveau port a été ouvert sur la Freebox. Peut être :
- UPnP automatique par un service/jeu/application
- Ajout volontaire via l'interface Freebox
- Un conteneur Docker qui expose un port en mode host

**Action** : le signaler et demander si l'utilisateur a configuré quelque chose récemment. Si non, proposer d'investiguer.

## Pattern : vague de réhabilitation (recovery wave)

Symptôme : plusieurs entités qui étaient passées à `unavailabled`/`unavailable%` reviennent simultanément à la normale — certificats à `80d`, temps de réponse à des valeurs réelles, uptimes à ~99-100%.

**Diagnostic** : Cela confirme **rétroactivement** que la vague précédente était bien un flapping de la couche de monitoring, pas une vraie panne. Les certificats n'expirent jamais tous en même temps et ne se réhabilitent pas tous simultanément — c'est la sonde (CertMon / Pangolin) qui a retrouvé son accès.

**Action** : Accuser réception brièvement (« Certificats réhabilités, RAS ✓ »). C'est la confirmation que le diagnostic était correct. Passer à autre chose.

## Pattern : trafic réseau — spike puis retour au calme

Symptôme : débit entrant et/ou sortant d'un service (Pangolin, NAS, serveur) monte soudainement (ex: 0.09 → 5.76 MB/s, ou 1.5 → 4.7 MB/s), puis redescend après quelques minutes.

**Diagnostic normal :**
- Transfert ponctuel terminé (sauvegarde, synchro, mise à jour, réplication, pull d'image Docker)
- Si l'envoi ET la réception montent ensemble → probablement une synchro bidirectionnelle (syncthing, restic, rsync)
- Si seul l'envoi ou la réception monte → téléchargement ou upload isolé
- Le retour au bruit de fond (souvent <500 kB/s pour un serveur au repos) confirme que l'opération est finie

**Action** : constater la fin du transfert, ne pas investiguer. Si le trafic reste élevé >30 min sans raison apparente, proposer de vérifier.

## Pattern : valeurs électriques jTower (PC)

Symptôme : notifications de `jTower (PC)` pour consommation, tension, courant.

**Signal Wi-Fi jTower** : les variations de ±1 à ±2 dBm dans la plage -33 à -37 dBm sont normales. Ne pas signaler comme anomalie.

**F1 Race Track time** : horloge qui ticke de +1 minute régulièrement. C'est normal — ne pas commenter au-delà de « F1 +1min ». L'horloge peut osciller (14:10 → 14:11 → 14:10) — normal.

**DNS aggregate counters** : les entités `ALL Requêtes IPv4`, `ALL Requêtes IPv6`, `ALL Requêtes DNS`, `ALL Requêtes DNS-over-HTTPS`, `ALL Requêtes chiffrées`, `ALL Requêtes validées par DNSSEC` sont des compteurs agrégés. Leur augmentation (quelques dizaines à centaines) est normale — trafic DNS standard. Ne pas commenter au-delà de « +N requêtes DNS, normal. ».

**Corrélation DNS vagues monitoring** : pendant une vague monitoring, le trafic DNS peut augmenter de ~100 requêtes supplémentaires (ex: 739→833). C'est normal — les sondes qui récupèrent leur accès refrappent toutes les résolutions DNS pour ré-établir leurs monitors. Ne pas investiguer.

**Météo/Weather** : les changements de couverture nuageuse, pluie, marée, UV sont des mises à jour de prévisions normales. Pas d'investigation.

**Prix carburant** : les changements de prix (ex: Station Gonfrevildis Gazole 1.915→1.929€/l) sont des mises à jour normales. Ne pas commenter.

**PSN Zef__59** : voir section dédiée plus bas.

**Plages normales observées** (Zef's homelab) :
- **Tension** : 234–236 V (variations de ±0.2–0.4V normales)
- **Courant** : 0.8–1.4 A (variations de ±0.01–0.15A normales ; un écart plus marqué comme 1.13→0.98A peut indiquer qu'un appareil s'allume/s'éteint sur le PC)
- **Consommation instantanée** : 158–290 W selon l'état du PC (variations de ±0.6–2.4W normales ; le PC peut être en veille/idle à ~158W ou en charge active à ~275-290W)
- **Consommation aujourd'hui** : incrément normal de ~0.001–0.002 kWh par tick
- **Consommation ce mois-ci** : incrément normal de ~0.001 kWh par tick
- **Horloge** : ticks réguliers de +5s (normaux, confirmation d'activité)

Tout écart dans ces plages est normal. Seuils d'alerte : tension < 225V ou > 245V, courant > 2A, puissance > 500W.

## Pattern : écart uptime 1j vs 30j

Symptôme : uptime 1j à ~59 % mais uptime 30j à ~98 % (ex: Paperless).

**Diagnostic** : le service est fiable sur la durée mais a eu un épisode d'indisponibilité dans les dernières 24h. L'uptime 1j chute linéairement tant que l'épisode est dans la fenêtre, puis remonte après 24h.

**Action** : ne pas alarmer — la tendance 30j est la métrique fiable. L'uptime 1j est un indicateur à court terme qui se normalise de lui-même. Si l'uptime 30j est aussi bas (<95 %), alors c'est un vrai problème structurel.

## Piège : API HA directe en 403

L'API REST HA directe (`ha_get_state` sur `home.jefe.al` via outil direct `ha_get_state` ou terminal) retourne **403 Forbidden** pour certaines entités en raison de la configuration `trusted_proxies` ou du scope du token. Utiliser le MCP (`ha-mcp.jefe.al`) à la place pour toutes les requêtes HA.

**Note importante** : même via le MCP (`mcp__ha_mcp__ha_get_state`), certaines entités spécifiques — notamment les `sensor.*_temps_de_rponse` (FreshRSS, n8n, Immich, etc.) — retournent aussi **403**. C'est une restriction du token HA (scope limité), pas un problème de proxy. Dans ce cas, **attendre le flux d'événements HA** : l'utilisateur reçoit les changements en temps réel, et le retour à la normale arrivera comme un événement HA subséquent.

## Exemples concrets (extraits de sessions réelles)

```
[HA] FreshRSS Temps de réponse: 128ms → 2265ms
[HA] Immich Temps de réponse: 205ms → 1176ms
[HA] LibreTranslate Temps de réponse: 50ms → 744ms

→ Vérification : free, top. iowait 5.4%, reste OK.
→ Conclusion : transitoire, pas d'action. Les latences retombent.
```

```
[HA] Expiration du certificat: 80d → unavailabled (×8 services)  
→ Pattern monitoring flap. Services répondent normalement.  
→ Aucune action.  
```  

```  
[HA] Certificats Seerr, n8n, ntfy, FreshRSS, Immich, LibreTranslate: unavailabled → 80d (simultanément)  
→ Recovery wave — confirme rétroactivement le monitoring flap. RAS ✓  
```  

```  
[HA] pangolin: jflix, beszel, ph.jefe.al, node.losgalactique.fr → unavailable (×6 en 2 min)  
[HA] Certificats Los Galactique Panel: 80d → unavailabled  
→ Nouvelle vague monitoring. n8n toujours à 37ms, jTower stable.  
```  

```  
[HA] Zef__59 Subscribed to PlayStation Plus: cleared  
[HA] Zef__59 Trophy level: 116 → unavailable  
[HA] Zef__59 Platinum trophies: 0 → unavailabletrophies  
[HA] Zef__59 Silver trophies: 48 → unavailabletrophies  
→ PSN spécifique (pas monitoring) : seul le profil PSN tombe, tout le reste stable.  
...(2 min)...  
[HA] Zef__59 Next level: unavailable% → 0%  
[HA] Zef__59 Platinum trophies: unavailabletrophies → 0trophies  
→ Confirmation : intégration reconnectée, profil accessible mais vidé.  
```
