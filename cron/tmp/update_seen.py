#!/usr/bin/env python3
"""Update seen file with new IDs found during this scan."""
import json

with open('/opt/data/cron/output/havre-rental-seen.json', 'r') as f:
    seen_data = json.load(f)

seen_ids = set(seen_data['seen_ids'])
new_ids = [
    'sqhab-8a7d0d7c-b4d5-4f98-aefa-e1b417fbab14',
    'sqhab-f76a1651-f832-492c-8266-5fe1c7b39678',
]

added = 0
for nid in new_ids:
    if nid not in seen_ids:
        seen_ids.add(nid)
        seen_data['seen_ids'].append(nid)
        added += 1
        print(f"Added: {nid}")

seen_data['last_updated'] = '2026-08-05T12:00'
seen_data['total_seen'] = len(seen_data['seen_ids'])

with open('/opt/data/cron/output/havre-rental-seen.json', 'w') as f:
    json.dump(seen_data, f, indent=2)

print(f"\nTotal added: {added}")
print(f"Total seen: {len(seen_data['seen_ids'])}")