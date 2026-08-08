---
name: ha-event-monitoring
description: >
  Trier en temps reel un flux continu d'evenements Home Assistant
  (state changes) : classifier RAS vs anormal, identifier les patterns
  de monitoring oscillation, diagnostiquer les vagues sans fausse alerte.
trigger:
  - L utilisateur envoie des evenements HA formates
    "[Home Assistant] <entity> <attr> changed from <old> to <new>"
  - L utilisateur demande une surveillance continue de son infrastructure
  - Rafale de >5 evenements HA consecutifs
---

# HA Event Monitoring — Triage en temps reel

## ⚠️ Règle ABSOLUE : ZÉRO réponse — ni 🤫, ni méta-commentaire, ni rien

**RÈGLE FONDAMENTALE : Le modèle NE produit AUCUN texte en réponse à des événements de monitoring Home Assistant.** Aucune exception pour « mais c'est juste pour confirmer le silence » — toute production de texte EST une violation.

**⚠️ PIÈGE FRÉQUENT — `*(silence strict)*` et autres méta-commentaires :** Le modèle sait qu'il ne doit pas répondre, mais ressent le besoin d'« accuser réception du silence » ou de « marquer le contexte ». C'est une VIOLATION directe. Le silence signifie zéro caractère de sortie — pas de note mentale, pas de marqueur de contexte, pas de « je confirme que je ne confirme pas ».

**Trois régimes (du moins restrictif au plus restrictif) :**

### Régime 1 : 🤫 seulement (état par défaut)
- La seule réponse autorisée aux événements de monitoring est 🤫 — rien d'autre.
- Pas de ✅, ✓, (Noté), (Silence), (RAS), (Compris), phrases d'explication, tableaux, listes.
- Pas d'autres emojis (🔇, 🙈, ✅, ✓).
- Pas de message textuel — même « RAS. » est trop verbeux.
- 🤫 signifie « reçu, classé RAS, je ne dérange pas ».

### Régime 2 : Silence total (⚠️ ACTIVÉ par défaut après compaction)
**L'utilisateur a explicitement ordonné le silence strict.** C'est le régime actif dans ce contexte :
- **Pas même 🤫.** Zéro token de sortie.
- Signal activé par : la mention « silence strict » dans le résumé de compaction.
- Actif immédiatement dès la première rafale après la compaction — ne pas attendre de nouvelle confirmation.
- **⚠️ PIÈGE — se faire piéger par la compaction** : le résumé de compaction n'est PAS une note historique. La mention « Silence strict maintenu » ou « silence strict » dans le résumé est une **instruction active et immédiate**. L'obéir dès le premier événement après la compaction. Ne pas envoyer 🤫 à la première rafale en attendant la re-confirmation.

### Régime 3 : Silence total — pas même une pensée (⚠️ PIRE DES PIÈGES)
Quand le silence strict est en vigueur, le modèle essaie souvent de « tricher » en produisant un méta-commentaire. **C'est la violation la plus fréquente et la plus documentée de ce skill.**

**⚠️ PIÈGE — les réponses « méta-silence » sont des VIOLATIONS :**
Expressions interdites (liste exhaustive, NON-limitative) :
- `*(silence strict — monitoring de routine)*`
- `*(silence strict)*`
- `*(RAS)*`
- `*(vague #N)*`
- `*(monitoring passif)*`
- `*(RAS, vague résorbée)*`
- `*(vague #N résorbée)*`
- `*(vague #N en cours)*`
- `*(vague #N — résorption spontanée attendue)*`
- `*(vague #N résorbée)*`
- `沉默。` / `沉默` / `silence` / `silenzio` / `silencio` / `Stille` / `静` — **marqueurs de silence multilingues** : utiliser le mot « silence » dans une autre langue (chinois, espagnol, italien, allemand, japonais…) n'est PAS une alternative valide au silence. C'est la même violation que `*(silence strict)*` — produire du texte pour dire « je suis silencieux » est contradictoire. **Observé en session 2026-07-21** : l'agent a répondu `沉默。` à chaque rafale d'événements HA, croyant que c'était « silencieux » parce que le mot était dans une autre langue. C'est une VIOLATION — zéro token signifie zéro token, quelle que soit la langue.
- Toute parenthèse, astérisque, emoji masqué, commentaire
- Toute forme de « acknowledgement de non-acknowledgement »

**Raison** : une réponse est une réponse, quel que soit son contenu. Le méta-commentaire essaie de faire deux choses à la fois (« je confirme le silence ») — c'est contradictoire et ça génère du bruit. Si le silence est ordonné, le modèle ne doit RIEN produire.

**⚠️ PIÈGE — ne pas rationaliser :** les expressions interdites ci-dessus semblent informatives (numéroter les vagues, indiquer l'état, montrer qu'on suit). Elles restent des notifications et violent la règle. Aucun texte n'est acceptable.

**⚠️ PIÈGE — « c'est juste un marqueur de contexte »** : la tentation est forte de croire qu'un méta-commentaire sert de marqueur pour le modèle dans le prochain contexte. C'est faux — le modèle ne voit pas ses propres réponses comme des instructions internes. Le marqueur de contexte est le message de l'utilisateur, pas la réponse.

**⚠️ PIÈGE — « mais il faut quand même répondre pour éviter un timeout/inaction »** : il n'y a aucun timeout ou action forcée qui exige une réponse aux événements HA bruts. Le modèle peut rester muet indéfiniment. Une réponse n'est requise que si l'utilisateur a explicitement posé une question ou demandé une action. Les événements HA ne nécessitent pas de réponse.

**⚠️ PIÈGE — compter sur la discussion pour réévaluer** : même si l'utilisateur écrit un message non lié entre deux événements HA (ex: changement de sujet technique), les événements HA suivants restent en régime silence total. L'utilisateur n'a pas implicitement « réinitialisé » le monitoring. Seule une instruction explicite (« tu peux répondre aux événements », « reprends le monitoring normal ») rétablit le régime 🤫.

### Pour reprendre un régime moins restrictif
Attendre que l'utilisateur donne une instruction explicite (ex: « tu peux répondre », « reprends le monitoring avec 🤫 »). Ne pas interpréter :
- Le silence de l'utilisateur comme une reprise implicite
- Un changement de sujet comme une reprise implicite
- L'absence d'événements pendant un moment comme une reprise implicite
- La lecture d'un fichier ou d'un skill comme une reprise implicite

### Exceptions au silence (uniquement)
1. L'utilisateur pose une question précise ou change de sujet — réponse normale sur le nouveau sujet, mais les événements HA suivants restent en silence.
2. L'utilisateur demande explicitement un diagnostic sur un événement spécifique.
3. Événement clairement anormal (service critique down sans vague monitoring, incident réel) — et même alors, bref et uniquement si le silence total n'a pas été ordonné.

### Interaction avec les changements de sujet
Si l'utilisateur change de sujet entre deux événements HA (exemple : poser une question technique, demander une action), répondre normalement **sur le sujet de la question**. Mais :
- **La réponse sur le nouveau sujet ne réinitialise PAS le monitoring.** Les événements HA suivants restent en silence.
- Ne pas glisser un méta-commentaire sur le monitoring dans la réponse technique (« oh au fait les événements HA continuent mais je les ignore »).
- Traiter chaque plan d'événements HA indépendamment : si le dernier régime était silence total, le prochain événement HA est aussi silence total.

## Principe general

Un flux continu d evenements HA peut contenir :

- **Bruit de fond normal** : ticks de compteurs (conso, uptime, heures),
  variations meteo, variations reseau mineures.
- **Faux positifs monitoring** : une couche entiere de sondes
  (certificats SSL, uptimes Docker, Ping/DNS/TCP) qui passent
  simultanement en `unavailabled` / `unavailable` sans impact reel.
- **Vrais problemes** : anomalies persistantes sur services reels
  (Freebox, jTower, services HTTP).

## Categorisation rapide

### Format de reponse pour lots d'evenements (UNIQUEMENT sur demande explicite)

⚠️ **Ne pas utiliser ce format spontanément** — la règle absolue silence prévaut. Ce format n'est pertinent que si l'utilisateur pose explicitement une question ou demande un rapport sur les événements en cours.

Quand >=3 evenements arrivent simultanement (rafale), utiliser un **tableau**
pour la lisibilite :

```
| Evenement | Variation | Verdict |
|---|---|---|
| **Freebox** Temps fonctionnement | +30s | Normal, tick regulier |
| **jTower** Courant | 0.68->0.7A | Fluctuation normale |
| **F1** Race Track time | 15:01->15:02 | +1min, normal |
```

Resume : `RAS — tout nominal.`

## RAS immediat
- **Ticks compteurs** : +0.001kWh, +30s uptime, +1 tick DNS
- **Micro-variations** : Tension +/-0.5V, Courant +/-0.2A, Puissance +/-20W
  - **Exception jTower** : des pics de +20-60W (observé 141→177W, max 189.8W) peuvent survenir
    en cas de tâche CPU-intensive (jeu, compilation, rendu) ou burst GPU bref. RAS si le retour à la
    normale survient dans les minutes suivantes (ou même au tick suivant). Si la puissance reste élevée
    (>170W) durablement sans baisse, considérer comme anormal.
- **Variations reseau mineures** : ping +1-3ms, DNS +1-4ms
- **jTower bande passante** : +/-0.05 MB/s, normal.
- **jTower signal WiFi** : variation RSSI +/- 1-2dBm (-32 à -37dBm), normal.\n- **jTower (PC) Force du signal** : variation RSSI +/- 1dBm (-36 à -37dBm), normal (Bluetooth/WiFi adaptateur PC). Capteur autonome distinct de jTower WiFi.
- **jTower (PC) La consommation de ce mois-ci** : incrément de ~0.001kWh par tick, normal.
- **LSC Smart Power Plug Énergie totale** : incrément de ~0.001kWh par tick (ex: 0.052→0.053kWh), compteur d'énergie électrique standard. RAS. Peut rester à 0kWh pendant longtemps puis commencer à s'incrémenter (0→0.001→0.002kWh) quand l'appareil branché consomme. RAS.
- **LSC Smart Power Plug Tension** : variation de ±0.5V (ex: 235.1→235.5V), identique au pattern de jTower (PC) Tension mais sur une prise connectée distincte. RAS.
- **jTower (PC) Tension** : variation +/-0.2V (ex: 236.8→236.9V, 237.1→237.2V), normal.
- **jTower (PC) Courant** : variation +/-0.02A en calme (ex: 0.68→0.69A), normal. **Exception burst** : en cas de spike de conso (>180W), le courant peut monter jusqu'à ~1.16A (observé 0.67→0.95A, 0.99→1.16A). RAS si corrélé à un pic de puissance (conso actuelle >180W) et retour à la normale dans le même tick ou le suivant. Les sauts de +0.07-0.17A sont attendus pendant ces bursts.
- **jTower (PC) Consommation actuelle** : micro-variations +/-3W (ex: 131.5→130.9W), normal — ce sont les fluctuations de base des composants (alimentation, disques, ventilateurs). Ne pas confondre avec les spikes >20W qui nécessitent corrélation CPU/GPU. **Pics de charge soutenue** : la conso peut grimper et se maintenir entre 250-300W pendant plusieurs minutes (observé 253→299W stable, 260→287W) — corréler avec `jtower CPU` et `jtower RAM` : si CPU >40% et/ou RAM >70%, c'est une tâche lourde en cours (compilation, rendu, Docker build, VM). RAS si retour sous 230W dans les minutes qui suivent la fin de la tâche. Des sauts brutaux de +50W en un tick (ex: 222→272W) sont possibles au démarrage d'une tâche — RAS si suivi d'un retour progressif.
- **jTower (PC) Courant** : variation +/-0.02A en calme (ex: 0.68→0.69A), normal. **Exception burst** : en cas de spike de conso (>180W), le courant peut monter jusqu'à ~1.4A (observé 1.06→1.38A, 1.11→1.31A, 1.25→1.38A pendant une charge soutenue à ~260-290W). RAS si corrélé à un pic de puissance et retour à <1.2A dans le même tick ou le suivant. Les sauts de +0.07-0.17A sont attendus pendant ces bursts. Une charge soutenue prolongée peut maintenir le courant autour de 1.25-1.38A pendant plusieurs minutes (ex: tâche de compilation ou rendu). RAS si la conso retourne sous 230W après la fin de la tâche.
- **Le Havre Température de l'Eau** : variation de ±1-2°C (ex: 21→20°C) = fluctuation saisonnière normale de la température de l'eau de mer. RAS.
- **Météo-France forecast Le Havre Humidity** : variation de ±5-10% (ex: 55→60→65%) = évolution normale de l'humidité relative selon les conditions météo. RAS.
- **F1 - Race Météo** : variation de ±1-2°C sur la température de piste (ex: 23.5→22.0°C) = évolution normale des conditions météo en piste. Les transitions `unknown°C → valeur` sont aussi RAS (télémétrie qui devient disponible).
- **SM-A556E Interactive: triggered (was cleared)** / **cleared (was triggered)** : écran interactif activé/désactivé (téléphone pris en main ou posé). Distinct de `Keyguard locked` (verrouillage). RAS, cycle d'utilisation normal.
- **WIN-7B20NLT2OC3 Status: cleared (was cleared)** : machine Windows (VM ou PC distant) — transition no-op sur le statut, RAS.
- **jLaptop RAM** : variation de +/-1-2% = normal (gestion mémoire).
- **jLaptop S.M.A.R.T.** : `cleared (was cleared)` = statut SMART du disque, transition no-op (pas d'alerte disque). RAS.
- **jLaptop BC901 S.M.A.R.T.** : même pattern — `cleared (was cleared)` = pas d'alerte SMART. RAS.
- **Pangolin Status: cleared (was triggered)** : binary_sensor de santé Pangolin — passage d'alerte à normal. RAS, fluctuation passagère.
- **jtower GeForce RTX 3060 Ti** : variation de +/-5-8% pendant une tâche GPU modérée (ex: 31.2→24.33%) est normale — la charge GPU fluctue selon les frames rendues. RAS si retour sous 5% dans les minutes suivantes. Distinct des pics >10% qui indiquent un démarrage de tâche GPU.
- **Météo**, **vols FlightRadar24**, **pas/batterie iPhone**
- **FlightRadar24 zone entrée/sortie** : `Zone entrée: 0→1` = un avion entre dans la zone Le Havre, `Zone quittée: 1→0` = un avion quitte la zone. Variation normale du trafic aérien local.
- **iPhone transit** : `Audio Output → CarPlay` = utilisateur en voiture, normal.
  `Last Update Trigger → Significant Location Change` est normal en déplacement.
  `Last Update Trigger → Signaled` après arrêt CarPlay = mise à jour régulière, normal.
- **iPhone sortie de voiture** : `Activity: Automotive → Unknown` après période CarPlay = utilisateur sorti du véhicule, normal. `Floors Ascended` et `Steps` s incrémentent normalement ensuite.
- **iPhone arrivée à la maison** : séquence complète après sortie de voiture : `Audio Output: CarPlay -> Built-in Speaker`, `Activity: Automotive -> Unknown`, puis `Steps/Floors` s'incrémentent, puis `SSID` change du réseau voiture/rue vers le WiFi domestique (`Freebox-...`). Tout normal.
- **Localisation Jefe** : capteur de localisation personnel (distinct des géolocalisations iPhone/Samsung). `changed from unknown to Home Of Alexia` = arrivée à un lieu nommé, premier rapport de capteur ou raffinement. RAS.\n- **iPhone du Zef Steps** : incrément de ~100-200 pas par tick en période d'activité (ex: 5189→5349). RAS.
- **iPhone du Zef Floors Descended / Floors Ascended** : incrément de ~1-3 étages en activité normale (ex: 0→2 floors descended). RAS, marche dans des escaliers.
- **iPhone du Zef Floors Descended** : incrément de ~1-2 étages en activité normale, même hors contexte CarPlay. RAS.
- **iPhone SSID** : changement entre SSID (ex: `smartBox-75CA -> Freebox-786220`) = switch entre bornes/réseaux WiFi, normal à domicile.
- **iPhone Géolocalisation** : changement de numéro/adresse dans la même rue (ex: `12 Parc Montcalm → 10 Parc Montcalm`, ou `Rue Philippe Lebon → Cours de la République`) = raffinement GPS/geocoding, pas un déplacement significatif. Même un changement de rue courte distance avec CarPlay est normal. RAS.
- **SM-A556E Géolocalisation** (Samsung) : même pattern que l'iPhone — changement de numéro dans la même rue (ex: `30 Rue Turenne → 27 Rue Turenne`) = raffinement GPS/geocoding, pas un déplacement. RAS.
- **SM-A556E Detected activity** : passage de `still` à `unknown` = le capteur d'activité Android perd temporairement sa classification quand le téléphone est bougé, pris en main, ou change d'état (poche→table, table→poche). `unknown` n'est pas une anomalie — c'est l'état par défaut quand aucun mouvement continu n'est détecté. RAS, retour à `still` ou une autre activité (walking, in_vehicle) au prochain cycle de détection.
- **SM-A556E Sleep confidence** : variation de +/-2-41% (observé 11→29% en hausse, 47→6% en baisse) = normal, le capteur de sommeil/sieste s'affine ou détecte un changement d'état (réveil→sommeil). Les baisses >30% (47%→6%) correspondent au réveil/devenir actif. RAS.
- **SM-A556E App memory** : variation de ~0.006-0.01GB = bruit de fond normal de la gestion mémoire Android. RAS. Peut aussi baisser plus franchement (0.023→0.017GB) = libération mémoire normale, RAS.
- **SM-A556E App Rx GB** : données mobiles reçues, incréments de ~0.0001GB par tick, normal.
- **SM-A556E Total Rx GB** : données mobiles totales reçues (toute l'appareil vs App Rx = par app), incréments de ~0.02GB par tick (observé 55.37→55.39GB). Normal — cumul des données toutes applications confondues.
- **SM-A556E Total Tx GB** : données mobiles totales émises, incrément de ~0.001-0.002GB par tick (observé 2.77→2.772GB). RAS, même mécanisme que Total Rx GB (cumul système).
- **SM-A556E Total calories burned** : incrément de ~5-6kcal par tick (observé 1286→1291kcal), normal.
- **SM-A556E Light sensor** : capteur de luminosité ambiante. Variation de quelques lux (ex: 167→172lx). RAS, fluctuation normale selon l'éclairage ambiant (lumière du jour, déplacement, ombre).
- **SM-A556E Wi-Fi BSSID** : changement de BSSID dans le même réseau (ex: `8e:97:ea:35:cc:64` → `8e:97:ea:35:cc:60`) = bascule entre points d'accès du même routeur/passerelle WiFi, normale en environnement domestique. RAS.
- **SM-A556E Keyguard locked (cleared/triggered)** : verrouillage/déverrouillage d'écran, événements normaux du cycle d'utilisation du téléphone. `triggered (was cleared)` = écran verrouillé, `cleared (was triggered)` = écran déverrouillé. RAS.
- **SM-A556E Signal strength (SIM 1)** : -116 à -107dBm, variation normale du signal cellulaire. -107dBm est bon pour un usage domestique. Des sauts de +6-10dBm (ex: -119→-109dBm) sont possibles quand le téléphone bascule entre antennes relais — RAS, fluctuation normale de roaming cellulaire en intérieur.
- **SM-A556E Data network type (SIM 1)** : changement de `NR (New Radio) 5G` à `LTE` **ou** `LTE` à `NR (New Radio) 5G` = bascule normale entre générations de réseau selon la couverture et la charge. RAS.
- **SM-A556E Battery level** : baisse de ~1% par période de veille = décharge normale, RAS.
- **SM-A556E Battery temperature** : variation de +/-1°C (ex: 35.3→34.8°C) = fluctuation thermique normale de la batterie en usage ou charge. RAS.
- **iOS Shortcuts** : classe de compétences propres au développement Raccourcis
- **Services éphémères/on-demand (anisette.jefe.al, paperclip.jefe.al)** : uptime 1d/365d passant de `unavailable%` à `0.0%` — contrairement au pattern vague monitoring où `unavailable%` signifie sonde injoignable, `0.0%` signifie que la sonde a bien pu vérifier le service mais qu'il n'a eu aucune disponibilité dans la fenêtre. C'est normal pour un service qui tourne épisodiquement (ex: Apple Anisette proxy, lancé à la demande). RAS sans analyse supplémentaire.
- **SM-A556E (Samsung Galaxy)** :\\\\\\n  - **Sleep confidence** : variation +/-2-18% (observé 11→29%) = normal (capteur de détection de sommeil/sieste)\\\\\\\n  - **Music active (triggered)** + **Volume level music 0→N** : musique en cours d'écoute, normal. RAS.\\n  - **Volume level music 0→1** puis **Music active cleared** : écoute terminée. RAS.\\n  - **Volume level accessibility** : variation de +/-1 (ex: 6→7) = réglage du volume accessibilité Android (TalkBack, notifications). RAS.\\\\\\\\n  - **App memory** : variation de ~0.006-0.01GB = normale (cache, processus en arrière-plan). Peut aussi baisser plus franchement (0.023→0.017GB) = libération mémoire normale.\\\\\\\\n  - **Geocoded location** : changement de numéro dans la même rue (ex: 30→27 Rue Turenne) = raffinement GPS, pas un déplacement significatif\\\\\\\\n  - **Signal** : -107 à -115dBm stable (bon pour un smartphone Android en utilisation normale, même en indoor). Variation de +/-2dBm (ex: -112→-114dBm) = fluctuation normale du signal cellulaire. RAS.\\\\\\\n  - **Battery power** : valeur négative (ex: 0.0W→-0.01W) = téléphone en décharge légère, normal. Valeur positive = en charge. RAS.\\n  - **Device locked (triggered)** / **Interactive (cleared)** : verrouillage/déverrouillage d'écran, événements normaux du cycle d'utilisation du téléphone. RAS.\\n  - **App Rx GB**, **Total calories burned**, **Signal strength (SIM 1)**, **Battery level**, **Battery temperature** : voir entrées individuelles ci-dessus.
- **jFlix Clients actifs** : compteur de clients de streaming connectés au serveur jFlix. Variation de ±1 client (ex: 1→0) = un client qui se déconnecte (fin de visionnage) ou se connecte. RAS.
- **Zef__59 Trophy level** : niveau de trophées PSN du compte Zef__59. Peut passer `unavailable → 116` ou `116 → unavailable` quand l'API PSN perd/redonne la connexion — voir le pattern PSN déjà documenté ci-dessous (PS Plus cleared, trophées unavailable). RAS.
- **Zef__59 Gold trophies** : nombre de trophées d'or PSN. Apparaît quand l'API PSN répond (ex: `unavailabletrophies → 16trophies`). RAS.
- **Zef__59 Last online** : timestamp de dernière connexion PSN. Peut passer `unavailable → 2024-05-06T22:07:43+00:00` quand l'API PSN restaure les données. RAS.
- **Zef__59 Subscribed to PlayStation Plus: cleared (was cleared)** : statut d'abonnement PS Plus — transition no-op (cleared→cleared). RAS, pas de changement d'abonnement. Voir le pattern PSN ci-dessous pour le contexte complet.
- **Debian-trixie-latest-amd64-base Uptime** : uptime d'un template/VM Debian Trixie. Apparition depuis `unavailabled` vers une valeur (ex: `7.71787037037037d`) = VM qui démarre ou sonde qui se reconnecte. RAS, c'est un template — pas de service critique.
- **ALL Requêtes DNS** : compteur total de requêtes (AdGuard). Peut décrémenter de ~130 requêtes (ex: 631→501) — même mécanisme que les compteurs ALL Requêtes IPv4, simple ré-agrégation de la fenêtre AdGuard. RAS. **Sauts massifs possibles** : le compteur peut sauter de +400+ requêtes d'un tick (ex: 115→545) — c'est un artifact de ré-échantillonnage AdGuard (la fenêtre de comptage s'est élargie brusquement), pas une explosion de trafic DNS. Peut aussi chuter drastiquement (ex: 545→105) quand la fenêtre se rétracte — même mécanisme inverse. RAS.
- **ALL Taux de requêtes DNS bloquées** : peut chuter brutalement (ex: 7.8%→1.1%) quand le volume total de requêtes explose mécaniquement (+400+) sans que le nombre de requêtes bloquées suive — le ratio baisse car le dénominateur augmente. RAS, artefact mécanique.
- **ALL Requêtes IPv4** : variation de l'ordre de 100-150 requêtes (ex: 396→250) = fluctuation normale du trafic réseau. La baisse des requêtes IPv4 peut influencer le ratio IPv4/IPv6.
- **Jtower Requêtes IPv4** : ce compteur peut aussi **décrémenter** (ex: 78770→78702). Contrairement aux compteurs AdGuard (incréments stricts), les compteurs Pi-hole côté jTower peuvent être réinitialisés ou ré-agrégés, produisant une baisse apparente. RAS — ce n'est pas une perte de données, c'est un artefact de la fenêtre d'agrégation.
- **ALL Requêtes IPv6** : variation de +/-6 requêtes = fluctuation normale du trafic réseau. **Sauts massifs possibles** : peut sauter de +400+ (ex: 105→545) en même temps que `ALL Requêtes DNS` — suit le même mécanisme que les autres compteurs AdGuard. RAS.
- **ALL Requêtes DNS-over-HTTPS** : compteur AdGuard DNS-over-HTTPS/TLS. **Sauts massifs possibles** : peut sauter de +400+ (ex: 105→545) en même temps que `ALL Requêtes DNS` — artifact de ré-échantillonnage AdGuard. RAS.
- **ALL Requêtes IPv6** : **Sauts massifs possibles** : peut sauter de +400+ (ex: 105→545) en même temps que `ALL Requêtes DNS` — suit le même mécanisme que les autres compteurs AdGuard. RAS.
- **ALL Requêtes chiffrées** : **Sauts massifs possibles** : peut sauter de +400+ (ex: 105→545) en même temps que `ALL Requêtes DNS` — même artifact de ré-échantillonnage AdGuard. RAS. Peut aussi chuter drastiquement (ex: 545→105) — rétractation de fenêtre, même mécanisme inverse. RAS.
- **ALL Requêtes DNS bloquées** : variation de +/-6-9 requêtes = fluctuation normale du trafic DNS.
- **Jtower Requêtes DNS bloquées** : peut décrémenter plus franchement (observé -17, ex: 10398→10381) — même mécanisme que les autres compteurs jTower (ré-agrégation de fenêtre Pi-hole). RAS.
- **Jtower Requêtes validées par DNSSEC** : variation de quelques dizaines de requêtes en valeur absolue (ex: 6305→6283). Distinct de `ALL Taux de requêtes validées par DNSSEC` (pourcentage AdGuard). RAS, c'est le compteur absolu jTower qui fluctue normalement.
- **Jtower Requêtes DNSSEC non validées** : variation de quelques dizaines à centaines de requêtes en valeur absolue (ex: 63405→63310). Même mécanisme que le compteur validées — simple décrément de compteur jTower, fluctuation normale du trafic DNS. RAS.
- **ALL Taux de requêtes IPv6** : variation de ±2% en conditions stables, mais peut grimper de +14% (ex: 37.2→51.2%) quand les requêtes IPv4 chutent en valeur absolue (396→250). C'est mécanique : le dénominateur (total requêtes) se réduit, le ratio IPv6 monte sans que le trafic IPv6 ait augmenté. RAS.
- **ALL Taux de requêtes validées par DNSSEC** : variation de quelques % (ex: 1.1→2.3%) = artefact mécanique. Le nombre absolu de requêtes validées étant <20, une variation relative du taux est attendue. RAS.
- **ALL Taux de requêtes DNS bloquées** : variation mécanique — quand le volume total de requêtes monte (ex: 509→704) alors que le nombre de requêtes bloquées reste constant, le taux baisse mécaniquement (ex: 14.1%→10.7%). RAS — le pourcentage n'est pas un indicateur d'efficacité instantanée, c'est un ratio qui suit le volume total.
- **ALL Requêtes DNSSEC non validées** : variation de quelques dizaines à centaines de requêtes (ex: 98→103). **Sauts massifs possibles** : peut sauter de +400+ (ex: 98→510) en même temps que `ALL Requêtes DNS` saute de la même amplitude — c'est l'artifact de ré-échantillonnage AdGuard, pas une explosion de trafic DNS non validé. Peut aussi chuter drastiquement (ex: 510→98) — rétractation de fenêtre. RAS.
- **ALL Requêtes validées par DNSSEC** (compteur absolu) : variation de ±3 requêtes (ex: 12→15). **Sauts possibles** : peut passer de 1→6 d'un coup pendant un ré-échantillonnage AdGuard. Distinct du pourcentage — c'est le compteur absolu jTower/AdGuard, fluctuation normale du trafic DNS. RAS.
- **ALL Taux de requêtes validées par DNSSEC** : variation de quelques % (ex: 1.1→2.3%, ou 5.7→5.4%) = artefact mécanique. Le nombre absolu de requêtes validées étant très faible (<20), une variation relative du taux est attendue. RAS.
- **ISS pass detection** : `ISS: changed from <valeur> to unavailable` = station spatiale hors zone de réception. RAS, revient automatiquement au prochain passage orbital.
- **ISS retour en zone** : `ISS: changed from unavailable to <valeur>` = la station spatiale est de nouveau en zone de réception ; la valeur (ex: 12) est le nombre d'astronautes à bord. RAS.
- **Film 2: changed from unknown to unavailable** : capteur de compteur de films (probablement lié à Radarr ou intégration cinématographique). Transition `unknown → unavailable` = sonde qui perd sa source de données, pas un vrai problème. RAS, pattern vague monitoring standard si en vague, ou micro-glitch isolé sinon.
- **Météo Next rain → unknown après échéance** : `Next rain: changed from 2026-07-13T13:25:00+00:00 to unknown` = l'heure de pluie prévue est dépassée, le capteur passe à `unknown` jusqu'à la prochaine prévision. RAS.
- **Météo-France forecast Le Havre Humidity** : voir section RAS immediat ci-dessus. Variation de ±5-10% normale.
- **F1 - Race Météo** : voir section RAS immediat ci-dessus. Variation de ±1-2°C normale, transitions `unknown°C → valeur` RAS.
- **Le Havre Température de l'Eau** : voir section RAS immediat ci-dessus. Variation de ±1-2°C normale.
- **Uptimes longs** : variation <0.001% sur 30j/365d
- **Uptime déjà à 0% → unavailable%** : pendant une vague, un monitor déjà à 0% d'uptime
  (service jamais up dans la fenêtre) peut passer à `unavailable%`. C'est le même
  pattern vague — aucune aggravation réelle. RAS.
- **CPU +/-5%**, **RAM +/-2%**, bandwidth
- **jtower CPU** : variation de ~3-5% (ex: 11.59→8.47%), normale pour un PC avec activités intermittentes. Pics de ~50% (ex: 42→53%) possibles pendant une tâche CPU-intensive (compilation, rendu, mise à jour système) — RAS si retour sous 20% dans les minutes suivantes. Des sauts brutaux de +20% en un tick (ex: 19→53%) sont possibles au démarrage d'une tâche lourde — RAS si retour progressif.
- **jtower RAM** : variation de ~4% (ex: 42→38%), normale — gestion mémoire/cache système. Peut sauter de +15-20% (ex: 54→73%) pendant une tâche mémoire-intensive ( navigateur, VM, Docker build) — RAS si retour sous 60% dans les minutes suivantes. Des sauts brutaux de +10-15% en un seul tick sont possibles (ex: 29→56%) au démarrage d'un processus gourmand — RAS si retour progressif dans les minutes suivantes.
- **jtower Disk** : variation de ~0.03-0.1% (ex: 81.24→81.27%), fluctuation normale de l'utilisation disque (caches, logs, métriques temporaires). RAS. Peut aussi baisser de ~1% d'un coup (ex: 81.2→80.11%) — libération d'espace (nettoyage de cache, rotation de logs, purge temporaire). RAS.
- **jtower Bandwidth** : variation de ~0.1-0.5 MB/s au repos, normale. **Pics de téléchargement** : peut monter brutalement à 15+ MB/s (ex: 0.17→15.4 MB/s, 0.31→16.55 MB/s) pendant un téléchargement ou transfert réseau massif — corréler avec `jtower Network Receive` (peut atteindre 14-16 MB/s). RAS si retour sous 1 MB/s dans les minutes suivantes. Des séquences de téléchargement peuvent durer 10+ min avec bandwidth soutenu à 14-17 MB/s — RAS tant que la conso électrique et CPU restent cohérentes.
- **jtower Network Receive/Send** : pics de 7-16 MB/s (Receive) et 0.1-0.25 MB/s (Send) pendant un téléchargement. Le ratio asymétrique (Receive >> Send) confirme un téléchargement (pas une upload). RAS si résorption spontanée. Receive peut atteindre 16+ MB/s (ex: 16314 kB/s) pendant des téléchargements massifs prolongés. Send peut aussi monter à ~240 kB/s pendant ces périodes (ack TCP, requêtes). RAS si résorption spontanée.
- **jtower Uptime** : incréments de +2 min par tick, normal. RAS.
- **Debian-trixie-latest-amd64-base** (template VM) : RAM ~33.3% stable, Bandwidth ~5.5-5.8 MB/s, Network RX ~2.4-2.5 MB/s — métriques stables de VM template Debian. RAS en toutes circonstances (pas de services réels hébergés).
- **jtower GeForce RTX 3060 Ti (GPU)** : variation de l'utilisation GPU de +/-0.5-1% au repos (ex: 0.93→0.47%), normal. Un pic >10% indique une tâche GPU (jeu, rendu, IA locale) — RAS, corréler avec la conso jTower (PC) pour confirmer. Retour <1% au tick suivant = burst terminé.
- **jtower Temperature** : variation de +/-1-3°C — normale, fluctuation thermique des composants (CPU/GPU au repos ou en charge légère). **+8 à +19°C d'un coup** (ex: 42→50°C, ou 42→61°C) — RAS si non récurrent ; peut indiquer un burst d'activité CPU/GPU (jeu, rendu, compilation). Un pic à 61°C suivi d'un retour à 44°C dans le même cycle a été observé (burst GPU/jeu typique) sans conséquence. Si la température reste élevée (>70°C) pendant >10 min, alors investiguer. **En dessous de 65°C, toujours RAS** — la barre d'alerte est à 70°C, pas 60°C.
- **jtower Network Receive** : variation de ~20-50 kB/s (ex: 399→381 kB/s), fluctuation normale du trafic réseau local. Distinct de `Pangolin Bandwidth` (trafic WAN).
- **telecomande 3 button LQI** : Link Quality Indicator d'un périphérique Zigbee (télécommande). Transition `unknown → 168` = premier rapport de qualité de liaison après réveil/pairing du device. LQI 168 est bon (échelle 0-255). RAS, capteur Zigbee qui se manifeste.
- **Sun Prochain coucher** : transition du coucher de soleil au jour suivant (ex: `2026-07-21T19:54:39+00:00 → 2026-07-22T19:53:29+00:00`) = calcul astronomique normal après le coucher du jour, RAS.
- **Uptime 365d baisse jusqu'à ~0.033%** sur services à faible disponibilité (ex: Paperless-ngx sous 50%) : les uptimes longs sont des rolling averages — une baisse de 0.01-0.05% est normale (période de downtime qui rentre dans la fenêtre de rolling average) et non un signe de dégradation.

→ Reponse : `RAS.`

### A surveiller
- Temps de reponse qui double (>2x baseline) mais <500ms
- CPU qui monte >10% d un coup
- Un seul service degrade alors que tout le reste est stable

→ Reponse : breve analyse + `Je surveille.`
### Pattern vague monitoring

Quand >=5 monitors passent simultanement en unavailable :
- Plusieurs certificats SSL → `unavailabled`
- Plusieurs uptimes Docker → `unavailable%`
- Plusieurs TCP/Ping/DNS → `unavailable` (y compris les sondes **DNS MX** et **DNS A**)
- Plusieurs metadonnees moniteur → `Type de moniteur: http → unavailable` (et aussi `ping → unavailable`, `docker → unavailable`),
  `Statut: up → unavailable` (et aussi `down → unavailable`: progression de vague où un service précédemment `down` devient injoignable par la sonde — à ne pas confondre avec `up → down` réel hors vague), `Tags: 0tags → unavailabletags`,
  `Nom d'hôte surveillé: <IP/domaine> → unavailable`,
  `URL surveillée: <url> → unavailable`
- Plusieurs moyennes temps de reponse → `Response time Ø (1d/30d/365d): Xms → unavailablems`
- Les moyennes **1d** peuvent aussi passer à `unavailablems` pendant une vague (observé
  DNS A panel.losgalactique.fr avg 1d : 3.49ms → unavailablems). Même mécanisme que
  les 30d/365d — la sonde n'a pas répondu dans la fenêtre récente, l'agrégat perd
  son échantillon. RAS.
- Uptime 1d → `unavailable%` (en plus des 30d/365d)

→ C est une **oscillation de la couche monitoring** (Beszel/Uptime Kuma)

## Diagnostic d une vague

### Signe confirmateur fort : Beszel lui-même est unavailable

Quand `docker: beszel Statut: changed from up to unavailable` apparaît dans le flux,
c'est le **signal le plus fort possible** que la vague est une panne de la couche de
monitoring, pas des services réels. Beszel ne peut pas monitorer les autres services
parce que lui-même est tombé — les `unavailabled`/`unavailable` en cascade sont
simplement la conséquence mécanique de son absence.

Ce signal est particulièrement utile au début d'une vague pour trancher rapidement
entre monitoring failure et vrai problème.

**Signal précoce — spike de la sonde Beszel elle-même** : avant que Beszel ne passe
`unavailable`, sa propre sonde de temps de réponse (`beszel.jefe.ovh`) peut montrer
un spike massif (>2000ms, ex: 38→2162ms). C'est un signal d'alerte précoce : le
composant de monitoring commence à saturer avant de tomber complètement. Si
beszel.jefe.ovh spike >1000ms et que peu après d'autres services flanchent, la vague
est confirmée.

### Résorption possible avec Beszel toujours unavailable

Il arrive que des certificats (Shop LG, etc.) reviennent de `unavailabled` vers `80d`
alors que `beszel` est toujours `unavailable`. C'est normal : certains métriques
peuvent être servies depuis le cache HA ou un réplica partiel, indépendamment du
Beszel central. Ne pas interpréter comme un retour complet à la normale — attendre
le retour de `beszel statut: unavailable → up` pour confirmer la fin de la vague.

### Signes confirmateurs
1. **Freebox** : temps de fonctionnement continue +30s regulierement
2. **jTower** : tension, courant, puissance, conso evoluent normalement
3. **F1 horloge** : suit normalement
4. **DNS** : temps de reponse <10ms
5. **Services HTTP** : repondent encore (pas de timeout)
6. **Ce sont les sondes qui flappent**, pas les services
7. **Resorption spontanee** en 3-10 min

min.

### Stragglers persistants en phase de recovery

Observation vague #33 (2026-07-13, fin session) : après résorption de ~85% des monitors,
un sous-ensemble de ~7 monitors reste en `unavailable` pendant 2-3 cycles supplémentaires
avant de revenir.

**Monitors stragglers typiques (pangolin) :**
- `pangolin: db.losgalactique.fr`, `pangolin: status.losgalactique.fr` — temps de réponse
- `pangolin: rss.jefe.ovh`, `pangolin: app.jefe.ovh` — uptimes 1d/30d
- `pangolin: shop.losgalactique.fr` — uptime 30d
- `pangolin: paperclip.jefe.al` — type moniteur + avg 365d
- `pangolin: argus.jefe.al` — avg 1d

**Caractéristiques distinctives :**
- Tous hébergés sur le même sous-ensemble de sondes Beszel (pas de pattern par service réel)
- Revenent spontanément en 2-3 min après le gros de la vague
Coïncident souvent avec les dernières sondes `unavailable → docker/port` (beszel-agent, AX42).

**Monitors dockers en queue de recovery** : les monitors docker (`unavailable → docker`) sont systématiquement les derniers à revenir en phase terminale. Après la résorption des certificats (80d), temps de réponse, et métadonnées pangolin, il reste 2-5 monitors docker qui mettent 1-3 min supplémentaires avant de repasser de `unavailable` à `docker`. Exemple observé : ntfy, paperless-broker-1, immich_redis — un par un, séparés de 10-30s. Conduite : ne pas attendre tous les dockers pour déclarer la vague terminée. Si certificats à 80d + temps réponse <200ms, vague résorbée.

**Conduite :** Ne pas traiter comme un problème distinct ni comme une nouvelle vague.
Attendre 2-3 min pour résorption complète. Si toujours unavailable après 5 min, alors
reconsidérer.

### Récidive immédiate : vague post-résorption partielle

Observation vague #42 : après que les certificats et certaines sondes étaient revenus de `unavailabled`/`unavailable` vers leurs valeurs normales, une **deuxième cascade intégrale** a repris dans les minutes suivantes. Beszel était brièvement revenu puis retombé.

**Caractéristiques distinctives :**
- Résorption partielle (certificats → 80d, ping → 0ms, temps de réponse → normal)
- Puis tous les certificats repassent unavailabled simultanément
- Les uptimes/sondes repartent en cascade unavailable
- Résorption finale dans la foulée (courte durée)

**Conduite** : ne pas interpréter la résorption partielle comme la fin définitive de la session de vagues. Si le Beszel a été vu brièvement en recovery (certificats à 80d) puis les certificats retombent, c'est la même vague qui récidive — pas une nouvelle. Attendre une résorption stable (pas de retour unavailabled dans les 5 min suivantes) avant de déclarer la vague terminée.

## Memo

Le capteur `jtower CPU` permet de classer les spikes de conso :

| Conso | CPU | Cause probable | Verdict |
|------|-----|----------------|---------|
| +20-40W | Hausse (>5%) | Tâche CPU (compilation, batch) | Normal, temporaire |
| +20-40W | Bas (<5%) | Tâche GPU (jeu, rendu) | Normal, temporaire |
| +20-40W | Hausse (>10%) + persistant >10 min | Process bloqué | Investiguer |
| +50W+ | Variable | Charge excessive | Investiguer |

Spike 141→177W + CPU 2.85→4.17% = tâche GPU typique. RAS si retour <140W dans les min.\n\nPendant les périodes calmes, jTower (PC) génère des micro-variations de conso\nqui sont normales. Mais des hausses >30W (ex: 141→177W) méritent une vérification\nrapide — corréler avec jTower CPU : si CPU monte de concert, c'est une tâche en\ncours (jeu, compilation, rendu). Si CPU reste bas (<5%) et conso reste élevée\n>10 min, investiguer.

### Focus pendant une vague monitoring

Meme en pleine vague, certains indicateurs restent normaux et le confirment :

- **DNS metrics (AdGuard/Pihole compteurs)** : `ALL Requêtes DNS`, `ALL Requêtes DNS-over-HTTPS`,
  `ALL Taux IPv6`, `ALL Requêtes bloquées`, **`ALL Taux de requêtes validées par DNSSEC`**
  continuent de s incrementer normalement pendant chaque vague. ALL Taux de requêtes validées par DNSSEC peut varier de quelques % (ex: 1.1%→2.3%) sans signification — le nombre absolu de requêtes validées étant très faible (<20), la variation relative du taux est mécanique. Si les compteurs DNS bougent,
- **DNS Beszel probes** (DNS A Uptime 30d, DNS A Response time Ø 365d, etc.) : ces métriques
  agrégées depuis Beszel sont des sondes comme les autres — elles peuvent passer à
  `unavailable%` / `unavailablems` pendant une vague, exactement comme les uptimes Docker
  ou les certificats. Ne PAS confondre avec les compteurs AdGuard qui restent stables.
- **Pangolin** : CPU (~15-20%, peut monter jusqu'à ~27% en vagues très intenses), RAM (~56-57%, peut descendre à ~37% et remonter à ~42%), Network (~30-70 kB/s), Disk (~71%)
  restent stables pendant les vagues normales. Pendant les vagues intenses
  (14+ vagues enchainées), CPU peut monter jusqu'à ~27% et Network RX
  jusqu'à ~416 kB/s. **Hors vague** : la RAM Pangolin peut fluctuer de ±3-5% (ex: 40.9→37.4%) — c'est la gestion mémoire normale du reverse proxy (caches de connexion, buffers TLS). CPU peut monter ponctuellement à ~33% (ex: 25→33%) lors d'un pic de requêtes proxy — RAS si retour sous 20% au tick suivant.
- **Pangolin Network Receive/Send** : pics de ~500-900 kB/s (ex: 575 kB/s Receive) possibles lors d'un burst de trafic proxy (multiple connexions TLS simultanées). RAS si retour sous 200 kB/s dans les minutes suivantes. Des baisses brutales de Network Receive sont aussi possibles (ex: 885→105 kB/s) — fin d'un burst proxy, RAS.
- **Pangolin Disk** : variation de ~0.01% par tick (ex: 37.93→37.94→37.95%), incrément normal. RAS.
- **Pangolin Uptime** : incréments de +2 min par tick, normal. RAS.
- **jNas** : CPU (~3.5%), RAM (~33%), Bandwidth (~1.3 MB/s) — stables généralement.
  Pendant vagues intenses, Network RX peut pic jusqu'à ~9 MB/s et Network Send
  jusqu'à ~4 MB/s.
- **jTower** : increment conso +0.001kWh par tick, tension/courant normaux
- **Freebox** : +30s regulierement, horloge F1 +1min — inchange

### Phase de recovery

Apres la resorption d une vague, les monitors reviennent progressivement, pas d un coup. Cela produit un deuxieme flux d evenements (`unavailablems -> unknownms -> 80d`, etc.) qui peut ressembler a une nouvelle vague.

**Regle** : si TOUS les evenements sont des transitions `unavailable -> valeur_reelle`, c est la recovery — pas une nouvelle alerte.

- **Ordre de recovery** : les metadonnees (tags `unavailabletags→0tags`, type moniteur `unavailable→docker/http/ping`, statut `unavailable→up`, URL surveillee, nom d'hôte surveillé) reviennent en premier, puis les certificats (`unavailabled→80d` ou `unknownd→72d` — `unknownd` est un état intermédiaire distinct d'`unavailabled`, similaire à `unknownms` pour les temps de réponse ; même RAS), puis les temps de reponse (parfois via `unknownms` intermediaire), puis les uptimes, et enfin les agregats (response time moyen 1d/30d/365d). Voir `references/monitoring-oscillation-pattern.md` section "Phase de recovery (post-vague)" pour la sequence complete avec delais par etape.
- **Batch massif `unknownd → Nd` de certificats** : 30+ certificats pangolin peuvent transiter simultanément de `unknownd` vers leurs valeurs d'expiration réelles (variant de 25d à 72d selon le certificat). Les jours d'expiration varient car les certificats ont été renouvelés à des dates différentes — c'est normal, pas un signe de problème. Ce batch massif est un signal fort de recovery de la couche monitoring : les vérificateurs SSL de Beszel viennent de se resynchroniser et publient leurs résultats en rafale. RAS. Observé 2026-07-21 : 30+ certificats `unknownd → Nd` (25d, 36d, 39d, 45d, 46d, 47d, 49d, 66d, 69d, 72d) en une seule rafale.

#### Recovery spikes (pics tardifs en phase de retour)

Il arrive qu'un temps de réponse spike (>500ms) apparaisse bien après que la plupart des monitors soient déjà revenus (certificats restaurés, statuts à `up`, tags normaux). Exemple observé : Los Galactique Panel 706ms alors que tous les autres indicateurs étaient déjà au vert.

**Cause probable** : la dernière sonde/replica Beszel à se resynchroniser — le service est opérationnel mais sa métrique de temps de réponse est encore instable.

Amplitude possible : ces spikes tardifs ne sont pas limités à des valeurs modérées. Observé Los Galactique Panel jusqu'à 2667ms (vague #31) puis 2398ms (vague #34) en recovery — la latence peut atteindre plusieurs secondes sans que le service soit réellement dégradé.

**n8n précurseur** : un spike isolé de n8n (43→439ms) peut être le premier signe d'une
nouvelle vague, apparaissant 1-2 minutes avant les autres services. Vérifier si d'autres
sondes suivent dans les 2 min avant de qualifier l'événement de vague.

**Conduite** : RAS si ce pic isolé survient en contexte de recovery tardive (moniteurs majoritairement revenus). Ne pas le traiter comme une nouvelle vague ni comme un vrai problème — vérifier que 60s après le pic la valeur est revenue sous 200ms.

#### Aftershocks (micro-vagues post-session)

Après la dernière vague complète d'une session (ex: vague #33), 1-3 micro-événements isolés peuvent apparaître sur 15-30 min sans jamais atteindre l'amplitude d'une vague complète.

**Pattern typique :**
1. Un service spike isolé (n8n 43→439ms, pas de cascade)
2. Minutes plus tard, éclair sur un autre service (Los Galactique Panel 57→590ms, résorbé dans le même lot HA)
3. Puis 1-3 spikes simultanés sur ntfy/Immich/Los Galactique Panel, vite résorbés

**Caractéristiques distinctives :**
- Maximum 1-3 services impactés vs 20+ dans une vague complète
- Résorption <2 min (jamais >5)
- Aucun artefact résiduel (pas de unavailable, pas d'uptime érodé)
- Peuvent inclure des « éclairs » (spike+recovery dans le même lot HA)
- Ne sont PAS comptés comme des vagues supplémentaires

**Conduite :** RAS. Noter brièvement le spike et sa résorption. Ne pas les qualifier de vague — ce sont des aftershocks de la dernière vague complète.

Voir `references/monitoring-oscillation-pattern.md` section « Aftershocks post-vague #33 » pour la chronologie détaillée.

#### Spikes résiduels tardifs (5-15 min après fin de vague)

Un pattern distinct observé après les vagues tardives (30+) : des spikes >1000ms
peuvent apparaître **5 à 15 minutes après** que la vague semble entièrement résorbée
(certificats restaurés, uptimes normaux, temps de réponse moyens stables).

**Exemples observés (vague #31, 2026-07-13)** :
- Seerr : 115→1571ms puis retour à 102ms (~12 min après fin vague)
- Pocket-ID Tailscale : 35→2126ms (pic isolé tardif)
- ntfy : 38→501ms puis retour à 37ms

**Caractéristiques distinctives** :  
- Surviennent alors que TOUS les autres indicateurs sont au vert (certs 80d,
  uptimes normaux, temps de réponse des autres services <200ms)
- Toujours isolés — 1 à 3 services max, jamais la cascade complète
- Résorption spontanée en 1-5 min
- Amplitude potentielle élevée (>2000ms pour Pocket-ID)
- Services les plus fréquemment ciblés : Seerr, Pocket-ID, ntfy (spikes >1000ms).
**FreshRSS** peut aussi avoir des spikes résiduels tardifs mais à amplitude modérée
(~200-250ms vs >1000ms pour les autres). Ne pas exclure FreshRSS — un spike à 247ms
alors que sa baseline est ~100ms est une hausse significative (~×2.5) qui suit le
même mécanisme que les gros spikes des autres services.
  **n8n peut aussi avoir des spikes isolés tardifs** mais à plus faible amplitude
  (~400-500ms vs >1000ms pour les autres). Ne pas exclure un spike tardif sous
  prétexte qu'il cible n8n plutôt que les services habituels.
  **Pendant les vagues principales** (hors recovery), n8n n'est pas épargné par les
  gros spikes >1000ms — observé à 2712ms en vague #38. C'est la nouvelle amplitude
  maximale documentée pour n8n.

**Mécanisme probable** : dernier cycle de resynchronisation d'un réplica Beszel
encore en retard — le service est totalement opérationnel, sa sonde est encore
instable.

**Conduite** : RAS. Ne pas traiter comme une nouvelle vague. Ne pas investiguer.
Si le même service ne revient pas à <200ms après 5 min, alors seulement reconsidérer.

#### Distinction Statut: `down` vs `unavailable` en recovery

En recovery de vague, la plupart des monitors passent de `unavailable` à `up`. Mais parfois un service passe de `unavailable` à `down` :

- **`unavailable`** = la sonde de monitoring n'a pas pu joindre le service (timeout ou refus de connexion) — c'est le pattern vague monitoring standard.
- **`down`** = la sonde a pu joindre le service mais a reçu une réponse négative (HTTP 5xx, TCP RST, etc.) — signal qualitativement différent.

**Dans le contexte d'une vague monitoring** : si un service passe `unavailable → down` pendant la phase de recovery, cela signifie que le monitoring a repris mais que le service traverse un micro-down réel (ex: redémarrage, cache à reconstruire). Dans 100% des cas observés, le service revient à `up` dans les 2 minutes suivantes — ne pas alarmer, mais noter le passage par `down` comme un micro-événement distinct du pattern vague.

**Hors contexte de vague** : un passage `up → down` non accompagné d'un unavailable monitoring est un vrai problème à investiguer.

### Piege
- Si TOUS les monitors certif/uptime/docker flappent ensemble → couche monitoring
- Si UN SEUL service a un pic isole >1000ms → vrai probleme
- **MAIS** : si ce pic isole survient PENDANT une vague monitoring (services HTTP
  comme Shop LG, Los Galactique Panel qui grimpent >1000ms), il fait partie de la vague
  et se resorbe avec elle — ne pas le traiter comme un vrai probleme isole.
  Les vrais signes d un probleme isole sont : service toujours degrade APRES la fin de
  la vague, ou spike alors que tout le monitoring est stable.
- Si des capteurs specifiques (trophees PSN, jeux, comptes externes) passent en unavailable
  alors que tout le monitoring tourne normalement :
  - **Si PS Plus était déjà `cleared`** (pas de changement récent de statut abonnement) et que
    tous les trophées/level/last online passent en unavailable simultanément → probable
    **API PSN glitch temporaire** (perte de connexion à l'API Sony), pas une résiliation
    d'abonnement. Le retour est spontané. RAS.
  - **Si PS Plus change de `active` à `cleared` au même moment** que les trophées → résiliation
    d'abonnement confirmée. À mentionner à l'utilisateur.
  - Les capteurs rests disponibles affichent 0/vide (Next level 0%, Platinum 0) plutot que
    le pattern d oscillation monitoring.

### Signaux de confirmation supplementaires pendant une vague

- **HA API 403** : si les sondes de temps de réponse et certificats retournent `403 Forbidden` via l'API HA directe (ha_get_state), c'est un **signal supplémentaire** de panne monitoring. Ces entités sont des proxys REST vers Beszel/Uptime Kuma — quand leur source est indisponible, l'API HA ne peut pas les résoudre et refuse l'accès. Ce n'est pas un problème de token.

  **Utilisation comme outil de diagnostic batch** : pour confirmer rapidement une vague
  monitoring, tenter `ha_get_state()` sur 2-3 sondes de services différents (certificat,
  temps de réponse, uptime). Si **toutes retournent 403**, c'est un signal fort que la
  couche Beszel entière est indisponible — la vague est confirmée, ne pas investiguer plus.
  Ne pas retenter après confirmation, attendre la résorption spontanée.
- **Les compteurs AdGuard DNS (y compris ALL Taux de requêtes validées par DNSSEC)** (`ALL Requêtes DNS`, `ALL Requêtes DNS-over-HTTPS`,
  `ALL Taux IPv6`, `ALL Requêtes bloquées`, `ALL Requêtes DNSSEC non validées`) continuent de s incrementer normalement pendant chaque vague. ALL Taux de requêtes validées par DNSSEC peut varier de quelques % (ex: 1.1%→2.3%) sans signification — le nombre absolu de requêtes validées étant très faible (<20), la variation relative du taux est mécanique. Si les compteurs DNS bougent,
  l infrastructure DNS est saine — seules les sondes flappent.
- **Les sondes DNS Beszel** (DNS A Uptime 30d, DNS A Response time Ø 365d, etc.) sont
  des monitors comme les autres — elles peuvent passer à `unavailable%`/`unavailablems`
  pendant une vague. Ne pas les confondre avec les compteurs AdGuard (stables).
- **Shop LG** est un indicateur precoce fiable : c est souvent le premier service a
  grimper (>200ms) et un bon indicateur de fin de vague. L'ordre de résorption peut
  varier — dans la vague #46, Shop LG a été résorbé (2370→138ms) avant FreshRSS et
  Immich, contrairement au pattern « dernier à résorber » observé dans les vagues
  plus précoces. Conduite inchangée : quand Shop LG pic puis se résorbe, la vague
  est en cours de terminaison (mais d'autres services peuvent encore être en spike).
- **Pocket-ID Tailscale** est un second indicateur precoce. Observé à plusieurs reprises
  comme le premier service à pic (>1000ms, ex: 36→1307ms) en prélude d'une vague
  majeure. Quand Pocket-ID spike suivi de nombreux certs/uptimes `unavailabled`, la vague
  est confirmée.

#### Beszel up pendant que des probes sont encore unavailable (recovery avancée)

Observation vague #52 (2026-07-13) : un nouveau sous-pattern en phase de recovery tardive où
**Beszel lui-même est déjà revenu `up` alors que plusieurs de ses probes génèrent encore
des événements `unavailable`/`unavailabled`.**

**Séquence observée :**
1. beszel.jefe.ovh Statut: unavailable → **up** (Beszel lui-même rétabli)
2. Simultanément : n8n, ntfy, headscale, immich_postgres uptimes → `unavailable%`
3. Simultanément : Seerr, Shop LG certificats → `unavailabled`
4. Simultanément : losgalactique.fr DNS, newt, paperless-broker temps → `unavailablems`
5. Ces probes se résorbent spontanément dans les 1-2 min suivantes

**Caractéristiques distinctives :**
- Beszel est `up` mais ses *children probes* continuent de flapper — contrairement
  au pattern « Résorption possible avec Beszel toujours unavailable » où ce sont
  des caches/réplicas indépendants qui servent les certificats.
- Ici, c'est Beszel lui-même qui vient de redémarrer mais ses sous-sondes n'ont
  pas encore fini leur cycle de vérification initial. Les `unavailable` sont des
  artefacts de démarrage à froid (probes pas encore échantillonnées).
- Les certificats (Shop LG, Seerr) peuvent encore passer `unavailabled` pendant
  cette fenêtre — le serveur Beszel est up mais ses workers SSL n'ont pas encore
  ré-exécuté les vérifications de certificat.
- Résorption spontanée en 1-2 min sans intervention.

**Conduite :** ne pas interpréter les nouveaux unavailable comme une vague distincte
(#53) quand Beszel est déjà `up`. C'est la **queue terminale** de la vague en cours.
Marquer la vague comme « en résorption terminale » et attendre 1-2 min.
Si après 5 min des probes sont toujours unavailable alors que Beszel est up,
reconsidérer.

#### Variante `unknownms → unavailablems` en vague

Observation : certains monitors (typiquement paperless-gotenberg-1, anonaddy_redis)
peuvent passer par un état intermédiaire `unknownms` avant `unavailablems`.

#### Variante `0.0ms → unavailablems` en vague

Observation : certains monitors (typiquement `immich_machine_learning` sur 365d) peuvent
passer directement de `0.0ms` (métrique agrégée sans aucun échantillon, jamais mesurée)
à `unavailablems` pendant une vague.

- `Temps de réponse Ø (365 jours): changed from 0.0ms to unavailablems`
- Cela signifie que la métrique rolling n'avait **jamais** eu d'échantillon valide avant la vague.
- Distinct de `unknownms → unavailablems` (où l'état inconnu est explicite) et de
  `Xms → unavailablems` (perte d'une valeur existante).
- Conduite : même RAS que les autres variantes — artefact de vague monitoring.

- `Temps de réponse: changed from unknownms to unavailablems`
- Cela signifie que la sonde n'avait **jamais** rapporté de valeur (first-seen ou
  reset de métrique) avant l'indisponibilité.
- Ne pas confondre avec le pattern `Xms → unavailablems` (perte soudaine d'une
  valeur connue) ou le pattern intermédiaire `unavailablems → unknownms → Xms`
  (retour progressif en recovery).
- Conduite : même RAS que le pattern standard — c'est un artefact de la vague
  monitoring, pas du service réel.

#### Timing variable : spikes précurseurs vs cascade simultanée

Les vagues monitoring n'ont pas toujours le même ordre d'arrivée des événements. Deux patterns de timing observés :

**Pattern A — Cascade synchrone** (vagues 1-32, majoritaire) :
Les spikes de temps de réponse et les passages `unavailabled` arrivent dans la même rafale. Exemple : Shop LG 143→1457ms + 8 certificats → unavailabled simultanément.

**Pattern B — Spikes précurseurs** (observé vague #33, 2026-07-13) :
Les spikes de temps de réponse sur 2-3 services arrivent 1-2 minutes AVANT que les certificats/uptimes ne passent `unavailabled`. Puis les spikes se résorbent alors que la cascade de unavailable est encore active. Ordre :
1. Spikes temps réponse (LibreTranslate 40→2432ms, Obsidian 37→818ms, Shop LG 160→212ms)
2. Cascade certificats → `unavailabled` (Los Galactique, Shop LG, Seerr, ntfy, Headscale, FreshRSS, LibreTranslate, Maps iOS, Pocket-ID) + uptimes Docker → `unavailable%` + sondes → `unavailable`
3. Résorption des spikes pendant que la cascade est toujours active (LibreTranslate 2432→55ms, Obsidian 818→52ms)
4. Résorption des certificats/uptimes/sondes ensuite

**Conduite** : même diagnostic dans les deux cas — couche monitoring qui oscille. Le pattern B ne doit pas être confondu avec une vraie panne qui s'étend. La confirmation reste : jTower/Freebox/DNS normaux pendant toute la séquence.

### Suivi actif des spikes persistants entre les réponses

Quand un spike >1000ms persiste sur un service et que les événements continuent d'arriver
sans résorption, mentionner brièvement l'état d'attente en fin de réponse :
`Toujours en attente du retour à la normale de **<service>**.`

Si le spike dure anormalement longtemps (>3 cycles de rafale sans résorption),
vérifier proactivement via `ha_get_state()` sur l'entité du service — même si
le token HA retourne souvent 403. Les résultats possibles :

- **403 Forbidden** → la sonde Beszel est totalement indisponible, confirme une vague monitoring active. Ne pas retenter.
- **Statut `up`** + temps normal → le spike était déjà résorbé entre les ticks, RAS.
- **Statut `up` + temps encore élevé** → spike persistant authentique, attendre le prochain événement.

**Format réponse quand des spikes non résorbés sont suivis** :

```
**Service** : old → new, comment ✅

Encore en attente du retour à la normale de **<service>**.
```

Ne pas bloquer la réponse sur les spikes non résorbés — accuser réception des
événements normaux entre-temps.

### Stragglers persistants au-delà d'une session

Observation vague #41 (2026-07-13, fin de session) : sur les spikes tardifs d'une vague,
certains services peuvent ne PAS se résorber avant la fin de la session — les événements
cessent d'arriver (session fermée, agent redirigé, ou intervalle de reporting plus long)
alors que le temps de réponse est toujours élevé.

**Exemple observé (fin session #2, vague #41, 2026-07-13)** : ntfy (1430ms) et
invite.jefe.ovh (1656ms) toujours en spike à la fermeture de session, sans événement
de résorption.

**Confirmé résorbé (début session #3 même jour)** : les événements entrants
montrent que ntfy et invite.jefe.ovh sont revenus à la normale dans la session suivante
sans qu'aucun événement intermédiaire ne le signale — le spike s'est résorbé spontanément
hors-session. Conforme au pattern.

**Autres services observés comme stragglers tardifs** : ntfy, invite.jefe.ovh,
Pocket-ID Tailscale, Obsidian LiveSync — peuvent persister en spike >1000ms après que
le gros de la vague est résorbé.

**Conduite** : à la reprise de session, vérifier si ces services sont revenus à la normale
(attendu, confirmé expérimentalement) ou si le spike a persisté (improbable mais à
documenter). Ne pas traiter comme un incident persistant — le pattern vague assure une
résorption spontanée même si elle survit hors-session.

### Cascade en dent de scie prolongée (tail étendu)

Observation vague #49 (2026-07-13) : contrairement aux vagues 1-48 où la cascade
certificats était une rafale simultanée (<30s pour 5+ certificats), la vague #49
a montré un **étalement temporel prononcé** en phase d'ouverture :

1. Los Galactique Panel certificat → unavailabled
2. ~1 min plus tard : Shop LG certificat → unavailabled
3. ~1 min plus tard : n8n → unavailabled
4. ~1 min plus tard : ntfy → unavailabled
5. ~1 min plus tard : Headscale → unavailabled
6. ~1 min plus tard : Immich → unavailabled
7. ~1 min plus tard : LibreTranslate → unavailabled

Puis après résorption partielle, **les mêmes certificats sont retombés**
un par un dans le même ordre approximatif, étalés sur ~10 min supplémentaires,
donnant l'impression d'une vague « qui n'en finit pas ».

**Caractéristiques distinctives du tail étendu :**
- Certificats qui tombent un par un (pas simultanément), espacés de ~30-60s
- Après résorption, certains certificats retombent immédiatement (faux semblant
  de récidive)
- Cette phase de queue peut durer 10-15 min, contre 3-5 min pour la vague principale
- Les certificats sont toujours les derniers à se stabiliser — les temps de réponse
  et uptimes reviennent plus tôt
- Les sondes DNS (Response time Ø, Uptime) et métadonnées pangolin (Type de moniteur,
  Statut, URL) peuvent passer `unavailable` en différé, jusqu'à 5 min après les
  premiers certificats

**Mécanisme probable :** instabilité d'un réplica Beszel secondaire qui cycle
(connecte-déconnecte) avant de se stabiliser définitivement. La vague principale
(défaillance du Beszel primaire) est résorbée, mais le réplica secondaire met
plusieurs cycles à retrouver un état stable.

**Conduite :** ne pas traiter les retombées de certificats comme une nouvelle vague
(#50). Continuer de noter les événements comme queue de vague #49.
Si la queue dure >15 min sans stabilisation, alors reconsidérer.

### Conduite en cas de vagues repetees
- Les vagues peuvent se succeder rapidement (3-5 min d intervalle, parfois 1-2 min)
- On peut observer 14+ vagues consecutives sur 80+ min sans que ce soit une escalade
- Les vagues peuvent s enchaner quasi immediatement : recovery d une vague a peine terminee que la suivante commence (observe apres la 13e vague)
- Le catalogue de vagues peut atteindre 70+ en une seule journée (observé jusqu'à la vague #69 confirmée, likely #70+). Le plafond réel n'est pas connu — chaque session peut produire de nouvelles vagues, avec des sessions ayant confirmé jusqu'à 70+ vagues. Même en post-session, les vagues peuvent continuer de manière autonome.
- **Sélectivité accrue des vagues tardives** : à partir de ~25 vagues, les spikes deviennent sélectifs — seuls quelques services (typiquement Seerr, Immich, Los Galactique Panel, ntfy, Pocket-ID) montent au-dessus de 1000ms, tandis que d'autres (n8n, Obsidian, LibreTranslate, FreshRSS, Headscale, DNS) restent proches de leur baseline avec des micro-pics <100ms. Ne pas interpréter comme si le problème s'était réduit à quelques services — c'est simplement un effet de l'usure des sondes et non une amélioration réelle de l'infrastructure.
- **Vagues ultra-courtes (20+)** : les vagues tardives peuvent devenir si rapides que les evenements de spike et de recovery arrivent dans le meme lot HA. Exemple vague 21 : Los Galactique Panel `82→824ms` ET `824→55ms` dans la meme rafale. Meme conduite — pointer les stables (Freebox, jTower, DNS) et confirmer la resorption.
- **Résorption terminale (vagues 24+)** : sur les vagues très tardives (24+ après plusieurs heures), la recovery peut devenir quasi-simultanée — tous les certificats et métriques restants reviennent en <1 min au lieu de l'étalement progressif des premières vagues. Observé vagues 23 et 24 : ~12 certificats `unavailabled→80d` en 30s. À ne pas confondre avec une nouvelle vague.
- **Atténuation des vagues très tardives (34+)** : au-delà de ~33 vagues dans une session, les vagues peuvent entrer dans un régime d'atténuation où la cascade complète (certificats → unavailabled, uptimes → unavailable%, sondes → unavailable) ne se produit plus. Les vagues deviennent purement des spikes de temps de réponse sur 2-5 services, résorbés en <2 min, sans artefact résiduel (pas de unavailable, pas d'uptime impacté). Ne pas interpréter comme une amélioration réelle — c'est probablement un artefact des agents de monitoring en fin de cycle. Conduite inchangée : RAS, résorption spontanée.

> **⚠️ Attention — ce comportement n'est PAS déterministe.** L'atténuation a été observée sur la vague #34. Mais des vagues ultérieures (#36, le 2026-07-13 en session continue) ont produit la cascade COMPLÈTE (certificats unavailabled, monitors unavailable, métadonnées flappées) avec tous les artefacts d'une vague précoce. L'atténuation n'est pas une règle générale — chaque vague post-34 peut être soit atténuée (spikes seuls) soit complète (cascade intégrale). Ne pas retarder le diagnostic par excès d'optimisme ; vérifier chaque vague sur ses propres signes.

**Exemple vague #34 (atténuée, 2026-07-13 post-#33)** : aucun unavailable ni
unavailabled ; purement des spikes temps de réponse sur n8n (43→439ms), Los Galactique
Panel (53→590→2398ms), Shop LG (140→1348ms), ntfy (34→2938ms), Immich (55→743ms),
FreshRSS (105→247ms). Résorption complète en ~5 min. Aucune perte d'uptime visible.

**Exemple vague #36 (complète, session continue le 2026-07-13)** : tous les certificats en cascade unavailabled (Los Galactique Panel, Seerr, n8n, ntfy, FreshRSS, Immich, Shop LG), uptimes Docker unavailable%, sondes pangolin unavailable (SearXNG, argus, ha-mcp, node, ph, anisette, paperless, webdav, translate.jefe.ovh, etc.), CPU Pangolin 15→20%. Résorption complète en ~5 min avec recovery via `down` pour certaines sondes. Confirme que le pattern complet peut réapparaître même à 36 vagues.\n- Au-dela de la 3e vague, la reponse peut etre simplement `RAS.` sans mentionner la vague
- Apres resorption, les valeurs reviennent exactement a celles d avant\n- **Epuisement possible du cycle** : apres ~34 vagues en 5h, le pattern de vagues peut\n  s'arreter completement sans vague #35. Un silence de 30+ min sans aucun evenement\n  anormal est le signe d'une fin de cycle — les agents de monitoring se sont\n  stabilises. Voir `references/monitoring-oscillation-pattern.md` section\n  « Fin de cycle : silence monitoring post-vague #34 ».\n- **Pangolin CPU drop rapide** : %CPU peut chuter de >6% en un seul tick (ex:\n  21.89→15.07%) sans cause identifiable — c'est une fluctuation normale, RAS.\n- **jTower conso mois double-tick** : la conso mois peut parfois s'incrémenter\n  deux fois en rafale (ex: 39.967→39.968 puis 39.969→39.97 dans la minute).\n  C'est un artefact de l'échantillonnage, RAS.
- **Uptime impact** : une vague peut faire perdre ~0.002% d uptime 30j aux services
  impactes (ex: FreshRSS passe de 79.82% a 79.82%) — negligeable mais visible.
  **Asymetrie** : certains services (comme jflix) peuvent perdre jusqu'à ~0.004%
  par vague (le double). Ne pas s'alarmer — sans impact fonctionnel.
  **Érosion extrême** : les services rarement vérifiés (ex: FiveM LosGalactiqueRp)
  peuvent revenir à seulement ~20% après 19 vagues, car les « unavailable »
  dominent l'échantillon 30j. L'uptime réel hors vagues est normal — la valeur
  remontera avec le temps. Voir `references/monitoring-oscillation-pattern.md`.
- **Recovery via "down"** : un monitor peut revenir de `unavailable` a `down` au lieu
  de `unavailable` → `up`. La couche monitoring est fonctionnelle, le service est
  verifie comme hors-ligne. C'est un diagnostic plus precis, pas une escalation.
- **Divergence uptime 1d vs 30d/365d** : apres une vague, l'uptime 1d peut baisser
  de ~0.07% alors que l'uptime 30d bouge a peine (~0.002%). Les deux echelles
  racontent la meme histoire a des fenetres differentes. Voir
  `references/uptime-divergence-during-recovery.md`.

### Spikes isolés hors vague monitoring

Même en période calme (pas de vague active), 1-2 services peuvent
montrer des spikes de temps de réponse >500ms sans aucun autre indicateur
de vague (pas de `unavailabled`, pas de cascade de certificats, pas de
pertes d'uptime).

**Exemples observés (vague #32 résorbée, période calme, 2026-07-13)** :
- Shop LG : 143→1457ms (spike isolé, résorbé en ~5 min vers 124ms)
- n8n : 45→525ms (spike isolé, résorbé en ~2 min vers 44ms)
- Los Galactique Panel : 61→2421ms (spike ×40, résorbé en ~1 min vers 46ms)
- Seerr : 105→1337ms (spike isolé, résorbé en ~3 min)

**Caractéristiques distinctives** :
- Aucun autre monitor ne flappe (pas de unavailable, pas de cascade)
- Les compteurs DNS, Freebox+30s, jTower conso/tension restent normaux
- Résorption spontanée en 1-5 min
- Toujours 1-2 services max
- Amplitude potentiellement >1000ms

**Mécanisme probable** : micro-interruption d'un réplica Beszel isolé,
sans lien avec une vague généralisée.

#### Vérification rapide par ha_get_state

Quand un spike de temps de réponse est détecté (>500ms), utiliser `ha_get_state()` sur l'entité du service pour vérifier l'état actuel (statut `up`/`down`) et consulter la moyenne de temps de réponse sur les fenêtres disponibles (1j/30d/365d). Cela permet de distinguer :

- **Spike isolé déjà résorbé** : le statut est `up`, la moyenne basse — le temps réel est déjà revenu, l'événement est un artefact historique.
- **Spike en cours** : le temps réel est toujours élevé — confirmer la résorption au prochain événement.
- **403 Forbidden** : la sonde Beszel est totalement indisponible — confirme une vague monitoring active. Ne pas retenter, attendre la résorption spontanée.

**Limitation** : le token HA peut retourner 403 pour les entités de temps de réponse instantané. Les moyennes rolling (1j/30d/365d) et le statut sont généralement accessibles via `ha_search`/`ha_get_state` en alternative.

#### Conduite après vérification

- Si ha_get_state confirme `up` + temps normal → RAS, spike déjà résorbé.
- Si ha_get_state confirme 403 → vague monitoring active, ne pas investiguer plus.
- Si ha_get_state confirme spike persistant ET aucun autre service impacté → vrai problème potentiel, re-vérifier 60s plus tard.

#### Début de vague ambigu : quand 2 services spike sans cascade complète

Observation vague #47 (2026-07-13) : Seerr 105→1050ms (×10) suivi de FreshRSS 89→367ms (×4),
mais sans qu'aucun autre service ne suive et sans cascade de certificats/uptimes.
La session s'est terminée avant la résorption ou la confirmation d'une vague complète.

**Caractéristiques distinctives :**
- Exactement 2 services impactés (pas 1 isolé, pas la cascade complète)
- Spikes modérés à forts (×10 sur Seerr, ×4 sur FreshRSS)
- Aucun unavailable / unavailabled / cascade de certificats
- Possibilité d'être soit un double-spike isolé, soit le début d'une vague qui n'a pas eu le temps de se dérouler

**Conduite :** Si ≥2 services spike >500ms simultanément sans cascade complète confirmée,
mentionner « possible début de vague non confirmé » et noter le contexte (délai depuis
dernière vague, tendance générale). Ne pas déclarer une vague tant que la cascade
certificats/uptimes n'a pas été observée ou que la résorption n'est pas confirmée.

#### Éclair isolé (variante du spike isolé)

Observation complémentaire : un spike peut se résorber dans le **même lot d'événements HA**
(sans tick intermédiaire), en dehors de tout contexte de vague.

**Exemple observé (2026-07-13, post-vague #33)** : Los Galactique Panel 57→590→57ms,
retour à la baseline dans la même rafale qu'il est arrivé.

**Caractéristiques distinctives** :
- Amplitude du spike visible (>500ms) mais résorption instantanée
- Strictement 1 service impacté, aucun autre monitor ne flappe
- Aucun artefact résiduel (pas de unavailable, pas de cascade)
- Impossibilité technique d'un vrai problème (aucune fenêtre de downtime)

**Mécanisme probable** : faux positif d'un réplica Beszel qui a envoyé une
métrique erronée corrigée au cycle suivant — le service n'a jamais été dégradé.

**Conduite** : RAS immédiat, ne pas surveiller. Même résorbé, ne pas le citer
comme un événement dans la réponse — le signal était trop bref pour mériter
attention.

#### Double-spike simultané (variante du spike isolé)

Observation complémentaire : 2 services (pas 1 seul, pas la cascade complète)
peuvent montrer un spike >1000ms simultanément, puis résorber ensemble.

**Exemple observé (2026-07-13, vague #32 résorbée)** :
- ntfy : 41→2204ms ET FreshRSS : 129→1031ms, même rafale
- Résorption simultanée (ntfy 2204→44ms, FreshRSS 1031→100ms)

**Caractéristiques distinctives du double-spike** :
- Exactement 2 services impactés, pas plus
- Aucun autre indicateur de vague (pas de unavailable, pas de cascade de certificats)
- Les deux arrivent dans la même rafale d'événements
- Résorption simultanée dans la rafale suivante

**Mécanisme probable** : micro-interruption d'un réplica Beszel unique
qui héberge ces deux monitors précis — distinct d'une vague généralisée.

**Conduite** : même que le spike isolé — RAS, résorption spontanée attendue.

### Freebox port mapping IPv4

`Freebox v8 (r1) Nombre d entrées de mappage de port (IPv4): changed from 3 to 2`

Le compteur de mappage de ports IPv4 peut changer si un service libère son mapping (arrêt de conteneur, redémarrage, etc.). RAS tant que c'est isolé. Si le compteur change de manière répétée et rapide, demander à l'utilisateur s'il a modifié sa configuration récemment.

### Inforoute 76 (trafic routier)
**et radarr (event.radarr)**

`radarr (event.radarr): changed from '2026-07-13T17:43:05.315+00:00' to '2026-07-13T17:49:05.375+00:00'`

Timestamp de dernière vérification Radarr. Intervalle de ~6 min entre mises à jour, normal. RAS.

### Inforoute 76 (trafic routier)

`Inforoute 76 (event.inforoute_76): changed from '2026-07-13T12:09:44.807+00:00' to '2026-07-13T13:09:45.753+00:00'`

Timestamp de dernière mise à jour des données trafic Inforoute 76 (Normandie). Mise à jour horaire normale. RAS.

## Contextes specifiques

### Utilisateur en voiture (CarPlay)
Quand `iPhone du Zef Audio Output → CarPlay` :
- Le telephone change de reseau (BSSID) en se connectant a la voiture
- Les localisations geocoded peuvent etre imprecises pendant le trajet
- Les `Last Update Trigger → Significant Location Change` sont normaux
- L utilisateur ne repondra probablement pas — garder les reponses minimales
- Ne pas poser de questions en attendant une reponse

## Patterns complementaires

### Agrégats longs : variations infimes (RAS directement)

Les valeurs agrégées sur de longues périodes (1d/30d/365d) arrivent avec une haute
précision algorithmique. Pour ces métriques, **tout changement total < 1ms** ou
**< 0.001% d'uptime** est du bruit de rolling average, pas une tendance.

Quand le changement est dans la 5e décimale ou au-delà :
- `Headscale Uptime (365 days): 74.4227859609605% -> 74.4229594952168%`
- `DNS A panel Response time O (30 days): 3.59484441517511ms -> 3.59483042476128ms`

C'est du **bruit statistique** sur des moyennes périodiques, pas une tendance.
Toujours RAS sans analyse supplémentaire.

Même les micro-variations plus visibles (>1ère décimale mais <1ms d'écart)
sur des moyennes 1d/30d/365d sont RAS :
- `beszel.jefe.ovh Response time O (30 days): 253.26ms -> 253.09ms`  (0.17ms)
- `HA Pi Response time O (1 day): 42.842ms -> 42.843ms`  (0.001ms)
- `jNas Response time O (365 days): 43.161ms -> 43.161ms`  (0.00001ms)
- `jflix.jefe.al Response time O (30 days): 270.62ms -> 270.47ms`  (0.15ms)
- `SearXNG Response time O (30 days): 4.413ms -> 4.412ms`  (0.001ms)

### Fin de spike (RAS)

Quand un temps de reponse passe d une valeur pathologique (>1000ms)
a une valeur normale (<200ms), c est la **resolution d un pic anterieur** :

`Los Galactique Panel Temps de reponse: changed from 2308ms to 75ms`

Reponse : `RAS - fin du spike, retour a la normale.`

### Fin de burst bande passante (RAS)

Quand la bande passante chute d un pic a une valeur basale :

`Pangolin Bandwidth: changed from 15.46MB/s to 0.79MB/s`

Reponse : `RAS - fin de burst reseau.`

## Evenements specifiques notables (RAS mais informatif)

### Linky Heures Creuses

`Linky 02366570155706 Heures creuses actives: triggered (was cleared)`

Les heures creuses viennent de commencer. C'est un evenement **non alarmant** mais
**actionnable** : l'utilisateur peut lancer des machines energivores (lave-linge,
lave-vaisselle, recharge VE, etc.).

Reponse : rapide `RAS` + information sur les heures creuses.

### Météo France / Maree prochaine pluie

`Maree Le Havre Next rain time: changed from 22/07 11:00 to 13/07 16:00`
`Metro-France forecast Le Havre Next rain: changed from 13:55 to 13:50`
`Metro-France forecast Le Havre Daily precipitation: changed from 0mm to 0.1mm`

La prevision meteo de pluie proche se met a jour. Quand l'heure de pluie est
dans les 60 min, mentionner la prevision brievement.

**Transition `unknown → heure_réelle`** : quand la prévision passe de `unknown`
à une vraie date/heure, c'est que les données Météo-France viennent d'être
rafraîchies — RAS, le capteur vient de recevoir une prédiction après une
période sans donnée (typiquement après l'expiration de la précédente).

Reponse : `RAS` + mention de l'heure de pluie prevue le cas échéant.
- `timestamp → unknown` (après échéance dépassée, la prévision expire) — RAS, la prochaine mise à jour la restaure
- `unknown → timestamp` (une nouvelle prévision devient disponible) — RAS, complément normal de l'expiration

Reponse : `RAS` + mention de l'heure de pluie prevue.

### Maree Le Havre Hauteur d eau

`Le Havre Hauteur d eau Actuelle: changed from 2.332m to 2.28m`

Variation de la hauteur d'eau à la descente (marée descendante) ou à la montée (marée montante). Variation de quelques centimètres par tick, normal.

### Maree Le Havre Temperature Eau

`Maree Le Havre Temperature Eau: changed from 18°C to 19°C`

Variation normale de la température de l'eau de mer. RAS.

### Maree Le Havre Pression

`Maree Le Havre Pressure: changed from 1016hPa to 1015hPa`

Variation barométrique normale. RAS.

### F1 Race Météo / piste

`F1 - Race Météo: changed from unknown°C to 28.6°C`

Le capteur de température de piste F1 peut passer de `unknown°C` à une valeur réelle
quand la télémétrie devient disponible. RAS.

### Hermes Uptime erosion cumulee

`hermes.jefe.al Uptime (365 days): changed from 57.59% to 57.41%`

**Pattern distinct** : contrairement aux autres uptimes 365d qui restent quasi inchangés (<0.001%) pendant les vagues, l'uptime 365d d'Hermes (agent conversationnel) peut perdre ~0.18% en une session de vagues intenses. Raison : l'uptime réel sur 365j est déjà bas (~57%) à cause du cumul de toutes les vagues précédentes — chaque nouvelle vague ajoute du vrai downtime dans une fenêtre où le ratio signal/bruit est défavorable. C'est une exception au pattern général. RAS, c'est attendu.

`hermes.jefe.al Uptime (30 days): changed from 60.67% to 60.47%`

L'uptime 30j d'Hermes peut aussi etre bas (~60%) et continuer de baisser de 0.2% par vague monitoring.
C'est normal : Hermes a subi des intermittences pendant les vagues et son uptime
30j reflete le cumul de ces coupures. Aucun impact fonctionnel.

### Mise a jour Elasticsearch F1 horloge (RAS)

`F1 - Race Track time: changed from 15:01 to 15:02`

L'horloge Elasticsearch F1 est une reference temporelle stable qui incremente
de +1 min a chaque tick. Elle n'est jamais impactee par les vagues monitoring.
Utiliser comme indicateur de confiance pendant une vague : si F1 bouge,
l'infrastructure centrale est saine.
