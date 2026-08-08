#!/usr/bin/env python3
"""Parse web_extract results for Le Havre rental listings."""
import json
import re
import os

RESULTS_FILE = "/tmp/hermes-results/call_e1d8hgzk.txt"
SEEN_FILE = "/opt/data/cron/output/havre-rental-seen.json"

# Load seen IDs
seen_ids = set()
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE) as f:
        data = json.load(f)
        seen_ids = set(data.get("seen_ids", []))

print(f"=== Seen IDs loaded: {len(seen_ids)} ===")

# Load web_extract results
with open(RESULTS_FILE) as f:
    raw = f.read()

results_data = json.loads(raw)
results = results_data["results"]

all_listings = []

# ---- Parse Leboncoin ----
lbc_content = ""
for r in results:
    if "leboncoin.fr" in r["url"]:
        lbc_content = r["content"]
        break

print(f"\n=== LEBONCOIN content length: {len(lbc_content)} ===")

# Extract all ad positions and IDs
ad_positions = [(m.start(), m.group(1)) for m in re.finditer(r'leboncoin\.fr/ad/locations/(\d+)', lbc_content)]
print(f"Ad positions found: {len(ad_positions)}")

for i, (pos, ad_id) in enumerate(ad_positions):
    start = pos
    end = ad_positions[i+1][0] if i+1 < len(ad_positions) else len(lbc_content)
    block = lbc_content[start:end]
    
    # Extract price
    price_match = re.search(r'(\d+)\s*€', block)
    price = int(price_match.group(1)) if price_match else None
    
    # Extract rooms/surface: "Appartement · 2 pièces · 31m²"
    type_match = re.search(r'Appartement\s*·\s*(\d+)\s*pi[èe]ces?\s*·\s*([\d,]+)\s*m[²2]', block)
    rooms = int(type_match.group(1)) if type_match else None
    surface = type_match.group(2).replace(',', '.') if type_match else None
    
    # Extract location: "Le Havre 76600 XXXX" or "Située à Le Havre 76600 XXXX"
    loc_match = re.search(r'Le Havre\s*766\d\d\s+([^\n\\]+?)(?:\\n|Situ|aujourd|Date|Pro|Particulier|Voir)', block)
    location = loc_match.group(1).strip() if loc_match else None
    
    cp_match = re.search(r'766(00|20)', block)
    cp = "766" + cp_match.group(1) if cp_match else "76600"
    
    listing = {
        "source": "leboncoin",
        "id": f"lbc-{ad_id}",
        "url": f"https://www.leboncoin.fr/ad/locations/{ad_id}",
        "price": price,
        "rooms": rooms,
        "surface": surface,
        "location": location,
        "cp": cp,
    }
    all_listings.append(listing)

print(f"\nLeboncoin parsed: {len(all_listings)}")
for l in all_listings:
    print(f"  {l['id']} | {l['price']}€ | {l['rooms']}p | {l['surface']}m² | loc={l['location']} | cp={l['cp']}")

# ---- Parse SeLoger ----
for r in results:
    if "seloger.com" not in r["url"]:
        continue
    
    url = r["url"]
    content = r["content"]
    
    if "centre-ville" in url:
        quartier = "Centre-ville"
    elif "sanvic" in url:
        quartier = "Sanvic"
    elif "bleville" in url:
        quartier = "Bléville"
    else:
        continue
    
    print(f"\n=== SELOGER {quartier} length: {len(content)} ===")
    
    # Find listing links: [Title](URL.htm...)
    # Title format: "Appartement à louer - Le Havre - 420 € - 2 pièces, 1 chambre, 22 m², RDC/2"
    pattern = r'\[([^\]]+)\]\((https://www\.seloger\.com/annonces/locations/appartement/le-havre-76/[^\)]+?\.htm)'
    matches = re.findall(pattern, content)
    
    print(f"  Links found: {len(matches)}")
    
    seen_urls = set()
    for title, listing_url in matches:
        if listing_url in seen_urls:
            continue
        seen_urls.add(listing_url)
        
        price_match = re.search(r'(\d+)\s*€', title)
        price = int(price_match.group(1)) if price_match else None
        
        rooms_match = re.search(r'(\d+)\s*pi[èe]ce', title)
        rooms = int(rooms_match.group(1)) if rooms_match else None
        
        surface_match = re.search(r'([\d,]+)\s*m[²2]', title)
        surface = surface_match.group(1).replace(',', '.') if surface_match else None
        
        # Extract ID from URL
        lid_match = re.search(r'/([A-Z0-9]{12}|\d{6,})\.htm', listing_url)
        lid = lid_match.group(1) if lid_match else None
        
        listing = {
            "source": "seloger",
            "id": f"seloger-{lid}" if lid else None,
            "url": listing_url,
            "price": price,
            "rooms": rooms,
            "surface": surface,
            "location": quartier,
            "cp": "76620" if quartier in ("Sanvic", "Bléville") else "76600",
            "title": title[:100],
        }
        all_listings.append(listing)
        print(f"  -> id={listing['id']} | {price}€ | {rooms}p | {surface}m² | {quartier}")

# ---- FILTER ----
print("\n\n========== FILTERING ==========")
print("Criteria: T2+ (rooms>=2), price<=500, quartier in [Centre-ville, Bléville, Sanvic]\n")

ACCEPTED_QUARTIERS = {"centre-ville", "bleville", "sanvic"}

def normalize_quartier(q):
    if not q:
        return ""
    return q.lower().strip().replace("-", "").replace(" ", "").replace("é", "e")

# For leboncoin: search is 76600 which covers Centre-ville + other quartiers
# Bléville/Sanvic are 76620 - not in leboncoin search
# We accept 76600 listings as Centre-ville (leboncoin search covers the city center area)
# But we should exclude known non-centre-ville neighborhoods if identifiable

# Non-centre-ville 76600 areas: Dollemard, Sainte-Adresse (different town), Caux, 
# Graville, Soquence, Rouelles, Caucriauville, Mare-aux-Clercs, etc.
# Actually many of these are 76600 too. Let's be inclusive for 76600 since the 
# leboncoin search specifically targets 76600.

NON_CENTRE_VILLE_76600 = [
    "caucriauville", "dollemard", "dolle", "graville", "rouelles",
    "soquence", "mare", "clercs", "bléville", "bleville", "sanvic",
    "la plage", "aigle", "océane", "ocean", "havre de grâce",
    "sainte-adresse", "fontaine", "mont-gaillard", "gaillard",
    "côte", "cote", "orée", "oree", "forêt", "foret",
    "vallée", "vallee", "bois", "chapelle", "valleux",
]

def is_accepted_quartier(listing):
    loc = (listing.get("location") or "").lower()
    cp = listing.get("cp", "")
    source = listing.get("source", "")
    
    if source == "seloger":
        q = normalize_quartier(listing.get("location", ""))
        return q in ACCEPTED_QUARTIERS
    
    # Leboncoin: check location
    loc_norm = normalize_quartier(loc)
    
    # Check for explicit accepted quartiers
    if "bleville" in loc_norm:
        return True
    if "sanvic" in loc_norm:
        return True
    
    # Check for non-centre-ville areas (exclude)
    for area in NON_CENTRE_VILLE_76600:
        if area in loc_norm:
            return False
    
    # Default: 76600 = accept as centre-ville
    if cp == "76600":
        return True
    
    return False

filtered = []
for l in all_listings:
    if l.get("id") is None:
        print(f"  SKIP (no ID): price={l['price']} rooms={l['rooms']}")
        continue
    if l["rooms"] is None or l["price"] is None:
        print(f"  SKIP (missing data): {l['id']} | price={l['price']} rooms={l['rooms']}")
        continue
    if l["rooms"] < 2:
        print(f"  SKIP (T1/studio): {l['id']} | {l['rooms']}p | {l['price']}€")
        continue
    if l["price"] > 500:
        print(f"  SKIP (price>500): {l['id']} | {l['price']}€")
        continue
    if not is_accepted_quartier(l):
        print(f"  SKIP (quartier): {l['id']} | loc={l.get('location')} | cp={l.get('cp')}")
        continue
    
    l["is_new"] = l["id"] not in seen_ids
    filtered.append(l)
    status = "🆕 NEW" if l["is_new"] else "SEEN"
    print(f"  ✅ KEEP [{status}]: {l['id']} | {l['price']}€ | {l['rooms']}p | {l['surface']}m² | {l.get('location', '?')}")

# Sort by price ascending
filtered.sort(key=lambda x: (x["price"], x["rooms"]))

new_listings = [l for l in filtered if l["is_new"]]

print(f"\n========== SUMMARY ==========")
print(f"Total parsed: {len(all_listings)}")
print(f"Filtered (T2+, <=500€, accepted quartiers): {len(filtered)}")
print(f"NEW: {len(new_listings)}")
print(f"Already seen: {len(filtered) - len(new_listings)}")

# Output
output = {
    "all_filtered": filtered,
    "new_listings": new_listings,
    "all_ids_this_run": [l["id"] for l in all_listings if l.get("id")]
}
with open("/opt/data/cron/tmp/parsed_rentals.json", "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\nSaved to /opt/data/cron/tmp/parsed_rentals.json")