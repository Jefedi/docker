# Dedup Normalization Rules

Exact regex patterns used to normalize Spotify track titles and artist names for duplicate detection.

## Title normalization

### 1. Remove parenthetical/bracket variant suffixes
```python
t = re.sub(
    r'\s*[\(\[](?:live|concert|acoustic|remix|radio edit|version|remastered|demo|strip|session|studio|bonus|feat|ft)[^\)\]]*[\)\]]',
    '', t, flags=re.IGNORECASE
)
```
Strips: `(Live)`, `(Live at Wembley)`, `(Acoustic Version)`, `(Remix)`, `(Radio Edit)`, `(Remastered 2012)`, `(Session)`, `(Bonus Track)`, `(Feat. Someone)`, etc.

### 2. Remove dash-style suffixes
```python
t = re.sub(
    r'\s*[-–]\s*(live|acoustic|remix|concert|session|version|remastered|demo|strip|radio edit)\b.*$',
    '', t, flags=re.IGNORECASE
)
```
Strips: `- Live`, `- Acoustic`, `- Remix`, `- Concert Version`, etc.

### 3. Remove any remaining trailing parenthetical
```python
t = re.sub(r'\s*[\(\[].*[\)\]]$', '', t)
```
Catches leftover parenthetical content after the targeted removals above.

### 4. Collapse whitespace
```python
t = re.sub(r'\s+', ' ', t).strip()
```

### 5. Lowercase
```python
t = t.lower()
```

## Artist normalization

### 1. Lowercase and strip
```python
a = artist.lower().strip()
```

### 2. Remove featuring artists
```python
a = re.sub(r'\s+(feat|ft|featuring)\s+.*$', '', a)
```
Turns `Eminem, Dido` → stays as is (comma-separated collaborators are kept).
Turns `Artist feat. Someone` → `Artist`.

## Grouping key

```python
key = f"{normalized_artist} - {normalized_title}"
```

Any group with more than 1 entry is a duplicate set.

## Album classification for "which to keep"

### Best-of / compilation indicators (DON'T keep these)
- "Best Of", "Greatest Hits", "Curtain Call", "The Hits"
- "Soundtrack", "OST", "STANS (The Official Soundtrack)"
- "Collection", "Anthology", "Essential"

### Deluxe / extended indicators (prefer standard edition)
- "Deluxe", "Extended", "Complete", "Anniversary"

### Single indicators (prefer album version)
- Album name equals track name (likely a single release)

### Priority logic
```python
def album_priority(album_name, track_name):
    a = album_name.lower()
    t = track_name.lower()
    if any(x in a for x in ['best of', 'greatest hits', 'curtain call', 'the hits', 'soundtrack', 'ost', 'collection', 'anthology']):
        return 0  # lowest priority
    if any(x in a for x in ['deluxe', 'extended', 'complete', 'anniversary']):
        return 1
    if a == t:  # single release
        return 2
    return 3  # original studio album — highest priority
```

When priority is equal, keep the track with the earliest `added_at` timestamp.