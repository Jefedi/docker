# Music Assistant — Diagnostic des logs

## Add-on info

- Slug : `d5369777_music_assistant`
- Version stable : 2.9.9 (dernière au 2026-07-24)
- Versions alternatives : BETA (`_beta`), NIGHTLY (`_nightly`), DEV (`_dev`)
- Repository : `music-assistant/home-assistant-addon`

## Lecture des logs MA

```python
# Via MCP — logs du conteneur add-on
ha_get_logs(source="supervisor", slug="d5369777_music_assistant", limit=100)
```

## Erreurs connues et diagnostic

### 1. librespot `audio key error 0 1` — Spotify ne joue pas

**Symptômes :**
```
librespot_core::audio_key] error audio key 0 1
librespot_playback::player] Unable to read audio file: Passthrough Decoder Error: No Ogg capture pattern found
Librespot exited with code -15
Failed to stream audio
```

**Cause :** Bug upstream librespot (Issue #1649, ouvert nov 2025). Spotify change progressivement la méthode de délivrance des clés audio côté serveur. Le rollout se fait compte par compte — certains comptes sont touchés, d'autres pas.

**IMPORTANT :** Ce n'est PAS un problème d'authentification. Le relogin Spotify réussit (`Successfully logged in as Jefe`) mais l'erreur persiste car c'est le **protocole d'audio key** qui change.

**Vérifications :**
1. Compte Premium requis (librespot ne marche pas sans Premium)
2. MA à jour ? (`ha_get_addon(query="music assistant")` → vérifier `update_available`)
3. Si 2.9.9 et toujours KO → bug upstream, pas de fix immédiat

**Solutions possibles :**
- Installer MA BETA ou NIGHTLY (peut inclure une version plus récente de librespot)
- Patienter — MA va updater sa version de librespot quand le fix sera mergé en amont
- Issue de référence : https://github.com/librespot-org/librespot/issues/1649

### 2. HA 502 — Connection to HA lost

```
Connection to HA lost. Connection will be automatically retried later.
Error loading provider(instance) Home Assistant: 502, message='Invalid response status', url='ws://supervisor/core/api/websocket'
```

**Cause :** HA restart ou indisponibilité temporaire. MA retente automatiquement la connexion toutes les 2 minutes.

**Action :** RAS — auto-récupéré après ~6 min. Vérifier si un restart HA a eu lieu à ce moment.

### 3. zeroconf — No such device / Network unreachable

```
zeroconf] Error with socket (('100.64.0.8', 5353))): [Errno 19] No such device
zeroconf] Error with socket (('fd7a:115c:a1e0::8', 5353, 0, 0))): [Errno 101] Network is unreachable
```

**Cause :** Interface réseau Tailscale (100.64.x.x / fd7a:...) brièvement perdue. zeroconf (mDNS) essaie de broadcast sur cette interface.

**Action :** RAS — auto-récupéré quand Tailscale revient. Si récurrent, vérifier `tailscale status` sur le serveur HA.

### 4. MusicBrainz — Rate Limiter

```
Attempt 1/5 failed: Rate Limiter
Retrying in 60 seconds...
```

**Cause :** MusicBrainz limite à 1 req/s. MA retente automatiquement (jusqu'à 5 tentatives avec backoff ~60s).

**Action :** RAS — normal, finit par réussir.

### 5. Last.fm — 0 recommendations

```
Building Last.fm recommendations
Last.fm recommendations built (0 folders)
```

**Cause :** Soit peu de musique en bibliothèque, soit Last.fm n'arrive pas à corréler. Toutes les 6h.

**Action :** Vérifier que les providers de musique (filesystem, Spotify, etc.) ont bien scanné la bibliothèque. Pas critique.

### 6. Queue vide — Resume queue requested but queue is empty

```
players/cmd/play_pause: Resume queue requested but queue Web (Firefox on Windows) is empty
```

**Cause :** L'utilisateur a cliqué play sans avoir mis de piste dans la file d'attente.

**Action :** RAS — pas un bug, juste un clic prématuré.

### 7. Spotify — Timeout authentication callback

```
config/providers/get_entries: Timeout while waiting for authentication callback
```

**Cause :** Le callback OAuth Spotify n'est pas arrivé à temps (fenêtre de login fermée trop tôt ou réseau).

**Action :** Relancer la connexion Spotify dans MA (Settings → Music Providers → Spotify → re-login). Le log doit afficher `Successfully logged in to Spotify` + `Developer Spotify session active`.

## Workflow de diagnostic

1. Lire les logs récents : `ha_get_logs(source="supervisor", slug="d5369777_music_assistant", limit=200)`
2. Filtrer les WARNING/ERROR : ignorer les `genre mapping scan completed` (INFO, normal toutes les 3h)
3. Identifier l'erreur principale (audio key > 502 HA > zeroconf > rate limit)
4. Pour Spotify : vérifier Premium + version MA + upstream issue #1649
5. Pour HA 502 : vérifier les restarts HA à la même heure
6. Pour zeroconf : vérifier Tailscale