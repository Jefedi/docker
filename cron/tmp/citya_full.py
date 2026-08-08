import re, json, html

# Citya: parse the property-card divs with data-itemId, data-itemName, data-price
s = open('/tmp/src_7d2dca6d.html').read()
# Also fetch page 2 and 3
import subprocess
# Find all property-card divs
cards = re.findall(r'data-itemId="([^"]+)"\s+data-itemName="([^"]+)"\s+data-category="[^"]*"\s+data-price="(\d+)"', s)
print(f"Citya cards: {len(cards)}")
for cid, name, price in cards:
    print(f"  {cid} | {price}€ | {name}")

# Fetch pages 2 and 3
import os
os.system('curl -s -A "Mozilla/5.0" -m 25 "https://www.citya.com/annonces/location/appartement/le-havre-76351?page=2" -o /tmp/citya2.html')
os.system('curl -s -A "Mozilla/5.0" -m 25 "https://www.citya.com/annonces/location/appartement/le-havre-76351?page=3" -o /tmp/citya3.html')

for fname in ['/tmp/citya2.html', '/tmp/citya3.html']:
    try:
        s2 = open(fname).read()
        cards2 = re.findall(r'data-itemId="([^"]+)"\s+data-itemName="([^"]+)"\s+data-category="[^"]*"\s+data-price="(\d+)"', s2)
        print(f"\n{fname}: {len(cards2)} cards")
        for cid, name, price in cards2:
            print(f"  {cid} | {price}€ | {name}")
    except:
        print(f"{fname}: not found")

# Now filter: T2+ (2 pieces+), <=500€
print("\n=== Citya candidates (T2+, <=500€) ===")
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = set(json.load(f)['seen_ids'])

all_cards = cards
for fname in ['/tmp/citya2.html', '/tmp/citya3.html']:
    try:
        s2 = open(fname).read()
        all_cards += re.findall(r'data-itemId="([^"]+)"\s+data-itemName="([^"]+)"\s+data-category="[^"]*"\s+data-price="(\d+)"', s2)
    except: pass

for cid, name, price in all_cards:
    try: pr = int(price)
    except: continue
    # Check pieces from name
    pmatch = re.search(r'(\d+)\s*pi[èc]', name)
    pc = int(pmatch.group(1)) if pmatch else 0
    # Check surface
    smatch = re.search(r'(\d+(?:\.\d+)?)\s*m', name)
    surf = float(smatch.group(1)) if smatch else 0
    if pc >= 2 and pr <= 500 and surf >= 28:
        seen_id = f"citya-{cid}"
        status = "NEW" if seen_id not in seen else "SEEN"
        print(f"  {status}: {seen_id} | {pr}€ | {pc}p | {surf}m² | {name}")