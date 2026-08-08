---
name: ha-dashboard-remote-cards
description: Configurer l'Universal Remote Card (Nerwyn) dans les dashboards Home Assistant — Apple TV, Android TV, Roku, etc. Couvre la découverte d'entités, les custom_actions, les SVG data URIs, le card_mod styling, et la disposition des boutons.
---

# HA Dashboard — Universal Remote Card

Configurer l'**Universal Remote Card** (Nerwyn) dans un dashboard Home Assistant. Carte custom HACS pour télécommandes de TV/streaming multi-plateforme.

## Prérequis

- HACS installé sur HA
- **Universal Remote Card** installée via HACS (repo: `Nerwyn/universal-remote-card`)
- Ressource Lovelace déjà enregistrée (installation HACS le fait auto)

## Découverte des entités

### Trouver la bonne entité

```python
# Lister les Apple TV
ha_search("apple tv", domain_filter="media_player")
# → 5+ entités, dont des restored stubs
```

⚠️ **Piège : restored stubs** — Vérifier `supported_features` :
- `supported_features: 0` + `restored: true` = **stub**, pas de device réel
- `supported_features > 0` = entité valide (ex: 450487, 6443523)

⚠️ **Piège : noms doublés** — L'intégration Apple TV peut créer `media_player.sejour_sejour` (nom de zone répété). Ne pas supposer `media_player.sejour`. Vérifier avec `ha_get_state`.

### Identifier les entités Remote + Media Player

Pour Apple TV, deux entités sont créées :
- `media_player.sejour_sejour` → contrôles lecture, volume, sources
- `remote.sejour_sejour` → télécommande (touches directionnelles, home, etc.)

Vérifier que les deux existent :
```python
ha_get_state(["media_player.XXXX", "remote.XXXX"])
```

### Config Entry ID (optionnel, pour clavier)

```python
ha_get_integration(domain="apple_tv")
# → entry_id: "01KTV..." + title: "Séjour"
```

Le `config_entry` permet le support clavier sur Apple TV.

## Configuration de base

### Structure de la vue

```yaml
type: sections
max_columns: 1              # Essentiel pour que la télécommande prenne toute la largeur
title: Apple TV 4K
path: apple-tv-4k
icon: mdi:apple
theme: Nordic Blue Dark       # Optionnel — thème HA installé
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
```

### Plateformes supportées

| Plateforme | Remote ID | Media Player ID | Config Entry | Particularité |
|------------|-----------|-----------------|--------------|---------------|
| Apple TV | ✅ (touches par défaut) | ✅ (sources, slider) | ✅ (clavier) | — |
| Android TV | ✅ | ✅ | — | — |
| Roku | ✅ (touches) | ✅ (sources, slider) | — | — |
| LG webOS | — | ✅ (touches, sources, slider) | — | Wake on LAN |
| Samsung TV | ✅ | ✅ (sources) | — | Wake on LAN + custom integration |
| Kodi | — | ✅ (touches, sources, slider) | — | Wake on LAN |
| Jellyfin | ✅ (touches) | ✅ (play/pause + slider) | — | — |
| Generic Remote | — | — | — | `remote.send_command` |

## Custom Actions (boutons non-par-défaut)

Les IDs par défaut (netflix, disney, youtube, primevideo, plex, twitch, etc.) sont supportés nativement par plateforme. Pour les autres :

```yaml
custom_actions:
  - name: jellyfin
    icon: mdi:play-box-multiple          # ou SVG data URI
    label: Jellyfin
    tap_action:
      action: perform-action
      perform_action: media_player.select_source
      target:
        entity_id: media_player.sejour_sejour
      data:
        source: Jellyfin
  - name: spotify
    icon: mdi:spotify
    label: Spotify
    tap_action:
      action: perform-action
      perform_action: media_player.select_source
      target:
        entity_id: media_player.sejour_sejour
      data:
        source: Spotify
```

⚠️ **Piège : nom du source** — Le nom dans `data.source` doit correspondre EXACTEMENT au `source_list` de l'entité (sensible à la casse). Vérifier avec :
```python
ha_get_state("media_player.sejour_sejour")
# → attributes.source_list: ["Jellyfin", "Spotify", "Streamyfin", ...]
```

## Logos des marques

### Icônes MDI recommandées

Le champ `icon` des `custom_actions` ne supporte **que les chaînes MDI** (`mdi:spotify`, `mdi:play-circle`, etc.). Les SVG data URIs ne s'affichent pas. Utiliser les MDI les plus proches de la marque :

| Marque | Icône MDI | Couleur `--remote-button-color` |
|--------|-----------|-------------------------------|
| Spotify | `mdi:spotify` (vrai logo) | `#1DB954` |
| Jellyfin | `mdi:play-circle` | `#00A4DC` |
| Streamyfin | `mdi:movie-open` | `#E50914` |
| Plex | `mdi:plex` (si disponible) ou `mdi:play-box` | `#E5A00D` |
| Prime Video | `mdi:amazon` | `#00A8E1` |

### Couleur de marque via CSS

La méthode fiable pour colorer un bouton custom est `--remote-button-color` sur `[data-id]` dans `card_mod` :

```css
[data-id="jellyfin"] { --remote-button-color: #00A4DC !important; }
[data-id="streamyfin"] { --remote-button-color: #E50914 !important; }
[data-id="spotify"] { --remote-button-color: #1DB954 !important; }
```

### ❌ Piège : SVG data URI dans le champ `icon` NE MARCHE PAS

Le champ `icon` de l'Universal Remote Card utilise le système d'icônes Home Assistant qui ne supporte **que** les identifiants MDI. Les SVG data URIs (même correctement encodés) ne s'affichent pas.

### ❌ Piège : CSS `background: url(...)` sur `::part(icon)` CASSE TOUS LES ICÔNES

```css
/* NE PAS FAIRE — rend tous les boutons invisibles */
#jellyfin::part(icon) {
  background: url('data:image/svg+xml,...') center/contain no-repeat !important;
  color: transparent !important;
}
```
Cette approche brise le rendu de l'icône et peut cacher **tous** les boutons de la rangée, pas seulement celui visé.

## Disposition des boutons (Layout)

Les `rows` sont des tableaux imbriqués. Chaque tableau externe = une rangée.

```yaml
rows:
  - - back
    - power
    - home
    - menu
  - - touchpad              # Pavé tactile swipe
  - - volume_buttons        # Shorthand : volume_down + mute + volume_up
  - - rewind
    - previous
    - play_pause
    - next
    - fast_forward
  - - netflix
    - jellyfin
    - spotify
    - twitch
    - streamyfin
    - youtube
```

### Éléments spéciaux disponibles

| Nom | Type | Description |
|-----|------|-------------|
| `touchpad` | touchpad | Pavé tactile swipe (navigation) |
| `dragpad` | touchpad | Pavé tactile drag (2 doigts = plus rapide) |
| `circlepad` | circlepad | 5 boutons directionnels en cercle |
| `slider` | slider | Curseur volume (media_player) |
| `volume_buttons` | rows | Volume down + mute + up |
| `dpad` | grid | Pavé directionnel 3×3 |
| `numpad` | grid | Chiffres 1-9 |
| `navigation_buttons` | rows | Flèches sur 3 lignes |

## Card Mod Styling

```yaml
card_mod:
  style: >
    ha-card {
      background: linear-gradient(135deg, #1f2937, #4b5563) !important;
      border-radius: 20px !important;
      border: 1px solid rgba(0, 212, 255, 0.2) !important;
      padding: 4px !important;
    }
    .touchpad {
      height: 100px !important;
      min-height: 100px !important;
    }
    .remote-button {
      --remote-button-background: rgba(255, 255, 255, 0.05) !important;
      --remote-button-color: #f9fafb !important;
      height: 48px !important;
    }
    .remote-row {
      justify-content: center !important;
    }
    .remote-row-container {
      gap: 2px !important;
    }
    /* Couleur par bouton */
    [data-id="power"] { --remote-button-color: #ff5252 !important; }
    [data-id="play_pause"] { --remote-button-color: #00d4ff !important; }
    /* Boutons custom — couleur de marque via CSS variable */
    [data-id="jellyfin"] { --remote-button-color: #00A4DC !important; }
    [data-id="spotify"] { --remote-button-color: #1DB954 !important; }
    [data-id="streamyfin"] { --remote-button-color: #E50914 !important; }
```

## Pièges

### Entité indisponible

Si l'Apple TV est éteinte, la carte montre "Unavailable" ou rien. C'est normal — allumer l'appareil rétablit l'entité.

### Mauvais entity_id

L'Universal Remote Card ne montre rien si l'entité n'existe pas ou est un stub (`supported_features: 0`). Vérifier avec `ha_get_state()` avant.

### Sources introuvables

Les boutons custom avec `media_player.select_source` échouent silencieusement si le nom de source ne correspond pas EXACTEMENT à ceux dans `source_list`.

### Logo SVG non affiché

Si le SVG data URI ne s'affiche pas, vérifier :
- L'encodage URL est correct (`%23` pour `#`, pas de `"` non encodés)
- La card supporte bien les data URIs (testé avec Universal Remote Card v4.11.4)
- Fallback : utiliser un `mdi:` standard + label textuel

### ❌ `::part(icon)` avec background-image

```css
/* NE PAS FAIRE — casse TOUS les icônes de la rangée */
#jellyfin::part(icon) {
  background: url('data:image/svg+xml,...') center/contain no-repeat !important;
  color: transparent !important;
}
#jellyfin .icon { display: none !important; }
```

Le rendu des icônes dans la card est géré en interne via le composant `<ha-icon>`. Essayer de remplacer son contenu par une image de fond via `::part(icon)` brise le rendu de **tous** les boutons, pas seulement celui visé. Utiliser `--remote-button-color` pour la marque visuelle, et garder les icônes MDI.

### Vue sections + colonnes

Pour une télécommande, toujours mettre `max_columns: 1` sur la vue sections — sinon la carte peut être rétrécie par la grille responsive.

## Références

- `references/apple-tv-session-20260711.md` — Session détaillée de configuration Apple TV (découverte entités, corrections, logs)
