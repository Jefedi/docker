#!/usr/bin/env python3
"""Re-ingest docs from ha-docs to ha-docs-v2 - resume from existing count"""

import json
import urllib.request
import time
import sys

QDRANT_URL = "http://localhost:6333"
LITELLM_URL = "https://litelllm.jefe.al/v1/embeddings"
LITELLM_KEY = "sk-JZIHNyIBf7EkeAR4-A2BGw"
OLD = "ha-docs"
NEW = "ha-docs-v2"
BATCH = 5  # smaller batches

def scroll(collection, offset=None, limit=50):
    body = {"limit": limit, "with_payload": True, "with_vector": False}
    if offset: body["offset"] = offset
    req = urllib.request.Request(f"{QDRANT_URL}/collections/{collection}/points/scroll",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["result"]

def embed(texts, retries=3):
    for attempt in range(retries):
        try:
            body = json.dumps({"model": "qwen3-embedding", "input": texts}).encode()
            req = urllib.request.Request(LITELLM_URL, data=body, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LITELLM_KEY}"
            })
            with urllib.request.urlopen(req, timeout=45) as r:
                data = json.loads(r.read())
            return [item["embedding"] for item in data["data"]]
        except Exception as e:
            print(f"    Embed retry {attempt+1}/{retries}: {str(e)[:100]}", flush=True)
            time.sleep(3 * (attempt + 1))
    return None

def store(collection, points):
    req = urllib.request.Request(f"{QDRANT_URL}/collections/{collection}/points",
        data=json.dumps({"points": points}).encode(), method="PUT",
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

# Count existing in new collection
req = urllib.request.Request(f"{QDRANT_URL}/collections/{NEW}",
    headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    existing = json.loads(r.read())["result"].get("points_count", 0)
print(f"Already in {NEW}: {existing} points", flush=True)

# Fetch all from old
all_points = []
offset = None
while True:
    result = scroll(OLD, offset=offset, limit=100)
    pts = result.get("points", [])
    if not pts: break
    all_points.extend(pts)
    offset = result.get("next_page_offset")
    if offset is None: break
print(f"Total in {OLD}: {len(all_points)}", flush=True)

# Skip already processed (existing count)
skip = existing
print(f"Skipping first {skip} (already done), starting at {skip}", flush=True)

base_id = int(time.time() * 1000) + skip
success = 0
errors = 0
processed = 0

for i in range(skip, len(all_points), BATCH):
    batch = all_points[i:i+BATCH]
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
                "payload": batch[j]["payload"]
            })
        store(NEW, pts)
        success += len(pts)
        processed += len(pts)
        
        if processed % 50 < BATCH:
            print(f"  Progress: +{success} (total ~{existing + success}/{len(all_points)})", flush=True)
        
        time.sleep(0.5)
    except Exception as e:
        errors += len(valid)
        print(f"  Store error at {i}: {str(e)[:100]}", flush=True)

print(f"\n=== DONE ===")
print(f"New: {success}")
print(f"Errors: {errors}")
print(f"Total in ha-docs-v2: ~{existing + success}")