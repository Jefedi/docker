# QualityProfile API Creation Workaround

Sonarr's qualityprofile POST endpoint has a strict `AllQualitiesValidator` that requires **all** quality IDs currently registered in the system to be present in the `items` array. The exact set of required IDs changes over time as Sonarr deprecates/removes old qualities (WORKPRINT, CAM, TELESYNC, etc.).

## The Problem

A naive POST with only the qualities you want to allow fails with:

```
"Must contain all qualities"  (AllQualitiesValidator)
"Cutoff must be an allowed quality or group"  (ValidCutoffValidator)
```

## The Fix: Clone-and-Modify

1. **GET the "Any" profile** (id=1) — this always has the correct, up-to-date item structure
2. **Modify the response**: change `name`, set `allowed` flags, update `formatItems` scores, set `cutoff`, etc.
3. **Remove the `id` field** so POST creates a new profile
4. **POST** the modified payload

### Python Pattern

```python
import httpx

headers = {"X-Api-Key": "your-key", "Accept": "application/json"}

# 1. Get the reference profile
r = httpx.get("http://sonarr:8989/api/v3/qualityprofile/1", headers=headers)
profile = r.json()

# 2. Modify for the new profile
profile["name"] = "1080p x264 Direct Play"
del profile["id"]  # New profile — let Sonarr assign the ID
profile["cutoff"] = 1002  # WEB 1080p group ID

allowed = {3, 5, 6, 7, 14, 15}  # WEBDL/Bluray 1080p and 720p
for item in profile["items"]:
    if "quality" in item and item["quality"]:
        item["allowed"] = item["quality"]["id"] in allowed
    for sub in item.get("items", []):
        if "quality" in sub:
            sub["allowed"] = sub["quality"]["id"] in allowed
    if "id" in item and isinstance(item["id"], int) and item["id"] >= 1000:
        item["allowed"] = any(sub.get("allowed", False) for sub in item.get("items", []))

profile["formatItems"] = [
    {"format": 551, "score": -10000},  # x265
    {"format": 552, "score": -10000},  # LQ
    {"format": 553, "score": -10000},  # No-RlsGroup
    {"format": 554, "score": 500},     # MULTI
    {"format": 555, "score": -50},     # VOSTFR
]
profile["minUpgradeFormatScore"] = 1

# 3. POST
r2 = httpx.post("http://sonarr:8989/api/v3/qualityprofile", headers=headers, json=profile)
# → id=19, name="1080p x264 Direct Play"
```

## Key Points

- NEVER try to construct the `items` array manually — the validator is version-sensitive and will reject valid structures if the order or included IDs don't match exactly.
- The "Any" profile (id=1) is the canonical reference because it was auto-created by Sonarr and always passes its own validator.
- Cutoff value must be an `int` (quality ID), never an object `{"id": N}`.
- After creation, assign the profile to a series via `PUT /api/v3/series/{id}` with `qualityProfileId: new_id`.
