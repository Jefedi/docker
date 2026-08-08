# Torrent-VPN — Field Knowledge (Jefe's Infrastructure)

Savoir terrain absent de la doc officielle, compilé depuis les skills existantes
(`qbittorrent`, `gluetun`, `cross-seed`) et sessions passées.

## Infrastructure Map

| Service | Container | Image | Mount | PUID/PGID |
|---------|-----------|-------|-------|-----------|
| qBittorrent | `qbittorrent` | `lscr.io/linuxserver/qbittorrent` (v5.1.4) | `/data` | 1000:1000 |
| Gluetun | `gluetun` | `qmcgaw/gluetun` | `/tmp/gluetun` (port fwd) | N/A |
| cross-seed | `cross-seed` | `crossseed/cross-seed` | `/data` | 1000:1000 |
| Radarr | `radarr` | `lscr.io/linuxserver/radarr` | `/data` | 1000:1000 |
| Sonarr | `sonarr` | `lscr.io/linuxserver/sonarr` | `/data` | 1000:1000 |

- Stockage: NFS depuis jNas (migration vers AX42 en cours)
- Mount unique `/data` critique pour les hardlinks
- VPN: ProtonVPN via Gluetun (WireGuard), port forwarding requis
- API keys: `~/.hermes/*.txt`

## Gluetun + ProtonVPN Port Forwarding

ProtonVPN supporte le port forwarding via Gluetun. Les variables d'env requises:
- `VPN_PORT_FORWARDING=on` (attention: `on`, pas `enabled`)
- `VPN_PORT_FORWARDING_PROVIDER=protonvpn` (utile si on utilise le provider custom)
- Pour OpenVPN uniquement: ajouter `+pmp` au username OpenVPN
- Pour WireGuard: pas de suffixe nécessaire

Le port forwardé est accessible via:
1. Le fichier `/tmp/gluetun/forwarded_port` (sera déprécié en v4.0.0)
2. L'API du control server de Gluetun
3. Un hook `VPN_PORT_FORWARDING_UP_COMMAND` (recommandé pour qBittorrent)

Le hook qBittorrent documenté dans `gluetun__setup__advanced__vpn-port-forwarding.md`
utilise `wget` pour appeler l'API qBittorrent `setPreferences` avec le port forwardé.
Requiert: Web UI sur port 8080 + `bypass_local_auth` activé.

TODO: documenter la config exacte du hook pour le setup de Jefe (WireGuard, linuxserver image).

## qBittorrent 5.x et Torrents Hybrides v1+v2

qBittorrent 5.x (libtorrent 2.x) rejette certains torrents hybrides BitTorrent v1+v2.
Les releases peuvent être marquées comme failed dans Radarr/Sonarr sans erreur
explicite dans qBittorrent — le torrent n'est tout simplement pas ajouté.

**Solution**: désactiver le support hybride dans qBittorrent ou utiliser un client
alternatif (Transmission, Deluge) pour les releases problématiques.

TODO: vérifier si qBittorrent 5.1.4 corrige ce problème. Voir
`qbt__webui-api-(qbittorrent-5.0).md` pour l'API v5.0.

## qBittorrent WebUI Derrière Gluetun

qBittorrent doit être connecté au conteneur Gluetun via `network_mode: "service:gluetun"`
dans le docker-compose. Le port WebUI (8080) doit être exposé sur le conteneur
**Gluetun**, pas sur qBittorrent:

```yaml
services:
  gluetun:
    # ...
    ports:
      - "8080:8080/tcp"  # WebUI qBittorrent exposé via Gluetun
  qbittorrent:
    network_mode: "service:gluetun"
    # PAS de section ports ici
```

Si on expose le port sur qBittorrent au lieu de Gluetun, le WebUI est inaccessible.
Voir `gluetun__setup__connect-a-container-to-gluetun.md` et
`gluetun__setup__port-mapping.md`.

## cross-seed et Partial Matching

cross-seed v6 supporte le partial matching via `matchMode: "partial"`. Utile pour
les releases multi-fichiers où seul un fichier correspond (ex: `.nfo` ou `.srt`
manquants). Peut doubler le nombre de cross-seeds trouvés.

Configuration clé (voir `crossseed__tutorials__partial-matching.md`):
- `matchMode: "partial"` (défaut: `"strict"`)
- `fuzzySizeThreshold: 0.02` (2% de variance de taille, défaut)
- Nécessite linking activé (`crossseed__tutorials__linking.md`)

TODO: documenter la config exacte `partialMatching` pour le setup de Jefe.

## cross-seed Injection Mode

cross-seed supporte l'injection directe dans qBittorrent via `action: "inject"`.
Le mode `inject` copie le torrent directement dans le client via l'API.
Il n'y a PAS de mode `saveSession` ou `announce` — ces termes sont incorrects.
Les modes réels sont: `inject` (injection directe client) ou `save` (sauvegarde
dans `outputDir` sans injection).

Configuration (voir `crossseed__tutorials__injection.md`):
- `action: "inject"` dans la config
- `torrentClients` avec l'URL et credentials de qBittorrent
- Permissions: cross-seed doit partager les mêmes PUID/PGID que qBittorrent
- Arr users: configurer `linking` ou `duplicateCategories: true` pour éviter
  que les cross-seeds n'entrent dans la queue d'import des *arr

TODO: documenter la config exacte pour qBittorrent (catégorie, watch dir, etc).

## PUID/PGID Cohérence

qBittorrent, cross-seed et Gluetun doivent utiliser les mêmes PUID/PGID (1000:1000)
que les *arr. Si qBittorrent écrit avec un UID différent, les *arr ne peuvent pas
importer (permissions denied).

Vérifier avec:
```bash
ls -n /data/downloads
# Tous les fichiers doivent être owned by 1000:1000
```

Si incohérence: `chown -R 1000:1000 /data/downloads` puis redémarrer les conteneurs.

## Kill-Switch Gluetun

Gluetun a un firewall kill-switch intégré. Si le VPN droppe, tout le trafic est
bloqué. qBittorrent s'arrête de downloader. C'est le comportement attendu.
**Ne PAS désactiver le kill-switch.**

Le kill-switch est géré par les règles iptables dans le conteneur Gluetun.
Voir `gluetun__setup__options__firewall.md` et `gluetun__faq__firewall.md`.

Si Gluetun ne se connecte pas au démarrage, qBittorrent (via `network_mode:
service:gluetun`) n'a pas de réseau du tout — c'est normal.

## qBittorrent v4 → v5 Migration

La migration de qBittorrent 4.x vers 5.x peut casser la config WebUI:
- Port WebUI peut être réinitialisé
- Credentials peuvent être perdus (temporaire, régénérés au premier démarrage)
- L'API change de version: v4.1 → v5.0 (voir `qbt__webui-api-(qbittorrent-5.0).md`)

**Sauvegarder `qBittorrent.conf` avant upgrade:**
```bash
cp /config/qBittorrent/qBittorrent.conf /config/qBittorrent/qBittorrent.conf.bak
```

TODO: documenter les breaking changes exacts entre 4.x et 5.x (libtorrent 1.x → 2.x,
suppression du support v1, changements API).

## cross-seed et /data Mount Critique

cross-seed doit avoir accès en lecture au même `/data` que qBittorrent, avec les
mêmes chemins. Si qBittorrent voit `/data/downloads/film.mkv` et cross-seed voit
`/media/downloads/film.mkv`, le matching échoue silencieusement.

Le mount `/data` unique (NFS depuis jNas) est critique pour:
1. Les hardlinks (qBittorrent → *arr import)
2. cross-seed data-based matching (voir `crossseed__tutorials__data-based-matching.md`)
3. cross-seed linking (`crossseed__tutorials__linking.md`)