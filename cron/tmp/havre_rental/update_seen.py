#!/usr/bin/env python3
"""Update the seen file with all new listing IDs from this run."""
import json
import os
from datetime import datetime

SEEN_FILE = "/opt/data/cron/output/havre-rental-seen.json"

# Load current seen file
with open(SEEN_FILE, 'r') as f:
    seen_data = json.load(f)

seen_ids = set(seen_data.get('seen_ids', []))
original_count = len(seen_ids)

# Load all listings from this run
with open('/opt/data/cron/tmp/havre_rental/all_listings_v3.json', 'r') as f:
    all_listings = json.load(f)

# Also add LP page 2 listings
import re
from html import unescape

def strip_tags(html_str):
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = text.replace('&nbsp;', ' ')
    text = re.sub(r'\s+', ' ', text)
    return unescape(text).strip()

with open('/opt/data/cron/tmp/havre_rental/lp_page2.html', 'r', errors='replace') as f:
    html = f.read()

h2_iter = [(m.start(), m.group(1)) for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)]
for h2_pos, h2_content in h2_iter:
    all_links = re.finditer(r'href="(/immobilier/location/appartement/[^"]*?/(\d+))"', html[h2_pos:h2_pos+5000])
    for m in all_links:
        listing_id = f"lp-{m.group(2)}"
        all_listings.append({'id': listing_id})

# Add all new listing IDs to seen
new_ids = []
for listing in all_listings:
    lid = listing['id']
    # Skip obviously non-listing entries
    if any(x in lid for x in ['xmlrpc', 'feed/', 'comments/', 'blog/', 'honoraires', 
                                'dossier-locataire', 'mandataire', 'investir', 
                                'annonces/page/', 'annonces/']):
        continue
    if lid not in seen_ids:
        seen_ids.add(lid)
        new_ids.append(lid)

# Update the seen data
seen_data['seen_ids'] = list(seen_ids)
seen_data['last_updated'] = datetime.now().strftime('%Y-%m-%dT%H:%M')
seen_data['total_seen'] = len(seen_ids)

# Save
with open(SEEN_FILE, 'w') as f:
    json.dump(seen_data, f, indent=2, ensure_ascii=False)

print(f"Original seen: {original_count}")
print(f"New IDs added: {len(new_ids)}")
print(f"Total seen: {len(seen_ids)}")
print(f"\nNew IDs:")
for nid in new_ids:
    print(f"  {nid}")