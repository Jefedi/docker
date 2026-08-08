# Servarr — Field Knowledge (Jefe's Infrastructure)

Savoir terrain absent de la doc officielle, compilé depuis les skills existantes
et sessions passées.

## Hardlinks et mount unique /data

Les *arr nécessitent un **seul mount /data** partagé entre Docker et le host pour
que les hardlinks fonctionnent. Si /data est split en /data/media et /data/downloads
(deux volumes Docker), les hardlinks sont impossibles et les fichiers sont copiés
(doublon d'espace).

Pattern correct:
```yaml
volumes:
  - /mnt/nfs/data:/data    # UN SEUL mount
```

Voir `servarr__docker-guide.md` pour le schéma complet.
Voir aussi la skill `media-stack` pour les détails hardlinks/NFS.

## Permissions PUID/PGID

Tous les conteneurs *arr doivent utiliser les mêmes PUID/PGID (généralement
1000:1000). Si qBittorrent utilise un PUID différent, les imports échouent
silencieusement.

Vérifier:
```bash
ls -n /data/downloads/  # UID propriétaire des fichiers
id                      # UID sur le host
```

Voir `servarr__permissions-and-networking.md`.

## NFS jNas -> AX42

TODO — Documenter le passage du NAS jNas au serveur AX42:
- Paths avant: /mnt/jnas/data (à confirmer)
- Paths après: TODO (vérifier montage AX42)
- Impact sur config *arr (root folder), qBittorrent (save path)
- Vérifier que le mount NFS reste un seul /data pour préserver les hardlinks

## Torrents hybrides v1+v2

qBittorrent 5.x (libtorrent 2.x) rejette certains torrents hybrides BitTorrent
v1+v2. Les *arr peuvent marquer ces releases comme failed sans raison apparente.
Solution: désactiver les torrents hybrides dans qBittorrent ou utiliser un client
alternatif (Transmission, Deluge). Voir aussi la skill `torrent-vpn`.

## Radarr/Sonarr API key

Stockée dans `config.xml` (chemin `/config/config.xml` dans le conteneur), pas
dans les variables d'env. Les API keys sont aussi dans `~/.hermes/*.txt`
(fichiers séparés: radarr.txt, sonarr.txt, prowlarr.txt).

Pour récupérer:
```bash
grep -oP '<apikey>\K[^<]+' /config/config.xml
```

## Prowlarr sync vers Sonarr/Radarr/Lidarr

Prowlarr synchronise les indexers vers les autres *arr via Settings > Applications.
Chaque app cible doit être configurée avec:
- URL (avec http:// + port, ex: http://sonarr:8989)
- API key (de l'app cible)

Si le sync échoue, vérifier:
1. L'URL est accessible depuis Prowlarr (même réseau Docker)
2. L'API key est correcte
3. Le type d'app est correct (Sonarr, Radarr, etc.)

TODO: Documenter la configuration exacte Prowlarr > Sonarr/Radarr de Jefe.

## Sonarr v4 vs v5

Sonarr v5 introduit une nouvelle API V5 (`src/Sonarr.Api.V5/openapi.json`).
L'ancienne API V3 reste disponible mais est deprecated. Pour les nouveaux
scripts, utiliser V5. L'openapi.json V5 est dans `sonarr-api-index.md`.

## Prowlarr et indexers privés

Prowlarr gère les indexers privés (trackers torrents, indexers usenet). Pour
les trackers privés nécessitant FlareSolverr (Cloudflare), voir
`prowlarr__prowlarr-setup-flaresolverr.md` (aussi dans TRaSH Guides:
`trash__Prowlarr__prowlarr-setup-flaresolverr.md`).

TODO: Documenter les indexers configurés sur le Prowlarr de Jefe.