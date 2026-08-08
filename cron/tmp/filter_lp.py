#!/usr/bin/env python3
"""Filter LP listings by criteria and check against seen file."""
import json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

with open('/opt/data/cron/tmp/lp_listings.json') as f:
    listings = json.load(f)

# The LP search is for locations with loyer-max=500&pieces=2
# But it returns listings above 500 (the filter is not strict, like the sales filter)
# Filter: price <= 500, pieces >= 2, surface >= 28

new_candidates = []
already_seen = []
rejected = []

for l in listings:
    id_ = l['id']
    prix = l['prix']
    pieces = l['pieces']
    surf = l['surf']
    
    if id_ in seen_ids:
        already_seen.append(l)
        continue
    
    reasons = []
    if prix > 500:
        reasons.append(f"prix {prix}>500")
    if surf < 28:
        reasons.append(f"surface {surf}<28")
    if pieces < 2:
        reasons.append(f"pièces {pieces}<2")
    
    if reasons:
        rejected.append((l, reasons))
    else:
        new_candidates.append(l)

print(f"LP TOTAL: {len(listings)} | SEEN: {len(already_seen)} | REJECTED: {len(rejected)} | NEW: {len(new_candidates)}")
print()
for l in new_candidates:
    print(f"NEW: {l['id']} | {l['prix']}€ | {l['pieces']}p | {l['surf']}m²")
    print(f"  URL: {l['url']}")
print()
print("=== REJECTED (new, not matching) ===")
for l, reasons in rejected:
    print(f"  {l['id']} | {l['prix']}€ | {l['pieces']}p | {l['surf']}m² -> {', '.join(reasons)}")