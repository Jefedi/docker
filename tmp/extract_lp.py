import json, subprocess, sys, time, re

TAB = "400718c1-768b-46c4-ab9d-c74f757bfa58"

def evaluate(expr):
    r = subprocess.run(["curl", "-s", "-X", "POST", f"http://127.0.0.1:9377/tabs/{TAB}/evaluate",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"userId":"hermes-veille","expression":expr})
    ], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        return d.get("result","")
    except:
        return ""

# Get full text
total_len = int(evaluate("document.body.innerText.length") or "0")
print(f"Total innerText length: {total_len}")

full_text = ""
chunk_size = 4000
for start in range(0, total_len, chunk_size):
    chunk = evaluate(f"document.body.innerText.substring({start},{start+chunk_size})")
    if chunk:
        full_text += chunk

with open("/opt/data/tmp/lepartenaire_full.txt","w") as f:
    f.write(full_text)

# Get the "Voir l'annonce" links
links = evaluate("Array.from(document.querySelectorAll('a')).filter(a=>a.textContent.includes('Voir')).map(a=>a.href).join('\\n')")
print(f"Links: {links}")

# Also get h2 headings
h2s = evaluate("Array.from(document.querySelectorAll('h2')).map(h=>h.textContent.trim()).join('\\n')")
print(f"H2s:\n{h2s}")

# Parse listings from text
# Pattern: "Location Appartement à Le Havre N pièces | XX m²" followed by price
# The text format seems to be blocks separated by "Voir l'annonce"
blocks = full_text.split("Voir l'annonce")
print(f"\nFound {len(blocks)} blocks (including last partial)")

listings = []
for i, block in enumerate(blocks[:-1]):  # skip last partial
    # Extract rooms and surface from title
    title_match = re.search(r'Location Appartement à Le Havre (\d+)\s*pièces\s*\|\s*(\d+)\s*m²', block)
    if title_match:
        rooms = int(title_match.group(1))
        surface = int(title_match.group(2))
    else:
        rooms = None
        surface = None
    
    # Extract price
    price_match = re.search(r'(\d+)\s*€\s*/\s*mois', block)
    if price_match:
        price = int(price_match.group(1))
    else:
        price = None
    
    # Extract quartier
    quartier = ""
    q_match = re.search(r'Quartier\s+([A-Z][^.]+?)(?:,\s*à)', block)
    if q_match:
        quartier = q_match.group(1).strip()
    
    # Check for cuisine séparée/indépendante
    cuisine_sep = "cuisine indépendante" in block.lower() or "cuisine séparée" in block.lower() or "cuisine indépendante" in block.lower()
    cuisine_ouverte = "cuisine ouverte" in block.lower() or "cuisine américaine" in block.lower() or "kitchenette" in block.lower()
    
    # Check for features
    meuble = "meublé" in block.lower() or "meuble" in block.lower()
    balcon = "balcon" in block.lower() or "terrasse" in block.lower()
    
    # Description snippet
    desc_start = block.find("€")
    desc = block[desc_start:desc_start+500] if desc_start >= 0 else block[:500]
    
    listing = {
        "idx": i,
        "rooms": rooms,
        "surface": surface,
        "price": price,
        "quartier": quartier,
        "cuisine_sep": cuisine_sep,
        "cuisine_ouverte": cuisine_ouverte,
        "meuble": meuble,
        "balcon": balcon,
        "desc": desc.strip()[:300]
    }
    listings.append(listing)
    
    print(f"\n--- Listing {i} ---")
    print(f"  Rooms: {rooms} | Surface: {surface}m² | Price: {price}€ | Quartier: {quartier}")
    print(f"  Cuisine séparée: {cuisine_sep} | Cuisine ouverte: {cuisine_ouverte} | Meublé: {meuble}")
    print(f"  Desc: {desc.strip()[:200]}")

with open("/opt/data/tmp/lepartenaire_listings.json","w") as f:
    json.dump(listings, f, ensure_ascii=False, indent=2)