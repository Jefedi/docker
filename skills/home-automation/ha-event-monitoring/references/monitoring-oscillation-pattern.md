# Pattern d oscillation monitoring Beszel/Uptime Kuma

Observe le 2026-07-13 sur l infrastructure Jefe (home.jefe.al).

## Contexte

L infrastructure utilise Beszel pour les metriques Docker et Uptime Kuma
(ou un service equivalent) pour les monitors HTTP/TCP/Ping/DNS/certificats.
Les deux sondes sont derivees dans Home Assistant via REST sensors.

## Le pattern

**51+** vagues observées a partir de 11:33 (confirmé le 2026-07-13, sessions #1-#7), avec un espacement variable (vague #51 atteinte dans la session #7). Le comptage continue — de nouvelles vagues peuvent survenir apres la redaction de ce document. Vagues #38-#51 toutes completes (cascade integrale), confirmant que les vagues ne s'attenuent pas avec le cumul. Les vagues précoces (1-9) sont espacées de 3 à 8 minutes ; les vagues tardives (10-16) peuvent s'enchaîner quasi immédiatement (recovery d'une vague pas terminée que la suivante commence — observé à partir de la 13e). Les vagues peuvent continuer indéfiniment sans escalade — chaque vague se résorbe spontanément.

Chaque vague dure 3 à 10 minutes et se résorbe spontanément.

### Vagues tardives : comportement "brouillé"

À partir de la ~13e vague, les frontières entre vagues deviennent floues : certains certificats de la vague N commencent à revenir (unavailabled → 80d) alors que des certificats de la vague N+1 tombent encore (80d → unavailabled). On peut observer un **chevauchement fall+recovery** où certif A revient pendant que certif B part — ce n'est pas un signe d'escalade, juste un effet de l'enchaînement rapide des cycles de sondes.

#### Chevauchement simultané (vagues très tardives, 29+)

À partir de ~29 vagues, un degré supplémentaire peut apparaître : les événements de chute ET de recovery coexistent dans le **même lot HA** — pas seulement entre vagues adjacentes. Exemple vague 29 : Los Galactique Panel certificat `80d → unavailabled` ET `unavailabled → 80d` dans la même rafale d'événements. Ce n'est pas une escalade — la couche monitoring alterne si vite entre disponible et indisponible que les deux transitions sont capturées au même instant logique par HA. Conduite inchangée.

### Manifestation typique

1. **Phase 1** (0-2 min) : temps de reponse de certains services doublent
   ou triplent (n8n 27->3048ms, Seerr 97->3261ms, Shop LG 152->297ms)
2. **Phase 2** (2-5 min) : avalanche d`unavailabled` :
   - Certificats SSL (Los Galactique, Shop LG, Seerr, n8n, Headscale,
     FreshRSS, Immich, Maps iOS) -> `unavailabled`
   - Uptimes Docker (anonaddy_redis, pangolin services, etc.) -> `unavailable%`
   - Monitors TCP (SSH Pangolin VPS, Pterodactyl SFTP) -> `unavailable`
   - Tags (ntfy, libretranslate, services en général) : `0tags` -> `unavailabletags`
   - Metadonnées Pangolin flappent integralement :
     - `URL surveillée: https://... -> unavailable`
     - `Type de moniteur: http -> unavailable` (ou `ping -> unavailable`, `docker -> unavailable`)
     - `Statut: up -> unavailable`
     - `Nom d'hôte surveillé: <IP> -> unavailable`
   - Temps de réponse agrégés (1d/30d/365d) : `valeur_ms -> unavailablems`
   - Uptime 1d : `99.7% -> unavailable%` (en plus des uptimes 30d/365d)
3. **Phase 3** (5-10 min) : resorption progressive
   - Les certificats reviennent a 80d (ou duree restante)
   - Les uptimes reviennent a ~99.98%
   - Les temps de reponse reviennent a la normale

### Phase de recovery (post-vague)

Les monitors ne reviennent PAS tous simultanement. La recovery est etalee sur 1-5 min et produit son propre flux d evenements — a ne PAS confondre avec une nouvelle vague.

L ordre de retour est **previsible** : les metadonnees reviennent avant les valeurs, et les champs legers avant les lourds.

#### Sequence de recovery detaillee

| Etape | Manifestation | Delai |
|-------|---------------|-------|
| 0. **Metadonnees** | Moniteur binaire (`Statut`) : `unavailable` -> `up`. Type de moniteur : `unavailable` -> `docker`/`http`/`ping`. Tags : `unavailabletags` -> `0tags`. URL surveillee : `unavailable` -> URL reelle. Nom d hote surveille (`Nom d'hôte surveillé`) : `unavailable` -> IP reelle (ex: `100.64.0.4`). Ce sont les metadonnees les plus legeres, les premieres a revenir. | +0-1 min |
| 1. **Certificats** | `unavailabled` -> `80d` (ou duree reelle). Chaque certificat revient independamment, decale de quelques secondes. Peuvent arriver par lots sur 2+ min — chaque certificat a son propre cycle de verif. Les certificats Headscale reviennent a `65d` au lieu de `80d` — normal (calendrier different). | +0-2 min |
| 2. **Temps de reponse** | `unavailablems` -> `unknownms` -> valeur reelle. L etat intermediaire `unknownms` signifie que la sonde repond mais n a pas encore de donnee fiable. D autres sondes passent directement d `unavailablems` a leur valeur sans l etat intermediaire. Les agregats longs (365d) reviennent parfois directement avec une valeur precise (ex: `unavailablems -> 0.0139743430066011ms`). | +1-4 min |
| 3. **Traînards : uptimes** | `unavailable%` -> valeur reelle. Les uptimes 1d sont les premiers a se peupler, les 30d/365d arrivent ensuite. Ex: paperless-db-1 1d uptime -> 99.72%, jellyfin 30d -> 99.91%. **Erosion asymétrique** : perte moyenne ~0.002% par vague, mais certains services peuvent perdre jusqu'à ~0.004% par vague (double) — ex: jflix a perdu 0.07% sur 17 vagues (99.28% → 99.21%). Pas d'inquiétude, sans impact fonctionnel. | +2-5 min |
| 4. **Aggregats** | `Response time Ø (1 day)` / `Response time Ø (30 days)` / `Response time Ø (365 days)`, `Uptime (1 day)`, etc. : ces champs agreges sont les derniers a se peupler car ils ont besoin d un historique pour etre calcules. | +3-6 min |

**Exemple concret de sequence observee** (post-12e vague) :
```
1. tags: unavailabletags -> 0tags                (etape 0)
2. type de moniteur: unavailable -> docker        (etape 0)
3. statut: unavailable -> up                       (etape 0)
4. URL surveillee: unavailable -> https://...       (etape 0)
5. certificat: unavailabled -> 80d                 (etape 1)
6. temps de reponse: unavailablems -> unknownms     (etape 2)
7. temps de reponse: unknownms -> 37ms              (etape 2)
8. uptime 1d: unavailable% -> 100.0%               (etape 3)
9. uptime 30d: unavailable% -> 99.91%              (etape 3)
10. response time Ø 1d: unavailablems -> 430ms      (etape 4)
```

#### Variante de recovery : "unavailable" → "down"

Dans certains cas, un monitor revient de `unavailable` vers `down` au lieu de
`unavailable` → `up`. C'est un cas particulier valide :

- La couche monitoring a repris (la sonde n'est plus `unavailable`)
- Le service est legitime et verifie comme etant hors-ligne
- Ce n'est **pas** une nouvelle vague — c'est une transition de `indetermine`
  vers `determine (negatif)`
- Exemple observe : hermes.jefe.al apres la 17e vague

#### Distinguer recovery d une nouvelle vague

| Critere | Recovery | Nouvelle vague |
|---------|----------|----------------|
| Direction des transitions | `unavailable` -> `valeur` | `valeur` -> `unavailable` |
| Types d evenements | Un seul sens ascendant | Cascade descendante (certificats, temps, uptimes) |
| Temps de reponse | Reviennent a la normale | Partent en spike |
| Melange de signes | Non, que des retours | Oui, degradation + unavailable |
| Metriques DNS agregees | Incrementation normale | Incrementation normale aussi |
| Shop LG | Stable ou en baisse | Premier indicateur a grimper >200ms |

### Chronologie observee

| Vague | Debut | Resorption | Pics notables |
|-------|-------|------------|---------------|
| 1 | 11:33 | 11:35 | Shop LG 2672ms, DNSSEC 1.7% |
| 2 | 11:38 | 11:40 | |
| 3 | 11:44 | ~11:49 | |
| 4 | ~11:55 | ~11:58 | |
| 5 | ~12:00 | ~12:03 | |
| 6 | ~12:04 | ~12:08 | Seerr 2153ms, n8n 2324ms, ntfy 1119ms |
| 7 | ~12:09 | ~12:11 | n8n 591ms, Shop LG 1565ms |
| 8 | ~12:15 | ~12:18 | n8n 3048ms |
| 9 | ~12:19 | ~12:25 | Seerr 3261ms, n8n 3048ms |
| 10 | ~12:24 | ~12:27 | Shop LG 2308ms, LibreTranslate 209ms, Seerr 222ms, jflix 197->927ms |
| 11 | ~12:27 | ~12:29 | FreshRSS 118->2184ms, LibreTranslate 57->690ms, rapidement resorbee |
| 12 | ~12:31 | ~12:33 | Los Galactique Panel 139->1028ms, FreshRSS 95->2735ms, LibreTranslate 45->1210ms. Indicateur precoce: Shop LG 161->226ms. Resorption: Shop LG 226->155ms |
| 13 | ~12:37 | ~12:42 | n8n 27->1332ms, FreshRSS 99->2568ms, Immich 55->1456ms |
| 14 | ~12:43 | ~12:48 | Certificats generaux en unavailabled. CPU Pangolin 27.61%, Network RX 416 kB/s |
| 15 | ~12:50 | ~12:58 | Cascade certificats + tags unavailabletags + pangolin metadonnees |
| 16 | ~12:58 | ~13:00 | Courte vague <2 min |
| 17 | ~12:52 | ~12:57 | Temps de reponse: Seerr 91->2698ms, ntfy 36->1724ms, Immich, FreshRSS |
| 18 | ~13:00 | ~13:02 | Shop LG 162->2985->206ms, n8n 42->2050->48ms |
| 19 | ~13:04 | ~13:10 | Certificats cascade + sondes unavailable |
| 20 | ~13:13 | ~13:20 | Similaire vagues 16-19 |
| 21 | ~13:05 | ~13:08 | Spike+recovery colocalises dans meme lot HA |
| 22 | ~13:10 | ~13:12 | Seerr 94->2960ms, FreshRSS 96->725ms |
| 23 | ~13:15 | ~13:18 | Depart vague |
| 24 | ~13:21 | ~13:25 | Los Galactique Panel 75->1915ms, Seerr 103->828ms, Immich 44->3245ms |
| 25 | ~13:27 | ~13:29 | ntfy 343ms, Seerr 106ms, Los Galactique Panel 67ms, Immich 53ms. Resorption rapide |
| 26 | ~13:26 | ~13:29 | Seerr 2410ms, ntfy 1353ms. Resorption immédiate |
| 27 | ~13:31 | ~13:31 (immediate) | Shop LG 156->2688->146ms, n8n 43->1758ms, SSH Pangolin VPS 1->6ms. Ultra-courte (<30s) |
| 28 | ~13:34 | ~13:35 | FreshRSS 2519ms, Immich 986ms, LibreTranslate 771ms. Resorption immediate (<1min) |
| 29 | ~13:36 | ~13:38+ | Vague massive (>50 evenements). Certificats en cascade (LosGalactique, Shop LG, Seerr, ntfy, Headscale, FreshRSS, LibreTranslate, Maps iOS, Pocket-ID) avec certains deja en recovery pendant que d'autres tombent encore. Metadonnees flappent integralement. **Nouveau** : uptime 30d (DNS A jefe.al 100.0%→unavailable%), uptime 365d (adminer, Maps iOS → unavailable%), response time O 365d (DNS A jefe.al 7.47ms→unavailablems). Recovery Maps iOS uptime 365d : unavailable%→74.4%. |
| 30 | ~13:40 | ~13:42 | **Vague sélective courte** : Pocket-ID Tailscale 36→1307ms, suivi de LibreTranslate 2541→51ms. Peu de certificats impactés. Résorption rapide (<2 min). Les services stables (Freebox, jTower, DNS, F1) n'ont pas flanché. Confirme que les vagues tardives peuvent être très sélectives — seuls 1-2 services spike. |
| 31 | ~15:13 | ~15:28 | **Vague complète tardive** : tous les certificats en cascade unavailabled (Los Galactique, Seerr, n8n, Headscale, FreshRSS, Immich, Maps iOS, Pocket-ID, Obsidian LiveSync). Metadonnees flappent. Docker uptimes unavailable. **Recovery spikes** : Seerr 115→1571ms (LB de monitoring), Los Galactique Panel 56→2667ms (spike tardif >1s en recovery). Résorption complète en ~15 min. |
| 32 | ~15:30 | ~15:32 | Vague courte, tous les certificats en cascade + metadonnees (Tags 0tags→unavailabletags, Type de moniteur ping→unavailable, Nom d'hôte surveillé IP→unavailable, Uptime 1d 99.7%→unavailable%). Recovery rapide <5 min avec retour ping→unavailable→ping. |
| 33 | ~15:52 | ~16:06 | **Dernière vague complète de la session (13:56→16:06, ~10 min)**. Spikes précurseurs : LibreTranslate 40→2432ms, Obsidian 37→818ms, Shop LG 160→212ms. Puis cascade complète : 9 certificats unavailabled, uptimes Docker unavailable, sondes pangolin unavailable. Résorption progressive avec ~7 sondes stragglers (db.losgalactique.fr, status.losgalactique.fr, rss.jefe.ovh, app.jefe.ovh, shop.losgalactique.fr, paperclip, argus avg 1d) restant unavailable 2-3 min de plus. Recovery spikes résiduels observés : ntfy 2938→47ms, Immich 743→55ms, Los Galactique Panel 590→66ms. |
| 34 | ~16:06 | ~16:10 | **Vague atténuée (spikes seuls, pas de cascade)**. Pics sur n8n 43→439ms, Los Galactique Panel 53→590→2398ms, Shop LG 140→1348ms, ntfy 34→2938ms, Immich 55→743ms, FreshRSS 105→247ms. Aucun unavailable/unavailabled. <2 min résorption. |
| 35 | ~16:10-16:30 | — | **Micro-aftershocks** (1-3 spikes isolés résorbés dans le même lot HA). Pas de cascade. |
| 36 | ~14:05 session suivante | ~14:12 | **Vague COMPLÈTE (cascade intégrale)**. Certificats unavailabled : Los Galactique Panel, Seerr, n8n, ntfy, FreshRSS, Immich, Shop LG. Sondes pangolin unavailable (SearXNG, argus, ha-mcp, node, ph, anisette, paperless, webdav, demand.jefe.al, rss.jefe.ovh, translate.jefe.ovh, etc.). Uptimes Docker unavailable%. CPU Pangolin 15→20%. Résorption complète en ~5 min. Confirme que le pattern complet peut réapparaître à 36 vagues, contrairement à l'hypothèse d'atténuation définitive post-34. |
| 37 | ~14:13 session suivante | ~14:19 | **Vague COMPLÈTE (cascade intégrale)**. Certificats unavailabled : Los Galactique Panel, Seerr, ntfy, FreshRSS, Headscale, Shop LG, Pocket-ID, Maps iOS. Sondes pangolin unavailable : SearXNG, argus, rss.jefe.ovh, localsync.jefe.al, signal.jefe.al, jellystat.jefe.al, anisette.jefe.al, webdav.jefe.al, paperless, webdav. DNS MX jefe.ovh (AnonAddy) unavailable. Docker probes unavailable : hbbr, webfinger, paperless, immich_redis, wizarr, ntfy, headplane. Uptimes 1d/30d/365d unavailable% sur multiple services. Temps de réponse spikes : Shop LG jusqu'à 2256ms, n8n 1374ms, FreshRSS 1620ms, Los Galactique Panel jusqu'à 172ms, Immich 443ms. Résorption complète en ~6 min (derniers stragglers : headplane `unavailablems→unknownms`, immich_machine_learning `unavailablems→unknownms` à ~14:20). Tous les certificats revenus à 80d. Localsync dernier à revenir `unavailable→up` à ~14:21. |

#### Fin de cycle apparent : silence monitoring post-vague #34 (30+ min calme)

Après les aftershocks de vague #34 (dernier événement anormal vers ~16:08), le flux d'événements HA est revenu à un **état parfaitement calme** pendant **30+ minutes consécutives** (jusqu'à ~16:40+). Aucune vague #35 ne s'est déclarée dans cette session.

C'est le plus long intervalle sans vague depuis le début de la session à 11:33 (~5h de monitoring continu). Les événements se limitaient strictement à :
- Ticks mécaniques (jTower conso +0.001kWh, Freebox +30s, F1 +1min)
- Uptimes longs (variations <0.002%)
- DNS / ping stables (0-5ms)
- Variations normales (SM-A556E batterie, iPhone pas, tension, météo)

**Interprétation probable** : le cycle de vagues peut s'épuiser après un nombre suffisant de cycles consécutifs (34 vagues complètes en ~5h). La cause sous-jacente (probablement une accumulation ou une instabilité dans l'agent Beszel/Uptime Kuma) finit par se stabiliser ou être vidée de son cache. Les agents de monitoring retournent à leur fonctionnement nominal.

> **⚠️ Attention — un silence prolongé ne garantit pas la fin définitive.** Vague #36 est survenue dans une session ultérieure (même jour, 2026-07-13), avec la cascade complète. Le silence peut n'être que temporaire — de nouvelles vagues peuvent réapparaître dans une session suivante sans prévenir.

**Conduite** : aucune action. Le retour au silence confirme a posteriori que les vagues étaient bien des artefacts de la couche de monitoring, sans impact infrastructurel.

**Aftershocks post-vague #33** (= vague #34, après 16:06) :
Après la dernière vague complète, des micro-événements isolés ont été observés :

| Temps | Événement | Résolution |
|-------|-----------|------------|
| ~16:06 | n8n 43→439ms (isolé, pas de cascade) | Résorbé à 40ms après ~2 min |
| ~16:07 | Los Galactique Panel 57→590ms (éclair, résorbé dans même batch) | Résorbé à 57ms instantanément |
| ~16:08 | Los Galactique Panel 57→590ms, puis ntfy 2938ms, puis Immich 743ms (décalés) | Tous résorbés dans la minute |

**Caractéristiques des aftershocks :**
- Affectent 1-3 services max (jamais la cascade complète)
- Résorption en <2 min
- Peuvent être des « éclairs » (spike+recovery dans le même lot HA)
- Aucun artefact résiduel (pas de unavailable, pas d'uptime impacté)
- Ne doivent PAS être comptés comme des vagues complètes dans le décompte

**Attenuation NUANCEE à 34+ vagues :** au-delà d'environ 33 vagues dans une session, le pattern PEUT changer qualitativement. Certaines vagues tardives (vague #34 observée après ~16:06) n'affichent que des spikes de temps de réponse sans la cascade complète de `unavailabled` sur certificats/uptimes/sondes. MAIS ce n'est pas déterministe — la vague #36 (session continue le 2026-07-13) a produit la cascade INTEGRALE (tous les certificats unavailabled, uptimes Docker unavailable, sondes pangolin unavailable, métadonnées flappées) avec tous les artefacts d'une vague précoce. Conduite : ne pas présumer de l'atténuation — vérifier chaque nouvelle vague sur ses propres signes avant de conclure. RAS, résorption spontanée dans les deux cas.

> **Note** : Les vagues 16-17 peuvent apparaitre dans un ordre non-chronologique (vague 17 commence a 12:52, vague 16 a 12:58). C'est normal pour les vagues tardives qui se chevauchent — le comptage ordinal (15e, 16e, 17e) reflete l'ordre dans lequel l'agent les a nommees dans le flux d'evenements, pas necessairement leur chronologie absolue.

| Vague | Debut | Resorption | Pics notables (suite) |
|-------|-------|------------|----------------------|

| 38 | ~15:20 (session #2, post-#37) | ~15:25 | **Vague COMPLÈTE (cascade intégrale)**. Certificats : Los Galactique, n8n, Shop LG, Seerr, ntfy, FreshRSS, Immich, LibreTranslate, Headscale, etc. → unavailabled. Sondes pangolin ping/http → unavailable. Uptimes Docker → unavailable%. Temps de réponse : LibreTranslate 68→679ms, Shop LG 119→2528ms, FreshRSS 111→2294ms, Los Galactique Panel 230→53ms volatile. **n8n spike précurseur** (43→439ms) ~1-2 min avant la cascade. Résorption complète en ~10 min. |
| 39 | ~15:30 | ~15:37 | **Vague COMPLÈTE (cascade intégrale)**. Reprend peu après vague #38. Certificats + uptimes + sondes. Résorption progressive. |
| 40 | ~15:40 | ~15:45 | **Vague COMPLÈTE (cascade intégrale)**. Tous les certificats → unavailabled, sondes → unavailable, uptimes → unavailable%. Résorption. |
| 41 | ~15:50 | ~15:55 | **Vague COMPLÈTE (cascade intégrale)**. Cascade massive : certificats unavailabled (Los Galactique Panel, Seerr, n8n, ntfy, FreshRSS, Immich, LibreTranslate, Shop LG, Pocket-ID, Paperless-ngx, Maps iOS, etc.) + sondes ping/http/TCP → unavailable (Pangolin VPS, AX42 tailnet, home.jefe.al, jNas tailnet, etc.) + uptimes Docker → unavailable% + métadonnées flappées. **Beszel lui-même passe unavailable** (docker: beszel Statut unavailable). **Stragglers intersession confirmés** : ntfy (1430ms) et invite.jefe.ovh (1656ms) non résorbés en fin de session #2 ; résorbés à l'ouverture de session #3. Résorption complète avec spikes tardifs (Seerr 90→102ms, ntfy 50→41ms, etc.). |
| 42 | ~14:45 (session #3) | ~15:10+ | **Vague COMPLÈTE (cascade intégrale)**. Tous les certificats → unavailabled (Shop LG, Seerr, n8n, Headscale, FreshRSS, Los Galactique, Pocket-ID, Immich, etc.). Sondes pangolin → unavailable (paperless.jefe.al, ha-mcp.jefe.al, if.jefe.al, trakii.tv, phpmyadmin, home.jefe.al, webdav.jefe.al, jellystat.jefe.al, etc.). Uptimes Docker → unavailable%. Wings API (local) → unavailable. Tags → unavailabletags. Temps de réponse spikes : FreshRSS 111→2294ms, Shop LG 119→2528ms, Los Galactique Panel 230→53ms volatile. **Beszel unavailable** confirmé. RÉSORPTION N°1 (partielle) vers ~15:05 : certificats → 80d (Shop LG, Los Galactique Panel, Seerr, n8n, FreshRSS), ping → 0ms (AX42 public), certains temps de réponse → unknownms. **RÉCIDIVE** dans les minutes suivantes : les certificats repassent unavailabled, les uptimes/sondes → unavailable. Résorption finale vers ~15:10. Straggler tardif : Obsidian LiveSync 47→2110ms en spike résiduel de recovery. **Confirmation : les vagues peuvent récidiver immédiatement après une résorption partielle — le Beszel reprend puis retombe dans la même session.** |
| 46 | ~15:13 session #5 | ~15:16 | **Vague COMPLÈTE (cascade intégrale)**. Spikes précurseurs beszel.jefe.ovh 38→2162ms. Shop LG 133→2370ms, n8n 39→1408ms, FreshRSS 127→2078ms, Immich 43→758ms. **Shop LG résorbé en premier** (2370→138ms avant que FreshRSS 2078→112ms et Immich 758→47ms ne suivent). Résorption complète <3 min. Contredit le pattern « Shop LG dernier à résorber » — l'ordre de résorption peut varier. Dernière vague de la session #5 avant silence monitoring prolongé. |
| 47 (partielle) | ~15:20 session #5 | session terminée | **Vague PARTIELLE (non confirmée)**. Seerr 105→1050ms + FreshRSS 89→367ms. 2 services spike sans cascade certificats/uptimes. Session terminée avant résorption ou confirmation de cascade complète. Possible début de vague avorté ou double-spike isolé. |
| 48 (partielle) | ~15:25 session #6 | ~15:35 | **Vague COMPLÈTE (cascade intégrale)**. Cascade massive : certificats unavailabled (Los Galactique Panel, Shop LG, Seerr, n8n, ntfy, FreshRSS, Immich, Termix, etc.), uptimes Docker unavailable%, sondes pangolin unavailable, métadonnées flappées. Spikes : Shop LG 142→849ms précurseur, n8n 43→207ms, ntfy 37→1718ms. Résorption : certificats 80d + Seerr, Los Galactique Panel stables dans les ~10 min. Aftershocks résiduels : Obsidian LiveSync 2463ms post-recovery. |

#### Vagues enchainees
Apres la 13e vague, la recovery n etait pas completement terminee que la 14e vague a demarre. Les vagues peuvent donc s enchaner quasi immediatement, sans la fenetre de 3-8 min observee plus tot dans la sequence. Le monitoring restaure peut retomber instantanement. Ne pas s alarmer — le pattern reste le meme (resorption spontanee).

#### Selectivite des vagues tardives (25+)

A partir de ~25 vagues dans une session, un nouveau pattern de **selectivite** apparait : tous les services ne sont plus impactes uniformement. Certains services subissent des spikes massifs (>1000ms) pendant que d'autres restent proches de leur baseline.

| Groupe | Services typiques | Comportement en vague tardive |
|--------|------------------|-------------------------------|
| **Fortement impactes** | Immich, Seerr, ntfy, Los Galactique Panel, Pocket-ID | Spikes reguliers >1000ms (parfois >3000ms) |
| **Peu/moyennement impactes** | FreshRSS, n8n, LibreTranslate, Obsidian LiveSync, Shop LG | Spikes <200ms ou absents, parfois micro-pics residuels |
| **Stables** | Headscale, DNS (tous), Freebox, jTower, F1, Pangolin CPU/RAM | Inchanges ou bruit <10ms |

**Interpretation** : il ne s'agit pas d'une amelioration reelle de l'infrastructure ou certains services deviendraient plus resilients. C'est un artefact du comportement des sondes tardives — certains monitors Beszel/Uptime Kuma cyclent plus vite et tombent/recovery plus frequemment, d'autres « tiennent » plus longtemps avant de flapper. Le pattern exact de qui spike peut varier d'une session a l'autre.

**Conduite** : ne pas interpreter la selectivite comme une preuve que certains services sont plus robustes que d'autres. Continuer de pointer les stables (Freebox, jTower, DNS, F1) comme indicateurs de confiance. La resorption reste spontanee pour l'ensemble.

#### Vagues ultra-courtes : spike+recovery colocalises (21+)

A partir de la ~21e vague, un nouveau degre d'acceleration peut apparaitre : **les evenements de spike et de recovery arrivent dans le meme lot HA** (meme timestamp logique). Exemple vague 21 :

- Los Galactique Panel : `82->824ms` ET `824->55ms` dans la meme rafale
- n8n : `36->2111ms` ET `SSH jNas: unknownms->43ms` simultanement
- Certificats qui tombent (`unavailabled`) et reviennent (`80d`) en alternance dans le meme flux

**Ce n'est pas une escalade** — c'est le cycle sonde/resorption qui s'est accelere au point que les deux phases se telescopent. Conduite inchangee : identifier la vague, pointer les stables (Freebox +30s, jTower, DNS <10ms, F1 +1min), attendre la resorption complete (generalement <3 min).

### Signes distinctifs

- Beszel lui-même (`docker: beszel Statut`) passe de `up` à `unavailable` — c'est le **signal le plus fort** que la vague est une panne de la couche de monitoring, pas des services.
- Les monitors `docker:` (beszel-agent, glance, vaultwarden, etc.) sont
  systematiquement touches.
- Les monitors `pangolin:` (SSL certifs + HTTP) sont aussi touches.
- Les monitors `DNS A/MX` et `Ping` le sont de maniere plus variable.
- Les services **non sondes** (Freebox temps de fonctionnement, jTower
  compteurs, F1 horloge) ne sont JAMAIS impactes.
- **Les metriques DNS agregees** (`ALL Requetes DNS`, `ALL Requetes DNS bloquees`,
  `ALL Requetes DNS-over-HTTPS`, `ALL Taux IPv6`) continuent de s incrementer
  pendant les vagues — le DNS est sain, seules les sondes flappent.
- **Shop LG est le premier a grimper et le dernier a resorber** : c est un
  indicateur precoce fiable de debut/resorption de vague.
- **Uptime erosion asymetrique** : l erosion d uptime 30j n est pas uniforme.
  Certains services (ex: jflix) perdent ~0.004% par vague contre ~0.002% pour
  la moyenne. En cumul sur 24 vagues, jflix a perdu ~0.09% (99.28% → 99.19%).
  Ce n est pas un signe d escalade — certains monitors mettent plus longtemps
  a revenir dans la file de verification et accumulent plus de downtime.
- **Progression `down → unavailable`** : l'inverse du recovery — un service déjà en `down` (confirmé éteint par la sonde) peut passer à `unavailable` (sonde ne le joint plus) pendant une vague. C'est un signe de progression de vague, pas d'escalade réelle. La sonde qui pouvait au moins confirmer l'état éteint du service n'arrive même plus à le sonder.
- **Recovery vers down** : un monitor peut revenir de `unavailable` a `down`
  (pas `up`). Cela signifie que la couche monitoring est a nouveau operationnelle
  et que le service est effectivement injoignable — un diagnostic plus precis que
  `unavailable`. Exemple : hermes.jefe.al est passe de `unavailable` a `down`
  apres la 17e vague. A ne pas confondre avec une escalation.
- **Resorption partielle (Beszel encore unavailable)** : des certificats (Shop LG,
  etc.) peuvent revenir de `unavailabled` a `80d` alors que `docker: beszel` est
  toujours `unavailable`. C'est normal — les metriques cachees/certificats peuvent
  etre servies depuis HA ou un replica partiel, independamment du Beszel central.
  Ne pas interpreter comme un retour complet. Attendre Beszel `unavailable -> up`.
- **CPU Pangolin post-vague** : apres une vague intense, le CPU Pangolin peut
  rester eleve (~19-23%) pendant 5-15 min avant de revenir a sa baseline
  (~13-16%). Cela reflete le traitement differe des sondes qui reviennent
  (verifications, mises a jour de cache). Pas un signe d escalade.
- **Pics reseau jNas en vague intense** : en vague intense (14+), le trafic
  reseau jNas peut picquer significativement : Network Receive jusqu'a ~9 MB/s
  et Network Send jusqu'a ~4 MB/s (observe vague 14 et 19). Ces bursts sont
  attribues a l'activite de verification/mise a jour des agents de monitoring.
  Les valeurs basales (~35-50 kB/s RX/TX) reviennent avec la vague.
- #### Recovery d'uptime vers une valeur <100% (hors érosion de vague)

Quand un uptime revient de `unavailable%` vers une valeur significativement inférieure à 100%
(sans être de l'érosion de vague classique) :

- Exemple : `wizarr Uptime (30d): unavailable% → 87.28%`
- L'uptime avant la vague était déjà <100% (wizarr à ~87% avant unavailable)
- La valeur de retour reflète l'uptime réel avant indisponibilité, pas une dégradation supplémentaire
- RAS — l'uptime reprend là où il s'était arrêté, sans perte additionnelle

**Conduite** : Ne pas s'alarmer d'une reprise <100%. Vérifier que la valeur est
similaire à celle d'avant la vague (vague suivante ou historique session récente).
Si c'est le cas, la recovery est propre.

#### Recovery Response time Ø (30d) vers 0.0ms

Observation : `immich_server Response time Ø (30d): unavailablems → 0.0ms`

L'agrégat 30d peut revenir à `0.0ms` au lieu d'une valeur réelle. C'est un artefact
du compteur d'agrégation qui redémarre à zéro après une indisponibilité prolongée —
la valeur réelle réapparaîtra au prochain cycle d'agrégation (généralement au tick
suivant). RAS — pas un signe que le service est à 0ms de temps de réponse.

**Érosion extreme sur services rarement verifies** : certains services dont
  les uptimes 30j sont construits sur un petit nombre de verifications peuvent
  afficher une erosion disproportionnee. Exemple observe : FiveM LosGalactiqueRp
  Uptime 30j revenu a seulement 20.5% apres 24+ vagues, car les ~80% de temps
  ou la sonde etait « unavailable » dominent statistiquement l'echantillon.
  Ce n'est pas un signe de probleme du service reel — un uptime « reel » de 99-100%
  hors vagues est normal pour ce service, mais la fenetre 30j a ete dominee par
  les sondes mortes. Conduite : RAS, la valeur remontera avec le temps si les
  vagues cessent.
- **Hermes 365d erosion massive (pattern distinct)** : contrairement aux autres uptimes 365d qui restent quasi inchanges (<0.001% de bruit) pendant les vagues, `hermes.jefe.al Uptime (365 days)` peut perdre ~0.18% en une session de vagues intenses. Raison : l'uptime reel d'Hermes sur 365j est deja bas (~57%) a cause du cumul de toutes les vagues precedentes — chaque nouvelle vague ajoute du vrai downtime dans une fenetre ou le ratio signal/bruit est defavorable. C'est une exception au pattern general. Conduite : RAS, c'est attendu.
- **Uptime 1d → 0.0% apres recovery** : certains monitors (ex: FiveM) peuvent
  revenir de `unavailable%` à `0.0%` au lieu d'une valeur normale (~99.7%).
  C'est un artefact du compteur 1d qui redemarre de zero apres une coupure
  complete de la sonde. Le service est fonctionnel — la valeur remontera
  avec le temps dans l'heure suivante. RAS.

## Cause racine presumees

Non identifiee precisement. Hypotheses :
1. Surcharge transitoire du serveur Beszel ou de sa base de donnees
2. Intermittence de l agent Beszel sur le Docker host
3. Uptime Kuma qui regenere son cache ou fait un refresh massif
4. Contention sur le socket Docker (le daemon etait inaccessible)

## Diagnostic differentiel

| Symptome | Cause monitoring | Vrai probleme |
|----------|-----------------|---------------|
| Certificats 80d -> unavailabled en masse | ✓ | ✗ |
| Uptimes Docker -> unavailable en masse | ✓ | ✗ |
| Freebox continue +30s | ✓ (rassurant) | ✗ |
| Un seul service en timeout (autres OK) | ✗ | ✓ |
