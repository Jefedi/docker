---
name: universal-remote-card
description: Configuring and troubleshooting the Universal Remote Card (Nerwyn) for Home Assistant — multi-platform TV/AVR remote dashboards with buttons, touchpads, sliders, and keyboards.
category: home-automation
triggers:
  - User wants a TV remote control dashboard
  - User mentions "universal remote card" or a specific platform (apple tv, android tv, roku, webos, kodi, etc.)
  - User installs a HACS custom card for media control
  - A custom dashboard card renders blank or shows nothing
---

# Universal Remote Card — Configuration Guide

**Repository:** [Nerwyn/universal-remote-card](https://github.com/Nerwyn/universal-remote-card) (HACS, ~576★)

## Installation

Already installed via HACS (v4.11.4 for this setup). Resource auto-registered.

## Platform-Specific Setup

### Apple TV

Required fields from the card's documentation table:

| Field | Value | Notes |
|-------|-------|-------|
| `platform` | `apple_tv` | Select in General tab |
| `media_player_id` | `media_player.apple_tv_X` | The ACTUAL entity, not a stub |
| `config_entry` | The Apple TV config entry ID | Enables keyboard support |

**Sources & slider:** Provided by the media_player entity.
**Keyboard:** Provided by the config entry.

### Other Platforms

| Platform | Remote Source | Media Player | Keyboard Source |
|----------|--------------|--------------|-----------------|
| Android TV | Default keys + keyboard | Default slider | — |
| Roku | Default keys + keyboard | Default sources + slider + search | — |
| LG webOS | — | Default keys + sources + slider + keyboard | Wake on LAN via MAC |
| Kodi | — | Default keys + sources + slider + keyboard + search | Wake on LAN |
| Samsung TV | Default keys | Default sources + slider (requires custom integration for keyboard) | Wake on LAN |
| Jellyfin | Default keys | Play/pause + slider | — |

## CRITICAL PITFALL: The Blank Card

**Symptom:** Card is added to the dashboard but shows nothing — no buttons, no controls, just empty space or border.

**Root cause:** The card's media_player entity is a **restored stub** with `supported_features=0`. The card needs a real entity with actual capabilities to render its default controls.

**How to check:**
1. Get the state of candidate entities:
   ```python
   ha_get_state(entity_id="media_player.apple_tv")
   ```
2. Look for `supported_features` in attributes:
   - `0` → **STUB**, will render blank
   - Any non-zero value (e.g. `6443523`) → **Real entity**, will render controls
3. Also check for `restored: true` — restored entities are often stale

**Why this happens:** Home Assistant restores entities from the registry even when the device was never properly connected. The Apple TV integration typically creates multiple media_player entities (`apple_tv`, `apple_tv_2`, etc.) but only 1–2 have real device connections.

**Fix:** Point the card's `media_player_id` to an entity with `supported_features > 0`.

## Quick Config (YAML)

Add to a **panel view** for full-screen remote:

```yaml
type: panel
title: "Apple TV"
path: apple-tv
icon: mdi:remote
cards:
  - type: custom:universal-remote-card
    platform: apple_tv
    media_player_id: media_player.apple_tv_2    # Must have supported_features > 0
    config_entry: "01KTVRBW9347FCNJ15DREAKBAD"  # Your actual config entry ID
```

## UI Customization

The card has a built-in editor with 4 tabs:
1. **General** — Platform, entity IDs, timing (hold/double-tap)
2. **Layout** — Grid rows/columns for buttons
3. **Elements** — Add/remove/arrange buttons, circlepads, touchpads, sliders
4. **Icons** — Per-element icon overrides

## References

- `references/apple-tv-setup.md` — Full session transcript and entity diagnosis details
- Card README: https://github.com/Nerwyn/universal-remote-card
