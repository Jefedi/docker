#!/usr/bin/env python3
"""
ZDR Mistral Countdown - Daily cron job
Decrements zdr/j-N tags in Paperless-ngx for documents sent to Mistral OCR.
When zdr/j-0 is reached, the tag is removed (document no longer on Mistral servers).
"""
import json, urllib.request, sys

TOKEN = "${PAPERLESS_TOKEN}"
BASE = "https://paperless.jefe.al/api"

# Build tag name -> id mapping
req = urllib.request.Request(
    f"{BASE}/tags/?page_size=100",
    headers={"Authorization": f"Token {TOKEN}"}
)
resp = urllib.request.urlopen(req)
tags_data = json.loads(resp.read().decode())
tag_id_by_name = {t["name"]: t["id"] for t in tags_data.get("results", [])}

changes = []
errors = []

# For each zdr/j-N tag from j-31 down to j-1, find docs and decrement
for day in range(31, 0, -1):
    current_tag_name = f"zdr/j-{day}"
    next_tag_name = f"zdr/j-{day - 1}"
    
    current_tag_id = tag_id_by_name.get(current_tag_name)
    next_tag_id = tag_id_by_name.get(next_tag_name)
    
    if not current_tag_id:
        continue
    
    # Search documents with this tag
    req = urllib.request.Request(
        f"{BASE}/documents/?tags__id__in={current_tag_id}&page_size=100",
        headers={"Authorization": f"Token {TOKEN}"}
    )
    resp = urllib.request.urlopen(req)
    docs_data = json.loads(resp.read().decode())
    
    for doc in docs_data.get("results", []):
        doc_id = doc["id"]
        current_tags = doc.get("tags", [])
        
        # Remove current zdr tag, add next one
        new_tags = [t for t in current_tags if t != current_tag_id]
        if next_tag_id:
            new_tags.append(next_tag_id)
        
        # Update document
        payload = json.dumps({"tags": new_tags}).encode()
        req = urllib.request.Request(
            f"{BASE}/documents/{doc_id}/",
            data=payload,
            headers={
                "Authorization": f"Token {TOKEN}",
                "Content-Type": "application/json"
            },
            method="PATCH"
        )
        try:
            urllib.request.urlopen(req)
            changes.append(f"doc {doc_id}: {current_tag_name} -> {next_tag_name}")
        except Exception as e:
            errors.append(f"doc {doc_id}: {e}")

# Handle j-0: remove the tag entirely (document no longer on Mistral servers)
j0_tag_id = tag_id_by_name.get("zdr/j-0")
if j0_tag_id:
    req = urllib.request.Request(
        f"{BASE}/documents/?tags__id__in={j0_tag_id}&page_size=100",
        headers={"Authorization": f"Token {TOKEN}"}
    )
    resp = urllib.request.urlopen(req)
    docs_data = json.loads(resp.read().decode())
    
    for doc in docs_data.get("results", []):
        doc_id = doc["id"]
        current_tags = doc.get("tags", [])
        new_tags = [t for t in current_tags if t != j0_tag_id]
        
        payload = json.dumps({"tags": new_tags}).encode()
        req = urllib.request.Request(
            f"{BASE}/documents/{doc_id}/",
            data=payload,
            headers={
                "Authorization": f"Token {TOKEN}",
                "Content-Type": "application/json"
            },
            method="PATCH"
        )
        try:
            urllib.request.urlopen(req)
            changes.append(f"doc {doc_id}: zdr/j-0 removed (Mistral ZDR expired)")
        except Exception as e:
            errors.append(f"doc {doc_id} j0 removal: {e}")

# Output: only print if there were changes or errors
if changes or errors:
    if changes:
        print(f"ZDR countdown: {len(changes)} documents updated")
        for c in changes[:10]:
            print(f"  {c}")
        if len(changes) > 10:
            print(f"  ... and {len(changes) - 10} more")
    if errors:
        print(f"ERRORS: {len(errors)}")
        for e in errors[:5]:
            print(f"  {e}")
else:
    # Silent on success (no docs to update)
    pass