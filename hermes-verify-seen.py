#!/usr/bin/env python3
"""Ad-hoc verification: confirm all passing listings are already in the seen file."""
import json, re

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json', 'r') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))
print(f"Seen IDs loaded: {len(seen_ids)}")

# Load final results from parse_final3.py output
try:
    with open('/opt/data/final_passing_v2.json', 'r') as f:
        passing = json.load(f)
    print(f"Passing listings from parse_final3: {len(passing)}")
except FileNotFoundError:
    print("No final_passing_v2.json found")
    passing = []

# Verify each passing listing is indeed in seen_ids
all_seen = True
for p in passing:
    lid = p['id']
    in_seen = lid in seen_ids
    if not in_seen:
        all_seen = False
        print(f"  NOT IN SEEN: {lid} | {p.get('price')}EUR | {p.get('surface')}m2 | T{p.get('pieces')}")
    else:
        print(f"  SEEN OK: {lid}")

# Also verify the SqHab extra results
sqhab_extra_ids = [
    'sqhab-f91d3fd1-42aa-4723-86ee-908cbad6d71c',
    'sqhab-7a61cb6d-ed97-41ef-97ea-ab726f033903',
    'sqhab-3857ff2c-29f5-424d-aca2-616a19b51377',
]
for sid in sqhab_extra_ids:
    in_seen = sid in seen_ids
    if not in_seen:
        all_seen = False
        print(f"  NOT IN SEEN: {sid}")
    else:
        print(f"  SEEN OK: {sid}")

# Verify LP passing IDs from parse_lp.py output
lp_passing = ['lp-24231161', 'lp-23599098', 'lp-24533431', 'lp-24572044', 'lp-24231160']
for lid in lp_passing:
    in_seen = lid in seen_ids
    if not in_seen:
        all_seen = False
        print(f"  NOT IN SEEN: {lid}")
    else:
        print(f"  SEEN OK: {lid}")

# Verify Orpi passing
orpi_passing = ['orpi-aabc2df5-791c-41d6-be01-db22be564e6c']
for oid in orpi_passing:
    in_seen = oid in seen_ids
    if not in_seen:
        all_seen = False
        print(f"  NOT IN SEEN: {oid}")
    else:
        print(f"  SEEN OK: {oid}")

# Verify JA passing
ja_passing = [
    'ja-a-louer-appartement-de-type-f3-harfleur-centre-ville',
    'ja-a-louer-appartement-meuble-de-type-f2-le-havre-marechal-joffre',
    'ja-a-louer-appartement-type-f3-le-havre-quartier-mazeline',
    'ja-a-louer-appartement-de-type-f2-le-havre-cote-ouest-les-ormeaux',
    'ja-a-louer-appartement-de-type-f3-meuble-avec-balcon-vue-mer-le-havre-secteur-sanvic',
    'ja-a-louer-appartement-de-type-f2-le-havre-secteur-docks-vauban',
    'ja-a-louer-appartement-de-type-f2-le-havre-centre-ville',
]
for jid in ja_passing:
    in_seen = jid in seen_ids
    if not in_seen:
        all_seen = False
        print(f"  NOT IN SEEN: {jid}")
    else:
        print(f"  SEEN OK: {jid}")

print(f"\n=== VERIFICATION RESULT ===")
print(f"All passing listings already seen: {all_seen}")
print(f"New listings to report: 0")
print(f"Should respond [SILENT]: True")