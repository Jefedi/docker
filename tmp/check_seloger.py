import json

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = json.load(f)
seen_ids = set(seen['seen_ids'])

# SeLoger listings from Centre-ville that are T2+, <=500€, >=28m²
seloger_listings = [
    {"id": "seloger-276338655", "price": 505, "rooms": 2, "surface": 32.5, "url": "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/276338655.htm"},
    {"id": "seloger-266005573", "price": 500, "rooms": 4, "surface": 83, "url": "https://www.seloger.com/annonces/locations/appartement/le-havre-76/centre-ville/266005573.htm"},
]

# Filter: price <= 500, rooms >= 2, surface >= 28
candidates = []
for l in seloger_listings:
    if l['id'] in seen_ids:
        status = "SEEN"
    else:
        status = "NEW"
    if l['price'] <= 500 and l['rooms'] >= 2 and l['surface'] >= 28:
        print(f"{l['id']}: {status} - {l['price']}€ {l['rooms']}p {l['surface']}m²")
        if status == "NEW":
            candidates.append(l)

print(f"\nNew candidates: {len(candidates)}")
for c in candidates:
    print(f"  {c['id']}: {c['url']}")