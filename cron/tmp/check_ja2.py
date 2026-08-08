#!/usr/bin/env python3
"""Check JA listings properly."""
import json, subprocess, time, re

def get_all_links(tab_id):
    js = '''JSON.stringify(Array.from(document.querySelectorAll("a")).map(function(a){return{url:a.href,text:a.innerText.substring(0,300)}}).filter(function(x){return x.text.length>10 && x.url && x.url.indexOf("javascript")<0}))'''
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

def get_body(tab_id, max_len=15000):
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

tab_id = "41c46838-108d-4fd5-aa28-f27e490b615c"

with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

body = get_body(tab_id, 15000)
links = get_all_links(tab_id)

# JA listing links
ja_listing_links = [l for l in links if '/annonce-immobiliere/' in l.get('url','')]

# Parse listings from body
listings_raw = re.findall(r'(\d+)€/par mois\s*CC\s*\n(A Louer [^\n]+)', body)

accepted_quartiers = [
    'centre-ville', 'coty', 'massillon', 'eure', 'félix faure', 'felix faure',
    'perret', 'docks', 'rond point - observatoire', 'saint-françois - les docks',
    'saint-francois - les docks', 'danton', 'sanvic', 'bléville', 'bleville',
]

print(f"Total JA listings: {len(listings_raw)}")
print(f"Total JA links: {len(ja_listing_links)}")

for prix_str, title in listings_raw:
    prix = int(prix_str)
    
    # Parse type
    tm = re.search(r'Type\s+(\w?\d+)', title)
    typ = tm.group(1).lower() if tm else ""
    
    # Get number of pieces
    pieces = 0
    if typ:
        m = re.search(r'(\d+)', typ)
        if m:
            pieces = int(m.group(1))
    
    # Parse quartier
    qm = re.search(r'–\s*LE HAVRE\s*–\s*(.+?)(?:\n|$)', title, re.IGNORECASE)
    quartier = qm.group(1).strip() if qm else ""
    
    # Find surface
    idx = body.find(title)
    nearby = body[idx:idx+600] if idx >= 0 else ""
    sm = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', nearby)
    surf = 0
    if sm:
        try: surf = int(float(sm.group(1).replace(',', '.')))
        except: pass
    
    # Find URL
    listing_url = ""
    # Try matching by part of the title
    title_lower = title.lower()
    for l in ja_listing_links:
        ltext = l.get('text', '').lower()
        # Match if key parts are in the link text
        if 'jardins d' in title_lower and 'jardins d' in ltext:
            listing_url = l['url']
            break
        elif 'ormeaux' in title_lower and 'ormeaux' in ltext:
            listing_url = l['url']
            break
        elif 'maréchal joffre' in title_lower and 'marechal joffre' in ltext:
            listing_url = l['url']
            break
        elif 'danton' in title_lower and 'danton' in ltext:
            listing_url = l['url']
            break
        elif 'docks' in title_lower and 'docks' in ltext:
            listing_url = l['url']
            break
        elif 'centre ville' in title_lower and 'centre-ville' in ltext:
            listing_url = l['url']
            break
        elif 'demidoff' in title_lower and 'demidoff' in ltext:
            listing_url = l['url']
            break
        elif 'sanvic' in title_lower and 'sanvic' in ltext:
            listing_url = l['url']
            break
        elif 'pasino' in title_lower and 'pasino' in ltext:
            listing_url = l['url']
            break
        elif 'anatole france' in title_lower and 'anatole-france' in ltext:
            listing_url = l['url']
            break
    
    # Extract slug from URL
    id_slug = ""
    if listing_url:
        m = re.search(r'/annonce-immobiliere/([^/]+)/?', listing_url)
        if m:
            id_slug = m.group(1)
    
    if not id_slug:
        id_slug = re.sub(r'[^a-z0-9-]', '', title.lower().replace(' ', '-').replace('–', '-').replace("'", ''))[:80]
    
    id_ = f"ja-{id_slug}"
    status = "SEEN" if id_ in seen_ids else "NEW"
    
    # Check quartier
    q_lower = quartier.lower()
    quartier_accepted = any(aq in q_lower for aq in accepted_quartiers)
    
    # Filter: T2+ (pieces >= 2), price <= 500, surface >= 28
    if pieces >= 2 and prix <= 500 and surf >= 28:
        print(f"\n  {status}: {prix}€ | F{pieces} | {surf}m² | {quartier} | quartier_ok={quartier_accepted}")
        print(f"    ID: {id_}")
        if listing_url:
            print(f"    URL: {listing_url[:100]}")
        if status == "NEW" and quartier_accepted:
            print(f"    *** POTENTIAL MATCH! ***")
    elif pieces >= 2 and prix <= 500:
        print(f"  {status} (below 28m²): {prix}€ | F{pieces} | {surf}m² | {quartier}")