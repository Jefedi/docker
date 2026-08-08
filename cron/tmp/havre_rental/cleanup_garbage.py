#!/usr/bin/env python3
"""Clean up garbage IDs from the seen file and qualified listings."""
import json

SEEN_FILE = "/opt/data/cron/output/havre-rental-seen.json"
QUAL_FILE = "/opt/data/cron/tmp/havre_rental/qualified_listings.json"

# IDs to remove (non-listing pages: WordPress system files, C21 with no data)
GARBAGE_PATTERNS = ['xmlrpc', 'feed/', 'comments/', 'blog/', 'honoraires',
                    'dossier-locataire', 'mandataire', 'investir',
                    'annonces/page/', 'annonces/']

# Load seen
with open(SEEN_FILE, 'r') as f:
    seen_data = json.load(f)

original_count = len(seen_data['seen_ids'])

# Remove garbage IDs from seen
cleaned_ids = []
removed = []
for sid in seen_data['seen_ids']:
    is_garbage = any(p in sid for p in GARBAGE_PATTERNS)
    # Also remove empty C21 listings (no actual data — SVG noise)
    if sid.startswith('c21-') and sid not in ['c21-7371', 'c21-15443', 'c21-7201', 'c21-15596', 'c21-15772891843']:
        # Keep only previously-seen C21 IDs, remove new empty ones
        is_garbage = True
    
    if is_garbage:
        removed.append(sid)
    else:
        cleaned_ids.append(sid)

seen_data['seen_ids'] = cleaned_ids
seen_data['total_seen'] = len(cleaned_ids)

with open(SEEN_FILE, 'w') as f:
    json.dump(seen_data, f, indent=2, ensure_ascii=False)

print(f"Seen file: {original_count} -> {len(cleaned_ids)} (removed {len(removed)} garbage)")
print("Removed IDs:")
for r in removed:
    print(f"  {r}")

# Also clean qualified listings
with open(QUAL_FILE, 'r') as f:
    qualified = json.load(f)

clean_qualified = []
removed_qual = []
for q in qualified:
    qid = q['id']
    is_garbage = any(p in qid for p in GARBAGE_PATTERNS)
    # Remove C21 entries with no data
    if q['source'] == 'c21' and not q.get('price') and not q.get('surface') and not q.get('rooms'):
        is_garbage = True
    
    if is_garbage:
        removed_qual.append(qid)
    else:
        clean_qualified.append(q)

with open(QUAL_FILE, 'w') as f:
    json.dump(clean_qualified, f, indent=2, ensure_ascii=False)

print(f"\nQualified: {len(qualified)} -> {len(clean_qualified)} (removed {len(removed_qual)} garbage)")
print("Removed qualified IDs:")
for r in removed_qual:
    print(f"  {r}")