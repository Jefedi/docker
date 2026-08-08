import re, json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = json.load(f)
seen_ids = set(seen['seen_ids'])

# Collect all IDs from this run that aren't already in seen
new_ids_to_add = []

# Orpi UUIDs from all pages
orpi_files = ['/tmp/veille/orpi.html', '/tmp/veille/orpi_cv.html', '/tmp/veille/orpi_coty.html',
              '/tmp/veille/orpi_mass.html', '/tmp/veille/orpi_ff.html', '/tmp/veille/orpi_eure.html',
              '/tmp/veille/orpi_sf.html', '/tmp/veille/orpi_p2.html']
for fn in orpi_files:
    try:
        with open(fn, encoding='utf-8', errors='replace') as f:
            raw = f.read()
        uuids = re.findall(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', raw)
        for u in uuids:
            lid = f'orpi-{u}'
            if lid not in seen_ids:
                new_ids_to_add.append(lid)
    except:
        pass

# SquareHabitat UUIDs
for fn in ['/tmp/veille/sqhab.html', '/tmp/veille/sqhab_p2.html']:
    try:
        with open(fn, encoding='utf-8', errors='replace') as f:
            raw = f.read()
        # Get listing-specific UUIDs (from listing URLs)
        listing_uuids = re.findall(r'/square-habitat-normandie-seine/annonces/biens/location/appartement/le-havre/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', raw)
        for u in listing_uuids:
            lid = f'sqhab-{u}'
            if lid not in seen_ids:
                new_ids_to_add.append(lid)
    except:
        pass

# Citya GES IDs
for fn in ['/tmp/veille/citya.html', '/tmp/veille/citya_p2.html', '/tmp/veille/citya_p3.html']:
    try:
        with open(fn, encoding='utf-8', errors='replace') as f:
            raw = f.read()
        ges_ids = re.findall(r'(GES\d+-\d+)', raw)
        for g in ges_ids:
            lid = f'citya-{g}'
            if lid not in seen_ids:
                new_ids_to_add.append(lid)
    except:
        pass

# C21 refs
try:
    with open('/tmp/veille/c21_list.html', encoding='utf-8', errors='replace') as f:
        raw = f.read()
    c21_refs = re.findall(r'Ref\s*:\s*(\d+)', raw)
    for r in c21_refs:
        lid = f'c21-{r}'
        if lid not in seen_ids:
            new_ids_to_add.append(lid)
except:
    pass

# Deduplicate
new_ids_to_add = list(dict.fromkeys(new_ids_to_add))
print(f"New IDs to add to seen: {len(new_ids_to_add)}")
for nid in new_ids_to_add[:20]:
    print(f"  {nid}")

# Update seen file
seen['seen_ids'].extend(new_ids_to_add)
with open('/opt/data/cron/output/havre-rental-seen.json', 'w') as f:
    json.dump(seen, f, indent=2)
print(f"\nUpdated seen file: {len(seen['seen_ids'])} total IDs")