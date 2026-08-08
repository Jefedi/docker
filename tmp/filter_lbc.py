import json, re

# Load seen IDs
with open("/opt/data/cron/output/havre-rental-seen.json") as f:
    seen_data = json.load(f)
seen_ids = set(seen_data["seen_ids"])

# Load leboncoin articles
with open("/opt/data/tmp/lbc_all_articles.json") as f:
    articles = json.load(f)

# Accepted quartiers (with sub-quartier mapping)
# Centre-ville: Coty, Massillon, Eure, Félix Faure, Perret, Docks, Rond-point Observatoire, Saint-François, Danton
accepted_quartiers = {
    "centre-ville", "coty", "massillon", "eure", "felix faure", "perret",
    "docks", "rond point - observatoire", "saint-françois - les docks",
    "saint-francois - les docks", "danton", "rond-point observatoire",
    "sanvic", "bleville",
    "saint-roch",  # close to centre, often associated
}

# Also accept without the restrictive mapping - the user said:
# Centre-ville (Coty, Massillon, Eure, Félix Faure, Perret, Docks, Rond-point Observatoire, Saint-François, Danton), Sanvic, Bléville
accepted_subquartiers = {
    "coty", "massillon", "eure", "felix faure", "perret",
    "docks", "rond point - observatoire", "saint-françois - les docks",
    "saint-francois - les docks", "danton",
    "centre-ville", "sanvic", "bleville",
}

# Also note: some listings show "Saint-Roch" which is the quartier around Saint Roch church —
# close to centre. Let me include it since Saint Roch Immobilier is listed.
# Actually the user's list doesn't include Saint-Roch. Let me be strict.

# Actually let me re-read the criteria:
# Quartiers acceptés: Centre-ville (Coty, Massillon, Eure, Félix Faure, Perret, Docks, 
#   Rond-point Observatoire, Saint-François, Danton), Sanvic, Bléville
# So only these. Saint-Roch, Sainte-Anne, Université, Graville, Les Ormeaux are NOT accepted.

def parse_article(text, ad_id):
    """Parse a leboncoin article text into structured data"""
    # Price
    price_match = re.search(r'(\d+)\s*€', text)
    price = int(price_match.group(1)) if price_match else None
    
    # Surface
    surface_match = re.search(r'(\d+)\s*m²', text)
    surface = int(surface_match.group(1)) if surface_match else None
    
    # Rooms
    rooms_match = re.search(r'(\d+)\s*pièces', text)
    rooms = int(rooms_match.group(1)) if rooms_match else None
    
    # Quartier
    # Look for "Le Havre 76600 XXX" pattern
    quartier_match = re.search(r'Le Havre 76600\s+([^\.]+?)(?:\s+Située|$)', text)
    quartier = quartier_match.group(1).strip() if quartier_match else ""
    
    # Features
    features = []
    if "Meublé" in text: features.append("Meublé")
    if "Dernier étage" in text: features.append("Dernier étage")
    if "Terrasse" in text: features.append("Terrasse")
    if "Balcon" in text: features.append("Balcon")
    if "Cave" in text: features.append("Cave")
    if "Parking" in text: features.append("Parking")
    if "Jardin" in text: features.append("Jardin")
    if "visite virtuelle" in text.lower(): features.append("Visite virtuelle")
    if "plan" in text.lower(): features.append("Plan")
    if "Baisse de prix" in text: features.append("Baisse de prix")
    
    # Floor
    floor_match = re.search(r'Étage\s+([^\s·]+)', text)
    floor = floor_match.group(1) if floor_match else ""
    
    return {
        "id": ad_id,
        "price": price,
        "surface": surface,
        "rooms": rooms,
        "quartier": quartier,
        "features": features,
        "floor": floor,
        "text": text
    }

parsed = []
for art in articles:
    if not art["text"]:
        continue
    p = parse_article(art["text"], art["id"])
    p["link"] = art["link"]
    parsed.append(p)

print(f"Total parsed: {len(parsed)}")
print()

# Filter by criteria
def check_quartier(q):
    q_lower = q.lower().strip()
    for sq in accepted_subquartiers:
        if sq in q_lower:
            return True, sq
    return False, q_lower

qualifying = []
for p in parsed:
    print(f"--- ID: {p['id']} ---")
    print(f"  Prix: {p['price']}€ | Surface: {p['surface']}m² | Pièces: {p['rooms']} | Quartier: '{p['quartier']}'")
    print(f"  Features: {p['features']}")
    
    issues = []
    
    # Check price
    if p['price'] is None or p['price'] > 500:
        issues.append(f"prix {p['price']} > 500")
    
    # Check surface
    if p['surface'] is None or p['surface'] < 28:
        issues.append(f"surface {p['surface']} < 28m²")
    
    # Check rooms
    if p['rooms'] is None or p['rooms'] < 2:
        issues.append(f"pièces {p['rooms']} < 2")
    
    # Check quartier
    ok_q, matched_q = check_quartier(p['quartier'])
    if not ok_q:
        issues.append(f"quartier '{p['quartier']}' non accepté")
    
    # Check if already seen
    seen_id = f"lbc-{p['id']}"
    if seen_id in seen_ids:
        issues.append("DÉJÀ VU")
    
    if issues:
        print(f"  ❌ REJETÉ: {' | '.join(issues)}")
    else:
        print(f"  ✅ QUALIFIE!")
        qualifying.append(p)
    print()

print(f"\n=== QUALIFYING LISTINGS: {len(qualifying)} ===")
for p in qualifying:
    print(f"ID: {p['id']} | {p['price']}€ | {p['surface']}m² | T{p['rooms']} | {p['quartier']} | {p['features']}")
    print(f"  Link: {p['link']}")

# Save qualifying for next step
with open("/opt/data/tmp/lbc_qualifying.json", "w") as f:
    json.dump(qualifying, f, ensure_ascii=False, indent=2)