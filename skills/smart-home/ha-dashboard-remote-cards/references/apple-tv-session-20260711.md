# Apple TV Remote — Session du 11 juillet 2026

Configuration de l'Universal Remote Card pour Apple TV "Séjour" sur le dashboard Maison.

## Entités découvertes

| Entité | État | Particularité |
|--------|------|---------------|
| `media_player.sejour_sejour` | off | ✅ Réel — sources: Jellyfin, Spotify, YouTube, etc. |
| `remote.sejour_sejour` | on | ✅ Réel — télécommande physique |
| `remote.sejour` | ❌ inexistante | N'existe pas (pas de doublon) |
| `media_player.sejour` | ❌ inexistante | N'existe pas |
| `media_player.apple_tv` | unavailable | ❌ Stub (restored=true, supported_features=0) |
| `media_player.apple_tv_2` | unavailable | Stub avec features (restored) |
| `media_player.ios` | unavailable | Stub étiqueté "Apple TV" |

## Sources disponibles

```
AdGuard Home, App Store, Arcade, F1 TV, FaceTime, Forme, Free TV,
Jellyfin, Musique, Ordinateurs, Photos, Podcasts, Proton VPN,
Rechercher, Réglages, Spotify, Streamyfin, Tailscale, TestFlight,
Trakt, TV, Twitch, UGREEN NAS, YouTube
```

## Diff entre l'ancienne et la nouvelle config

### Ancienne (ne marchait pas)
```yaml
type: panel
title: Apple TV
path: apple-tv
icon: mdi:remote
cards:
  - type: custom:universal-remote-card
    platform: apple_tv
    media_player_id: media_player.apple_tv   # ❌ stub vide
    config_entry: 01KTVRBW9347FCNJ15DREAKBAD
```

### Nouvelle (fonctionnelle)
```yaml
type: sections
max_columns: 1
title: Apple TV 4K
path: apple-tv-4k
theme: Nordic Blue Dark
icon: mdi:apple
sections:
  - type: grid
    cards:
      - type: media-control
        entity: media_player.sejour_sejour
      - type: custom:universal-remote-card
        remote_id: remote.sejour_sejour
        media_player_id: media_player.sejour_sejour
        platform: Apple TV
        grid_options:
          columns: full
        card_mod:
          style: "ha-card { background: linear-gradient(135deg, #1f2937, #4b5563) !important; ... }"
        rows:
          - [back, power, home, menu]
          - [touchpad]
          - [volume_buttons]
          - [rewind, previous, play_pause, next, fast_forward]
          - [netflix, jellyfin, spotify, twitch, streamyfin, youtube]
        custom_actions:
          - name: jellyfin
            icon: "data:image/svg+xml,%3Csvg..."
            label: Jellyfin
            tap_action:
              action: perform-action
              perform_action: media_player.select_source
              target: {entity_id: media_player.sejour_sejour}
              data: {source: Jellyfin}
          - name: spotify
            icon: mdi:spotify
            label: Spotify
            tap_action:
              action: perform-action
              perform_action: media_player.select_source
              target: {entity_id: media_player.sejour_sejour}
              data: {source: Spotify}
          - name: streamyfin
            icon: "data:image/svg+xml,%3Csvg..."
            label: Streamyfin
            tap_action:
              action: perform-action
              perform_action: media_player.select_source
              target: {entity_id: media_player.sejour_sejour}
              data: {source: Streamyfin}
```

## Corrections en cours de route

1. **Entity ID erroné** : `media_player.apple_tv` → `media_player.sejour_sejour`
2. **Ajout remote_id** : `remote.sejour_sejour` nécessaire pour les touches directionnelles
3. **Platform string** : `apple_tv` → `Apple TV` (casse différente selon version)
4. **Apps custom** : Plex/PrimeVideo → Jellyfin/Spotify → remplacement Disney → Streamyfin
5. **Logos** : Icônes MDI génériques → SVG data URIs pour Jellyfin et Streamyfin

## Commandes MCP utilisées

```python
# Découverte entités
ha_search("apple tv", domain_filter="media_player")
ha_get_state(["media_player.apple_tv", "media_player.sejour_sejour", ...])
ha_get_integration(domain="apple_tv")

# Dashboard
ha_config_get_dashboard(url_path="maison-dashboard")
ha_config_set_dashboard(url_path="maison-dashboard", python_transform="...", config_hash="...")
```
