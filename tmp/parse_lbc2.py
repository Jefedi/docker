import json, re

# Parse Leboncoin ad IDs from the raw output
raw = open('/tmp/lbc_ads.json').read()

# Extract all unique ad IDs
ids = re.findall(r'/ad/locations/(\d+)', raw)
unique_ids = []
seen = set()
for id in ids:
    if id not in seen:
        seen.add(id)
        unique_ids.append(id)

# Load seen file
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data['seen_ids'])

# Check which are new
new_ids = []
for id in unique_ids:
    lbc_id = f"lbc-{id}"
    if lbc_id not in seen_ids and id not in seen_ids:
        new_ids.append(id)

print(f"Total unique ad IDs: {len(unique_ids)}")
print(f"New (not seen): {len(new_ids)}")
for id in new_ids:
    print(f"  lbc-{id}: https://www.leboncoin.fr/ad/locations/{id}")