import json
import re

with open('/tmp/hermes-results/call_kx8lrzhr.txt') as f:
    data = json.load(f)

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

# LBC check
lbc_content = data['results'][0]['content']
all_lbc_ids = re.findall(r'leboncoin\.fr/ad/locations/(\d+)', lbc_content)
unique_lbc = list(dict.fromkeys(all_lbc_ids))
new_lbc = [x for x in unique_lbc if x not in seen_ids and f"lbc-{x}" not in seen_ids]
print(f"LBC: {len(unique_lbc)} total, {len(new_lbc)} new")
if new_lbc:
    print("  New LBC:", new_lbc)

# SeLoger check for each quartier
for idx, name in [(1, 'Centre-ville'), (2, 'Sanvic'), (3, 'Bléville')]:
    content = data['results'][idx]['content']
    # Extract all listing IDs from URLs like /annonces/locations/appartement/le-havre-76/<quartier>/<ID>.htm
    sl_ids = re.findall(r'seloger\.com/annonces/locations/appartement/le-havre-76/\S+?/(\w+)\.htm', content)
    unique_sl = list(dict.fromkeys(sl_ids))
    new_sl = [x for x in unique_sl if x not in seen_ids and f"seloger-{x}" not in seen_ids]
    print(f"SeLoger {name}: {len(unique_sl)} total, {len(new_sl)} new")
    if new_sl:
        print("  New SeLoger:", new_sl)
        # Print details for new ones
        for nid in new_sl:
            # Find the context around this ID in the content
            pos = content.find(nid)
            if pos >= 0:
                context = content[max(0,pos-300):pos+500]
                print(f"  Context for {nid}:")
                print(context[:600])
                print()

total_new = len(new_lbc) + sum(
    len([x for x in list(dict.fromkeys(
        re.findall(r'seloger\.com/annonces/locations/appartement/le-havre-76/\S+?/(\w+)\.htm', 
                   data['results'][idx]['content'])
    )) if x not in seen_ids and f"seloger-{x}" not in seen_ids])
    for idx in [1,2,3]
)
print(f"\nTOTAL NEW: {total_new}")