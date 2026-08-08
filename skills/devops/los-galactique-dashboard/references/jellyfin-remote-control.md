# Jellyfin Remote Control via MCP Tools

Key findings from testing Jellyfin Media Player (Windows v1.12.0) on jtower.

## Working Commands
| Action | Endpoint | Notes |
|--------|----------|-------|
| ❌ Pause | `send_command(session_id, "Pause")` | Fails with 400 — JMP rejects this command shape |
| ✅ Pause | `write_api(POST, "Sessions/{id}/Playing/Pause", {}, {})` | Works — returns `[{}]` |
| ✅ Stop | `write_api(POST, "Sessions/{id}/Playing/Stop", {}, {})` | Works — clears NowPlayingItem |
| ✅ Resume | `send_command(session_id, "Unpause")` | Works |
| ✅ Play | `jellyfin_play_remote(session_id, item_ids=["item_id"], mode="PlayNow")` | Works — but starts from beginning |
| ❌ Seek | `write_api(POST, "Sessions/{id}/Playing/Seek", ..., {PositionTicks: N})` | **NOT supported** — Jellyfin Media Player doesn't advertise Seek in its capabilities |
| ❌ Seek | `send_command(session_id, "Seek")` | **NOT supported** — same reason |

## Capabilities Detection
Jellyfin Media Player (Windows, 1.12.0) supports these remote commands:
```
MoveUp, MoveDown, MoveLeft, MoveRight, PageUp, PageDown,
PreviousLetter, NextLetter, ToggleOsd, ToggleContextMenu,
Select, Back, SendKey, SendString, GoHome, GoToSettings,
VolumeUp, VolumeDown, Mute, Unmute, ToggleMute, SetVolume,
SetAudioStreamIndex, SetSubtitleStreamIndex, DisplayContent,
GoToSearch, DisplayMessage, SetRepeatMode, SetShuffleQueue,
ChannelUp, ChannelDown, PlayMediaSource, PlayTrailers
```

Notably missing: **Seek**, **Pause** (send_command variant), **Stop** (send_command variant), **Rewind**, **FastForward**, **NextTrack**, **PreviousTrack**.

## Session ID
The session ID (`f4e1f8b887e703dcbf843bf10b0220ee` for Jefe's jtower) is found in the `get_now_playing` output under `Id`. It's persistent across actions — the same session ID can be used for pause, stop, and play commands.

## Workflow for Pause → Stop → Resume

```python
# 1. Pause
write_api(POST, "Sessions/{session_id}/Playing/Pause", {}, {})

# 2. Stop (clears playback)
write_api(POST, "Sessions/{session_id}/Playing/Stop", {}, {})

# 3. Resume (play from beginning — cannot seek)
jellyfin_play_remote(session_id, [item_id], "PlayNow")
```

## Notes
- Jellyfin Media Player on jtower uses DirectPlay (no transcoding) for most content
- The JMP client has Jefe's user ID: `30174a9fab2b4664a1964a7a8e62aee3`
- After stopping, the session remains active with `NowPlayingQueue` still populated
- The queue persists items — useful if Jefe wants to continue later
