# Apple TV Remote — Setup Debug Session

## Context

- **Dashboard:** "Maison" (`maison-dashboard`), view "Apple TV" (`apple-tv`)
- **Card:** Universal Remote Card v4.11.4 via HACS
- **Integration:** Apple TV config entry titled "Séjour" (entry_id: `01KTVRBW9347FCNJ15DREAKBAD`)

## Entities Found

| Entity ID | Restored? | supported_features | Status |
|-----------|-----------|-------------------|--------|
| `media_player.apple_tv` | ✅ yes | **0** ❌ | Stub — never connected |
| `media_player.apple_tv_2` | ✅ yes | **6443523** ✅ | Real device, has capabilities |
| `media_player.apple_tv_3` | ✅ yes | **0** ❌ | Stub |
| `media_player.apple_tv_4` | ✅ yes | **0** ❌ | Stub |
| `media_player.ios` | ❌ no | **6443523** ✅ | Real device (possibly iOS companion?) |

## Debug Steps

1. Added the card with `media_player_id: media_player.apple_tv` 
2. User reported blank view ("je vois rien")
3. Checked entities with `ha_get_state(entity_id="media_player.apple_tv")` — found `supported_features: 0` and `restored: true`
4. Checked ALL Apple TV entities — found that `_2` and `ios` had proper `supported_features: 6443523`

## Key Lesson

The Universal Remote Card needs a **real entity** with proper `supported_features` to render its default controls. A restored stub with `supported_features=0` produces a completely blank card with no error message.

Always verify with `ha_get_state()` before wiring a custom card that depends on entity capabilities.
