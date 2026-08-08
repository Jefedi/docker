---
name: cross-seed
description: Cross-seed automatique. Cherche des torrents déjà téléchargés sur d'autres trackers et les injecte dans le client torrent.
category: media
---

# Cross-Seed — Guide de référence

> **Image :** `ghcr.io/cross-seed/cross-seed:latest` (tag `:6` alias latest)  
> **Port API :** `2468`  
> **Site :** https://cross-seed.org  
> **Config :** `config.js` (généré par `cross-seed gen-config`)

Cross-seed cherche automatiquement des torrents que vous avez déjà téléchargés sur d'autres trackers et les injecte dans votre client torrent pour augmenter le ratio.

---

## 1. Docker Compose

```yaml
  cross-seed:
    image: ghcr.io/cross-seed/cross-seed:latest
    container_name: cross-seed
    restart: unless-stopped
    network_mode: service:gluetun
    depends_on:
      gluetun:
        condition: service_healthy
    environment:
      - TZ=Europe/Paris
    volumes:
      - ./configs/cross-seed:/config
      - "${COMMON_PATH}:/data"
      - ./configs/qbittorrent/qBittorrent/BT_backup:/torrent_files:ro
    command: daemon
```

## 2. Règle #1 — Les chemins doivent être IDENTIQUES

Cross-seed compare les paths entre ce qu'il trouve sur le filesystem et ce que le client torrent rapporte. **Pas de remapping de paths** — le montage doit être le même pour cross-seed et qBittorrent.

## 3. Configuration via `config.js`

Générer avec `cross-seed gen-config` puis ajuster. Fichier JS module export, **ne jamais supprimer de clés**.

### Variables clés

| Variable | Description |
|---|---|
| `torznab` | Tableau d'indexeurs : `[{name, url: "http://prowlarr:9696/ID/api", apiKey}]` |
| `qbittorrent` | Connexion : `qbittorrent:http://user:pass@host:8080` |
| `injectionMode` | `inject` (direct), `save` (fichiers .torrent), `inject_save` |
| `duplicateCategories` | `true` pour utiliser les catégories sans toucher aux Arr |
| `linkDir` | Répertoire de liens pour le mode "linking" |
| `matchMode` | `safe` (strict), `risky` (permissif) |
| `searchCadence` | Fréquence de recherche (`"every 30 minutes"`, etc.) |
| `rssCadence` | Fréquence RSS (`"every 10 minutes"`) |
| `dataDirs` | Répertoires à scanner pour les données |

## 4. Intégrations

- **qBittorrent :** injection directe via API `http://user:pass@host:8080`
- **Prowlarr :** indexers Torznab (URL type: `http://prowlarr:9696/1/api?apikey=...`)
- **Announce Matching :** écoute les annonces RSS des indexeurs en temps réel
- **Linking :** crée des liens physiques au lieu de torrents séparés
- **Webhook :** déclenchement par arrivée d'un nouveau torrent (`%I` pour le hash)

## 5. Modes

- **Daemon** (`command: daemon`) : tourne en continu
- **Search** : recherche unique déclenchée manuellement
- **Webhook** : déclenché par arrivée de nouveau torrent dans le client

## 6. Logs

- Logs verbeux dans `<config>/logs/verbose.current.log`
- Niveau `info` par défaut

## 7. Setup checklist

1. Générer `config.js` avec `docker exec cross-seed cross-seed gen-config`
2. Configurer les indexeurs Torznab (URL + API key depuis Prowlarr)
3. Configurer la connexion qBittorrent
4. Vérifier que les montages filesystem sont identiques cross-seed / qBittorrent
5. Démarrer en mode daemon
