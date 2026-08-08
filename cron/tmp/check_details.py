#!/usr/bin/env python3
"""Check Saint Roch LA1658 details and parse JA listings from body text."""
import json, subprocess, time, re

def navigate(tab_id, url):
    payload = json.dumps({'url': url, 'userId': 'hermes-veille'})
    subprocess.run(['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/navigate',
                    '-H', 'Content-Type: application/json', '-d', payload],
                   capture_output=True, text=True, timeout=30)

def get_body(tab_id, max_len=10000):
    payload = json.dumps({'userId': 'hermes-veille', 'expression': f'document.body.innerText.substring(0, {max_len})'})
    result = subprocess.run(
        ['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/evaluate',
         '-H', 'Content-Type: application/json', '-d', payload],
        capture_output=True, text=True, timeout=30
    )
    try:
        data = json.loads(result.stdout)
        return data.get('result', '')
    except:
        return ''

def get_all_links(tab_id):
    js = '''JSON.stringify(Array.from(document.querySelectorAll("a")).map(function(a){return{url:a.href,text:a.innerText.substring(0,200)}}).filter(function(x){return x.text.length>10 && x.url && x.url.indexOf("javascript")<0}))'''
    payload = json.dumps({'userId': 'hermes-veille', 'expression': js})
    result = subprocess.run(
        ['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/evaluate',
         '-H', 'Content-Type: application/json', '-d', payload],
        capture_output=True, text=True, timeout=30
    )
    try:
        data = json.loads(result.stdout)
        if data.get('ok'):
            return json.loads(data.get('result', '[]'))
        return []
    except:
        return []

tab_id = "41c46838-108d-4fd5-aa28-f27e490b615c"

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

accepted_quartiers = {
    'centre-ville', 'coty', 'massillon', 'eure', 'félix faure', 'felix faure',
    'perret', 'docks', 'rond point - observatoire', 'saint-françois - les docks',
    'saint-francois - les docks', 'danton', 'sanvic', 'bléville', 'bleville',
}

# === Check Saint Roch LA1658 ===
print("=== Saint Roch LA1658 (T2 duplex, 495€) ===")
navigate(tab_id, "https://www.saintrochimmo.com/location/appartement-duplex-2-pieces-le-havre-76600,LA1658")
time.sleep(5)
body = get_body(tab_id, 8000)
print(f"Body: {body[:3000]}")

# Extract details
body_lower = body.lower()
prix_match = re.search(r'(\d+)\s*€', body)
prix = int(prix_match.group(1)) if prix_match else 0
surf_match = re.search(r'(\d+(?:[.,]\d+)?)\s*m', body)
surf = 0
if surf_match:
    try: surf = int(float(surf_match.group(1).replace(',', '.')))
    except: pass

cuisine_sep = any(k in body_lower for k in ['cuisine séparée', 'cuisine indépendante', 'cuisine fermée'])
cuisine_ouverte = any(k in body_lower for k in ['cuisine ouverte', 'cuisine américaine', 'séjour cuisine ouvert'])
chambre = 'chambre' in body_lower

# Find quartier
quartier = ""
for q in accepted_quartiers:
    if q in body_lower:
        quartier = q
        break

print(f"\nPrix: {prix}€ | Surface: {surf}m² | Cuisine séparée: {cuisine_sep} | Cuisine ouverte: {cuisine_ouverte} | Chambre: {chambre} | Quartier: {quartier}")

# Check if qualifies
qualifies = prix <= 500 and surf >= 28 and quartier in accepted_quartiers
print(f"Qualifies: {qualifies}")

# === Parse JA listings from body text ===
print("\n\n=== Jullien-Allix listings (from body text) ===")
navigate(tab_id, "https://www.jullien-allix.fr/annonce/location")
time.sleep(5)
body = get_body(tab_id, 15000)
links = get_all_links(tab_id)

# Parse body text for listings
# Pattern: "XXX€/par mois CC\nA Louer Appartement De Type F2 ... – LE HAVRE – ..."
listings_raw = re.findall(r'(\d+)€/par mois\s*CC\s*\n(A Louer [^\n]+)', body)
print(f"Found {len(listings_raw)} listings in body text:")
for prix_str, title in listings_raw:
    prix = int(prix_str)
    # Parse type
    tm = re.search(r'Type\s+(\w\d+)', title)
    typ = tm.group(1) if tm else ""
    # Parse quartier from title
    qm = re.search(r'–\s*LE HAVRE\s*–\s*(.+)', title, re.IGNORECASE)
    quartier = qm.group(1).strip() if qm else ""
    
    # Get surface from surrounding text
    # Look for surface near this listing in body
    idx = body.find(title)
    nearby = body[idx:idx+500] if idx >= 0 else ""
    sm = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', nearby)
    surf = 0
    if sm:
        try: surf = int(float(sm.group(1).replace(',', '.')))
        except: pass
    
    # Find the URL for this listing
    listing_url = ""
    for l in links:
        if title[:30].lower() in l.get('text', '').lower() or any(word in l.get('text', '').lower() for word in title.split()[:5]):
            listing_url = l['url']
            break
    
    # Extract ID from URL
    id_part = ""
    if listing_url:
        m = re.search(r'/annonce/([^/]+)', listing_url)
        if m:
            id_part = m.group(1)
    
    id_ = f"ja-{id_part}" if id_part else f"ja-{title[:30].replace(' ', '-').lower()}"
    status = "SEEN" if id_ in seen_ids else "NEW"
    
    print(f"  {status}: {prix}€ | {typ} | {surf}m² | {quartier[:40]} | {id_}")
    if listing_url:
        print(f"    URL: {listing_url[:80]}")