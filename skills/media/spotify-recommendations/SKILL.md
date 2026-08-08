---
name: spotify-recommendations
description: "Suggest music from Spotify liked tracks, build a playlist."
---

# Spotify Recommendations from Liked Tracks

## Trigger
- User asks for music recommendations / suggestions based on their tastes
- User wants a playlist with songs they might like
- User says "propose-moi de la musique", "qu'est-ce que j'aimerais ?", "fait une playlist selon mes goûts"

## Workflow

### Step 1 — Fetch all liked tracks
1. Call `spotify_library(kind="tracks", action="list", limit=50, offset=0)` to get total count
2. Fetch all pages (offset 0, 50, 100, ... up to total) in parallel batches of 6 calls max
3. Large pages (>100KB) are saved to `/tmp/hermes-results/` — use `search_files(pattern="artist_name", path="/tmp/hermes-results")` to scan them efficiently instead of reading full files
4. For inline pages, scan the JSON directly in the tool output

### Step 2 — Analyze the library
Extract and count:
- **Top artists** (by frequency, dedup by artist ID)
- **Genres/regions** (e.g. rap FR, albanais, international, variété)
- **Albums** that appear multiple times (indicates fan of that album)
- **Explicit vs non-explicit** ratio
- **Era** (release dates distribution)

Group artists by region/style:
- 🇫🇷 Rap français (Ninho, PNL, Damso, Jul, Booba, etc.)
- 🇦🇱 Albanais/Balkan (Noizy, Mozzik, Elvana Gjata, Capital T, etc.)
- 🌍 International/US (Drake, Post Malone, Bruno Mars, etc.)
- 🎵 Variété/chanson (Aznavour, etc.)
- 🔊 Electronic/dance (Avicii, Alan Walker, etc.)

### Step 3 — Build recommendation list
For each identified genre/region cluster:
1. List 2-3 artists the user already listens to heavily
2. Propose 2-3 **similar artists** they don't have in their library
3. For each suggested artist, pick 1-2 specific tracks

**Suggestion sources:**
- Same genre, same region, artist not in library
- Collaborations between artists already in library
- Featured artists on tracks already liked
- Cult tracks from the genre

### Step 4 — Search tracks on Spotify
1. Batch `spotify_search(type="track", limit=1, query="Artist TrackName")` calls — up to 30 in parallel
2. Verify each result: artist name must match (case-insensitive)
3. Skip duplicates (same track ID already in library)
4. Skip wrong matches (e.g. classical music when searching rap) — check artist name in result
5. Collect URIs

### Step 5 — Create playlist
1. `spotify_playlists(action="create", name="Hermest ❤️", public=false, description="...")`
2. `spotify_playlists(action="add_items", playlist_id=<id>, uris=[...])`
3. Return the Spotify URL to the user

### Step 6 — Present results
Format output by category with flags:
```
🇫🇷 Rap français:
- Artist — Track name

🌍 Albanais/Balkan:
- Artist — Track name

🌍 International:
- Artist — Track name
```

Include the playlist link at the top.

## Pitfalls
- Spotify search is fuzzy — "Ninho Pop Smoke" may return a compilation track by another artist. Always verify the artist name in the result matches.
- Some tracks have multiple versions (deluxe, reissue, compilation) — dedup by track name + primary artist.
- Library can be large (300+ tracks) — use parallel fetch and file-based scanning for efficiency.
- `spotify_library(action="remove")` uses `items` parameter (not `uris`) for track URIs.
- Creating playlists: `spotify_playlists(action="add_items")` uses `uris` parameter.
- Max 100 tracks per `add_items` call.

## Language
Respond in the user's language (French by default for this user).