#!/usr/bin/env python3
"""Batch re-embed documents from one Qdrant collection to another.

Used when migrating embedding models (e.g., all-MiniLM-L6-v2 384-dim → Qwen3-Embedding-8B 4096-dim).
Reads all points from the old collection (payload only, no vectors), re-embeds via LiteLLM,
and stores in the new collection with fresh vectors.

Features:
- Resume capability: checks existing point count in target collection and skips already-processed docs
- Retry logic: 3 retries with exponential backoff on embedding API failures
- Configurable batch size (smaller = more reliable for large models like 8B)
- Progress reporting every 50 points

Usage:
  python3 reingest_batch.py

Config: edit the constants below (QDRANT_URL, LITELLM_URL, LITELLM_KEY, collections, batch size).
"""

import json
import urllib.request
import time

# === CONFIG ===
QDRANT_URL = "http://localhost:6333"
LITELLM_URL = "https://litelllm.jefe.al/v1/embeddings"  # Pangolin URL (works from n8n and Hermes)
LITELLM_KEY = "<LITELLM_MASTER_KEY>"
OLD_COLLECTION = "ha-docs"       # source (read payloads only)
NEW_COLLECTION = "ha-docs-v2"    # target (store with new vectors)
EMBED_MODEL = "qwen3-embedding"
BATCH_SIZE = 5                    # smaller batches for large models (8B is slow per request)
EMBED_TIMEOUT = 45                # seconds per embed API call
DELAY_BETWEEN_BATCHES = 0.5       # seconds, avoids rate limiting
# === END CONFIG ===

def scroll(collection, offset=None, limit=100):
    body = {"limit": limit, "with_payload": True, "with_vector": False}
    if offset:
        body["offset"] = offset
    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{collection}/points/scroll",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["result"]

def embed(texts, retries=3):
    for attempt in range(retries):
        try:
            body = json.dumps({"model": EMBED_MODEL, "input": texts}).encode()
            req = urllib.request.Request(LITELLM_URL, data=body, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LITELLM_KEY}",
            })
            with urllib.request.urlopen(req, timeout=EMBED_TIMEOUT) as r:
                data = json.loads(r.read())
            return [item["embedding"] for item in data["data"]]
        except Exception as e:
            print(f"    Embed retry {attempt+1}/{retries}: {str(e)[:100]}", flush=True)
            time.sleep(3 * (attempt + 1))
    return None

def store(collection, points):
    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{collection}/points",
        data=json.dumps({"points": points}).encode(),
        method="PUT",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def count_points(collection):
    req = urllib.request.Request(f"{QDRANT_URL}/collections/{collection}")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["result"].get("points_count", 0)

# === MAIN ===
existing = count_points(NEW_COLLECTION)
print(f"Already in {NEW_COLLECTION}: {existing} points", flush=True)

# Fetch all payloads from old collection
all_points = []
offset = None
while True:
    result = scroll(OLD_COLLECTION, offset=offset, limit=100)
    pts = result.get("points", [])
    if not pts:
        break
    all_points.extend(pts)
    offset = result.get("next_page_offset")
    if offset is None:
        break
print(f"Total in {OLD_COLLECTION}: {len(all_points)}", flush=True)

# Skip already processed
skip = existing
print(f"Skipping first {skip} (already done), starting at {skip}", flush=True)

base_id = int(time.time() * 1000) + skip
success = 0
errors = 0
processed = 0

for i in range(skip, len(all_points), BATCH_SIZE):
    batch = all_points[i:i + BATCH_SIZE]
    texts = [p["payload"].get("content", "") for p in batch]
    valid = [(j, t) for j, t in enumerate(texts) if t and len(t.strip()) > 10]
    if not valid:
        continue

    valid_texts = [t for _, t in valid]
    embeddings = embed(valid_texts)

    if embeddings is None:
        errors += len(valid)
        print(f"  FAILED batch at {i}, skipping", flush=True)
        continue

    try:
        pts = []
        for k, (j, _) in enumerate(valid):
            pts.append({
                "id": base_id + processed + k,
                "vector": embeddings[k],
                "payload": batch[j]["payload"],
            })
        store(NEW_COLLECTION, pts)
        success += len(pts)
        processed += len(pts)

        if processed % 50 < BATCH_SIZE:
            print(f"  Progress: +{success} (total ~{existing + success}/{len(all_points)})", flush=True)

        time.sleep(DELAY_BETWEEN_BATCHES)
    except Exception as e:
        errors += len(valid)
        print(f"  Store error at {i}: {str(e)[:100]}", flush=True)

print(f"\n=== DONE ===")
print(f"New: {success}")
print(f"Errors: {errors}")
print(f"Total in {NEW_COLLECTION}: ~{existing + success}")