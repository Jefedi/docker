#!/usr/bin/env python3
"""Re-ingest all docs from ha-docs (384-dim) to ha-docs-v2 (4096-dim) via LiteLLM Qwen3-Embedding-8b"""

import json
import urllib.request
import urllib.error
import time
import sys

QDRANT_URL = "http://localhost:6333"
LITELLM_URL = "https://litelllm.jefe.al/v1/embeddings"
LITELLM_KEY = "sk-JZIHNyIBf7EkeAR4-A2BGw"
OLD_COLLECTION = "ha-docs"
NEW_COLLECTION = "ha-docs-v2"
BATCH_SIZE = 10

def qdrant_scroll(collection, offset=None, limit=100):
    url = f"{QDRANT_URL}/collections/{collection}/points/scroll"
    body = {"limit": limit, "with_payload": True, "with_vector": False}
    if offset:
        body["offset"] = offset
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["result"]

def litellm_embed(texts):
    body = json.dumps({"model": "qwen3-embedding", "input": texts}).encode()
    req = urllib.request.Request(LITELLM_URL, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LITELLM_KEY}"
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return [item["embedding"] for item in data["data"]]

def qdrant_store(collection, points):
    url = f"{QDRANT_URL}/collections/{collection}/points"
    body = json.dumps({"points": points}).encode()
    req = urllib.request.Request(url, data=body, method="PUT", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# Main
print(f"Starting re-ingestion: {OLD_COLLECTION} -> {NEW_COLLECTION}")
print(f"Batch size: {BATCH_SIZE}")

all_points = []
offset = None
total = 0

while True:
    result = qdrant_scroll(OLD_COLLECTION, offset=offset, limit=100)
    points = result.get("points", [])
    if not points:
        break
    all_points.extend(points)
    total += len(points)
    offset = result.get("next_page_offset")
    print(f"  Fetched {total} points...", flush=True)
    if offset is None:
        break

print(f"\nTotal points to re-embed: {len(all_points)}")

success = 0
errors = 0
base_id = int(time.time() * 1000)

for i in range(0, len(all_points), BATCH_SIZE):
    batch = all_points[i:i+BATCH_SIZE]
    texts = [p["payload"].get("content", "") for p in batch]
    
    valid = [(j, t) for j, t in enumerate(texts) if t and len(t.strip()) > 10]
    if not valid:
        continue
    
    valid_texts = [t for _, t in valid]
    
    try:
        embeddings = litellm_embed(valid_texts)
        
        points_to_store = []
        for k, (j, _) in enumerate(valid):
            p = batch[j]
            point_id = base_id + i + j
            points_to_store.append({
                "id": point_id,
                "vector": embeddings[k],
                "payload": p["payload"]
            })
        
        qdrant_store(NEW_COLLECTION, points_to_store)
        success += len(points_to_store)
        
        if (i // BATCH_SIZE) % 10 == 0:
            print(f"  Progress: {success}/{len(all_points)} embedded & stored", flush=True)
        
        time.sleep(0.3)
        
    except Exception as e:
        errors += len(valid)
        print(f"  ERROR at batch {i//BATCH_SIZE}: {str(e)[:200]}", flush=True)
        time.sleep(2)

print(f"\n=== DONE ===")
print(f"Success: {success}")
print(f"Errors: {errors}")