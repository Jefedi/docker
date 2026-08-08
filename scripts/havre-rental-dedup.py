#!/usr/bin/env python3
"""Store seen rental listing IDs for dedup across cron runs."""
import json, os, sys

SEEN_FILE = "/opt/data/cron/output/havre-rental-seen.json"

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(ids):
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(list(ids), f)

if __name__ == "__main__":
    # Read new IDs from stdin (one per line), merge with seen, save
    new_ids = [line.strip() for line in sys.stdin if line.strip()]
    seen = load_seen()
    all_ids = seen | set(new_ids)
    save_seen(all_ids)
    # Output only truly new IDs
    truly_new = [id for id in new_ids if id not in seen]
    for id in truly_new:
        print(id)