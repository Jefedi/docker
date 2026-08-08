#!/usr/bin/env python3
"""Ad-hoc verification: re-run the core filter+dedup logic against cached scraping data
and confirm the [SILENT] conclusion (no new qualifying listings) is correct."""
import json, re, sys

CACHE = "/opt/data/cache/web/www.leboncoin.fr-6dab532d68.md"
RESULTS = "/tmp/hermes-results/call_lfk1h454.txt"
SEEN = "/opt/data/cron/output/havre-rental-seen.json"

SUBQ_MAP = {
    "Coty": "Centre-ville", "Massillon": "Centre-ville", "Eure": "Centre-ville",
    "Danton": "Centre-ville", "Saint-François": "Centre-ville",
    "Centre-ville": "Centre-ville", "Bléville": "Bléville", "Sanvic": "Sanvic",
}
ACCEPTED = {"Centre-ville", "Bléville", "Sanvic"}

with open(SEEN) as f:
    seen_ids = set(json.load(f)["seen_ids"])

# --- Leboncoin ---
with open(CACHE) as f:
    lbc_lines = f.read().split("\n")
ad_urls = []
for i, line in enumerate(lbc_lines):
    m = re.search(r"Voir l.annonce\]\((https://www\.leboncoin\.fr/ad/locations/(\d+))\)", line)
    if m:
        ad_urls.append((i, m.group(1), m.group(2)))
lbc_listings = []
for idx, (ln, url, ad_id) in enumerate(ad_urls):
    start = ad_urls[idx - 1][0] + 1 if idx > 0 else 0
    block = "\n".join(lbc_lines[start : ln + 1])
    price_m = re.search(r"(\d+)\s*€", block)
    price = int(price_m.group(1)) if price_m else 0
    type_m = re.search(r"Appartement\s*·\s*(\d+)\s*pi[èe]ces?\s*·\s*(\d+)m[²2]", block)
    rooms = int(type_m.group(1)) if type_m else 0
    surface = int(type_m.group(2)) if type_m else 0
    loc_m = re.search(r"Le Havre\s*\d+\s+(.+?)(?:\n|$)", block)
    location = loc_m.group(1).strip() if loc_m else "?"
    quartier = SUBQ_MAP.get(location, location)
    lbc_listings.append({"source":"lbc","ad_id":ad_id,"url":url,"price":price,
        "rooms":rooms,"surface":surface,"location":location,"quartier":quartier})

# --- SeLoger ---
with open(RESULTS) as f:
    data = json.load(f)
seloger_listings = []
for src_idx, quartier_label in [(1,"Centre-ville"),(2,"Sanvic"),(3,"Bléville")]:
    content = data["results"][src_idx]["content"]
    listings = re.findall(r"\[([^\]]+à louer[^\]]*)\]\((https://www\.seloger\.com/annonces/locations/[^)]+)\)", content)
    for title, url in listings:
        price_m = re.search(r"(\d[\d\s]*)\s*€", title)
        _p = price_m.group(1).replace("\xa0","").replace(" ","").replace("\u202f","").replace("\u2009","")
        price = int(_p) if price_m else 0
        pieces_m = re.search(r"(\d+)\s*pi[èe]ce", title)
        pieces = int(pieces_m.group(1)) if pieces_m else 0
        surface_m = re.search(r"([\d,]+)\s*m[²2]", title)
        surface = float(surface_m.group(1).replace(",",".")) if surface_m else 0
        id_m = re.search(r"/([A-Za-z0-9]+)\.htm", url)
        seloger_id = id_m.group(1) if id_m else url.split("#")[0].split("/")[-1]
        seloger_listings.append({"source":"seloger","ad_id":seloger_id,"url":url.split("#")[0],
            "price":price,"rooms":pieces,"surface":surface,"quartier":quartier_label})

# --- Filters ---
all_listings = lbc_listings + seloger_listings
qualifying = [l for l in all_listings if l["price"]>0 and l["price"]<=500 and l["rooms"]>=2
    and l["surface"]>=28 and l["quartier"] in ACCEPTED]

new_listings = [l for l in qualifying
    if not any(k in seen_ids for k in [l["ad_id"], f"lbc-{l['ad_id']}", f"seloger-{l['ad_id']}"])]

print("=== AD-HOC VERIFICATION ===")
print(f"Leboncoin parsed: {len(lbc_listings)} | SeLoger parsed: {len(seloger_listings)}")
print(f"Qualifying (T2+, ≤500€, ≥28m², accepted quartier): {len(qualifying)}")
print(f"New (not in seen): {len(new_listings)}")
print()
for l in sorted(qualifying, key=lambda x: x["price"]):
    seen = "SEEN" if any(k in seen_ids for k in [l["ad_id"],f"lbc-{l['ad_id']}",f"seloger-{l['ad_id']}"]) else "NEW"
    print(f"  [{seen:4s}] {l['source']:7s} {l['price']:3d}€ {l['rooms']}p {l['surface']:5.1f}m² {l['quartier']:12s} id={l['ad_id']}")
print()
if new_listings:
    print(f"FAIL: {len(new_listings)} NEW listing(s) — [SILENT] was wrong")
    sys.exit(1)
else:
    print("PASS: All qualifying listings already seen — [SILENT] is correct")
    sys.exit(0)