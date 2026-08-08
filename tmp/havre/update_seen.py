#!/usr/bin/env python3
"""Update the seen IDs file with new listing IDs."""
import json

SEEN_FILE = "/opt/data/cron/output/havre-rental-seen.json"

with open(SEEN_FILE) as f:
    seen_data = json.load(f)

new_ids = [
    "sqhab-547b5cfc-571a-48ae-9739-d19a72f2ec94",
    "sqhab-0e25b2fa-1cc0-4150-8c9b-66d83ac87c47",  # Below 28m² but track it
]

added = 0
for nid in new_ids:
    if nid not in seen_data["seen_ids"]:
        seen_data["seen_ids"].append(nid)
        added += 1

seen_data["last_updated"] = "2026-08-06T05:30"
seen_data["total_seen"] = len(seen_data["seen_ids"])

with open(SEEN_FILE, "w") as f:
    json.dump(seen_data, f, indent=2, ensure_ascii=False)

print(f"Added {added} new IDs. Total seen: {seen_data['total_seen']}")