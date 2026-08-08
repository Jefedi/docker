# cross-seed Documentation

> **Site**: https://cross-seed.org | **GitHub**: https://github.com/cross-seed/cross-seed
> **Image**: `ghcr.io/cross-seed/cross-seed:6` (latest tag alias: `:latest`)
> **Version**: v6.13.7 (June 2026) | **License**: Apache-2.0

---

## Table of Contents

1. [Overview](#overview)
2. [Docker Installation](#docker-installation)
3. [Configuration File (config.js)](#configuration-file-configjs)
4. [Daemon Mode](#daemon-mode)
5. [Torznab Indexers](#torznab-indexers)
6. [qBittorrent Injection](#qbittorrent-injection)
7. [Webhook Triggers](#webhook-triggers)
8. [Key Options Reference](#key-options-reference)

---

## Overview

cross-seed est un outil de cross-seeding automatique. Il cherche des torrents déjà téléchargés sur d'autres trackers et les injecte dans le client torrent pour augmenter le ratio sans téléchargements supplémentaires.

**Clients supportés** : qBittorrent, Deluge, Transmission, rTorrent
**Indexers supportés** : Torznab (via Prowlarr, Jackett, ou indexers natifs)
**Modes de matching** : strict, flexible, partial

**Fonctionnalités avancées** :
- Matching sur fichiers renommés
- Matching partiel (samples, NFOs)
- Matching par ID IMDb/TMDB
- IRC announce matching (via autobrr)
- Notification webhooks (apprise, Notifiarr)
- WebUI intégrée (port 2468)

---

## Docker Installation

### Image officielle

```yaml
# ghcr.io/cross-seed/cross-seed:6
# L'image expose le port 2468
```

### Docker Compose (recommandé)

```yaml
version: "2.1"

services:
  cross-seed:
    image: ghcr.io/cross-seed/cross-seed:6
    container_name: cross-seed
    user: "1000:1000"  # DOIT correspondre au client torrent (pas de support PGID/PUID)
    ports:
      - "2468:2468"
    volumes:
      - /path/to/config/folder:/config
      - /mnt/user/data:/data  # Volume partagé avec le client torrent et les Arrs
    command: daemon
    restart: unless-stopped
```

### Commandes Docker

```shell
# Générer le fichier config.js
docker run -v /path/to/config:/config ghcr.io/cross-seed/cross-seed gen-config

# Lancer le daemon
docker run -v /path/to/config:/config -v /data:/data ghcr.io/cross-seed/cross-seed daemon

# Voir la version
docker run ghcr.io/cross-seed/cross-seed:6 --version

# Récupérer l'API key
docker exec -it cross-seed cross-seed api-key
```

### Contrôle du conteneur

```shell
docker-compose pull          # Mise à jour
docker-compose up -d         # Créer/démarrer
docker start cross-seed      # Démarrer le daemon
docker stop cross-seed       # Arrêter
docker restart cross-seed    # Redémarrer
docker logs cross-seed       # Logs
```

### Règle cruciale pour les paths Docker

**cross-seed et le client torrent DOIVENT voir les mêmes données au même chemin.** Pas de couche de remapping de paths.

✅ **Bon** — Même mount au même chemin partout :
```yaml
qbittorrent:
  volumes: - /mnt/user/data:/data
cross-seed:
  volumes: - /mnt/user/data:/data
  # config.js → dataDirs: ["/data/torrents/movies"]
```

❌ **Mauvais** — Mounts différents :
```yaml
qbittorrent:
  volumes: - /mnt/user/data/torrents:/downloads
cross-seed:
  volumes: - /mnt/user/data:/data
  # qB dit /downloads/Movie, cross-seed cherche /downloads/Movie → échec
```

Les hardlinks doivent être dans le **même volume Docker** (même point de montage).

---

## Configuration File (config.js)

Le fichier utilise la syntaxe JavaScript (`module.exports = { ... }`). Généré avec `cross-seed gen-config`.

### Exemple complet

```js
module.exports = {
    // === INDEXERS ===
    torznab: [
        "http://prowlarr:9696/1/api?apikey=12345",
        "http://prowlarr:9696/2/api?apikey=12345",
    ],

    // === CLIENTS TORRENT ===
    torrentClients: [
        "qbittorrent:http://user:pass@localhost:8080",
        "deluge:http://:pass@localhost:8112/json",
        "transmission:readonly:http://user:pass@localhost:9091/transmission/rpc",
        "rtorrent:http://user:pass@localhost:8080/RPC2",
    ],

    // === LINKING ===
    linkDirs: ["/data/torrents/SomeLinkDirName"],
    linkType: "hardlink",      // hardlink | symlink | reflink | reflinkOrCopy
    linkCategory: "cross-seed-link",
    flatLinking: false,

    // === ACTION ===
    action: "inject",          // inject | save

    // === MATCHING ===
    matchMode: "flexible",     // strict | flexible | partial
    skipRecheck: true,
    includeSingleEpisodes: false,
    seasonFromEpisodes: 1,
    includeNonVideos: false,
    fuzzySizeThreshold: 0.02,

    // === DONNÉES ===
    dataDirs: ["/data/usenet/movies", "/data/torrents/tv"],
    maxDataDepth: 2,
    useClientTorrents: true,
    torrentDir: null,
    outputDir: null,

    // === CADENCES ===
    rssCadence: "30 minutes",
    searchCadence: "1 day",
    delay: 30,

    // === LIMITES ===
    searchLimit: 400,
    excludeOlder: "2 weeks",
    excludeRecentSearch: "3 days",
    excludeRecentSearch: "3 days",

    // === TIMEOUTS ===
    snatchTimeout: "30 seconds",
    searchTimeout: "2 minutes",

    // === DAEMON ===
    host: "0.0.0.0",
    port: 2468,
    apiKey: "VOTRE_CLE",      // 24 caractères min, ou laisser généré

    // === NOTIFICATIONS ===
    notificationWebhookUrls: [],

    // === BLOCKLIST ===
    blockList: [],

    // === Arrs ===
    sonarr: ["http://sonarr:8989/?apikey=12345"],
    radarr: ["http://radarr:7878/?apikey=12345"],
    duplicateCategories: false,
};
```

### Règles importantes
- **NE PAS supprimer d'options** du fichier config.js → erreurs
- Les strings doivent être entre guillemets
- Les tableaux entre crochets `[]`
- Windows : utiliser `\\` pour les paths

---

## Daemon Mode

Le daemon tourne en continu, écoute les RSS, fait les recherches programmées, et expose une API HTTP sur le port 2468.

### Lancement

```shell
# Direct
cross-seed daemon

# Avec logs verbeux
cross-seed daemon --verbose

# Docker
docker run -v /path/to/config:/config ghcr.io/cross-seed/cross-seed daemon
```

Les logs verbeux sont toujours écrits dans `<config_dir>/logs/verbose.current.log`.

### systemd (Linux)

```ini
[Unit]
Description=cross-seed daemon

[Service]
User=MyUserHere
Group=MyGroupHere
Restart=always
Type=simple
ExecStart=cross-seed daemon

[Install]
WantedBy=multi-user.target
```

```shell
sudo systemctl enable cross-seed
sudo systemctl start cross-seed
sudo journalctl -u cross-seed
```

### screen

```shell
screen -S cross-seed -d -m cross-seed daemon
screen -r cross-seed  # attacher
# Détacher : Ctrl-A, D
```

---

## Torznab Indexers

cross-seed utilise le protocole **Torznab** (API newznab pour torrents) via Prowlarr ou Jackett.

### Format des URLs

Chaque URL Torznab doit pointer vers un indexeur spécifique, **pas** vers l'API de base.

```
http://prowlarr:9696/1/api?apikey=TON_API_KEY
                    ^^^
             ID de l'indexeur
```

✅ **Correct** :
```
http://prowlarr:9696/1/api?apikey=12345
http://prowlarr:9696/2/api?apikey=12345
http://jackett:9117/api/v2.0/indexers/oink/results/torznab/api?apikey=12345
```

❌ **Incorrect** (base API Prowlarr) :
```
http://prowlarr:9696/api?apikey=12345
http://prowlarr:9696/api/v1/indexer?apikey=12345
```

### Obtenir les URLs

Dans Prowlarr/Jackett, copier **l'URL RSS** (RSS feed) de l'indexeur — elle fonctionne aussi pour Torznab.

### Résolution des noms en Docker

Utiliser le nom du service Docker, pas `localhost` :
```
http://prowlarr:9696/1/api?apikey=12345  ✅
http://localhost:9696/1/api?apikey=12345  ❌ (sauf si dans le même namespace)
```

### Dépannage

- `responded with invalid XML` → l'URL renvoie du JSON/HTML au lieu du XML Torznab
- Vérifier `/api/ping` sur cross-seed : `curl http://cross-seed:2468/api/ping`
- `Could not resolve host` → nom d'hôte pas accessible
- `Connection refused` → port pas publié ou pas d'écoute

---

## qBittorrent Injection

### Format de connexion

```
qbittorrent:http://user:pass@hôte:8080
```

Pour ne **pas injecter** dans ce client (sourçage seulement) :
```
qbittorrent:readonly:http://user:pass@hôte:8080
```

### Configuration

1. Mettre `action: "inject"` dans config.js
2. Ajouter l'URL dans `torrentClients`
3. Configurer le **linking** (ou utiliser `duplicateCategories: true` pour les utilisateurs d'Arrs)

### Permissions

- `cross-seed` et qBittorrent doivent avoir le **même user:group** (option `user:` dans Docker)
- qBittorrent doit voir les données aux **mêmes paths** que cross-seed

### Arr Users

Si vous utilisez Sonarr/Radarr :
- Configurer le **linking** (`linkDirs`) → recommandé
- OU utiliser `duplicateCategories: true` → injecte avec la catégorie `.cross-seed` pour éviter l'import Arr

### Webhook de complétion (qBittorrent)

Dans **Tools > Options > Downloads** :
```
Run external program on torrent completion:
curl -XPOST http://cross-seed:2468/api/webhook?apikey=TON_API_KEY -d "infoHash=%I" -d "includeSingleEpisodes=true"
```

- `%I` = infohash du torrent (variable qBittorrent)
- `http://cross-seed:2468` depuis un autre conteneur, `http://localhost:2468` depuis l'hôte
- API key obtenue avec `cross-seed api-key`

### Injection manuelle

```shell
cross-seed inject                                 # injecte les .torrent dans outputDir
cross-seed inject --inject-dir /path/to/folder    # injecte depuis un dossier spécifique
cross-seed inject --ignore-titles                 # force l'injection même si titres trop différents
```

**NE PAS** utiliser `outputDir` comme watch folder du client torrent.

### qBittorrent : torrentDir vs useClientTorrents

- **`useClientTorrents: true`** (recommandé) : interroge l'API du client → supporte SQLite, renommage, Content Layout modifié
- **`torrentDir`** : path vers le store de .torrent → pour qB : `~/.local/share/data/qBittorrent/BT_backup`
  - **N'utiliser `torrentDir` que si** vous n'êtes pas en SQLite, pas de renommage, et Content Layout = Original

---

## Webhook Triggers

cross-seed expose une API HTTP qui permet de déclencher des recherches à la complétion d'un téléchargement.

### Endpoint

```shell
curl -XPOST <BASE_URL>/api/webhook?apikey=<API_KEY> -d "infoHash=<infoHash>" -d "includeSingleEpisodes=true"
```

- **BASE_URL** : `http://cross-seed:2468` (Docker) ou `http://localhost:2468` (host)
- **API_KEY** : obtenir avec `cross-seed api-key`
- **infoHash** : infohash du torrent (variable dépend du client)
- **includeSingleEpisodes** : optionnel (permet de search les épisodes individuels à la complétion)

### Par client

| Client | Variable | Commande |
|--------|----------|----------|
| **qBittorrent** | `%I` | `curl -XPOST <BASE_URL>/api/webhook?apikey=<API_KEY> -d "infoHash=%I"` |
| **rTorrent** | `$2` (hash) | Script shell avec `curl -XPOST ... -d "infoHash=$2"` |
| **Transmission** | `$TR_TORRENT_HASH` | Script shell avec `curl -XPOST ... -d "infoHash=$TR_TORRENT_HASH"` |
| **Deluge** | `$1` (hash, via Execute plugin) | Script shell avec `curl -XPOST ... -d "infoHash=$infoHash"` |

---

## Key Options Reference

| Option | CLI | Format | Default | Description |
|--------|-----|--------|---------|-------------|
| `action` | `-A` | `save`/`inject` | `inject` | Sauvegarder ou injecter les cross-seeds |
| `torznab` | `-T` | `string[]` (URLs) | `[]` | URLs Torznab des indexeurs |
| `torrentClients` | `--torrent-clients` | URLs préfixées | `[]` | Clients torrent (ex: `qbittorrent:http://...`) |
| `matchMode` | `--match-mode` | `strict`/`flexible`/`partial` | `flexible` | Algorithme de matching |
| `delay` | `-d` | number (sec) | `30` | Pause entre chaque recherche |
| `rssCadence` | `--rss-cadence` | string (ms) | `30 minutes` | Intervalle RSS (min 10 min) |
| `searchCadence` | `--search-cadence` | string (ms) | `1 day` | Intervalle des recherches catalogue |
| `searchLimit` | `--search-limit` | number | `400` | Nombre max de requêtes par run |
| `port` | `-p` | number | `2468` | Port du daemon |
| `linkType` | `--link-type` | `hardlink`/`symlink`/`reflink` | `hardlink` | Type de lien |
| `linkDirs` | `--link-dirs` | `string[]` | `[]` | Dossiers pour les liens |
| `linkCategory` | `--link-category` | string | `cross-seed-link` | Catégorie pour les torrents injectés |
| `duplicateCategories` | `--duplicate-categories` | boolean | `false` | Injecter avec catégorie `.cross-seed` |
| `flatLinking` | `--flat-linking` | boolean | `false` | Linking plat vs dossiers par tracker |
| `useClientTorrents` | `--use-client-torrents` | boolean | `true` | Interroger les clients via API |
| `dataDirs` | `--data-dirs` | `string[]` | `[]` | Dossiers de données à scanner |
| `blockList` | `--block-list` | `string[]` | `[]` | Filtres (name:, category:, tracker:, etc.) |
| `excludeOlder` | `-x` | string (ms) | `2 weeks` | Exclure les vieilles recherches |
| `excludeRecentSearch` | `-r` | string (ms) | `3 days` | Exclure les recherches récentes |
| `apiKey` | `--api-key` | string (24+ chars) | généré | Clé API pour l'authentification |
| `skipRecheck` | `--skip-recheck` | boolean | `true` | Sauter la vérification des torrents injectés |
| `includeSingleEpisodes` | `--include-single-episodes` | boolean | `false` | Inclure les épisodes individuels |
| `seasonFromEpisodes` | `--season-from-episodes` | number (0-1) | `1` | Agréger épisodes en packs saison |
| `includeNonVideos` | `--include-non-videos` | boolean | `false` | Inclure les torrents non-vidéo |

Sources : docs officielles cross-seed.org, GitHub cross-seed/cross-seed
