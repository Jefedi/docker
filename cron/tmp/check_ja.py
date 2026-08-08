#!/usr/bin/env python3
"""Check JA listings for T2 ≤500€ in accepted quartiers with proper ID extraction."""
import json, subprocess, time, re

def navigate(tab_id, url):
    payload = json.dumps({'url': url, 'userId': 'hermes-veille'})
    subprocess.run(['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/navigate',
                    '-H', 'Content-Type: application/json', '-d', payload],
                   capture_output=True, text=True, timeout=30)

def get_all_links(tab_id):
    js = '''JSON.stringify(Array.from(document.querySelectorAll("a")).map(function(a){var c=a.closest("[class]")||a.parentElement;var p=c?c.innerText:"";return{url:a.href,text:a.innerText.substring(0,200),parent:p.substring(0,400)}}).filter(function(x){return x.text.length>10 && x.url && x.url.indexOf("javascript")<0}))'''
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

# JA seen IDs
ja_seen = [s for s in seen_ids if s.startswith('ja-')]
print(f"JA seen IDs: {len(ja_seen)}")

# Navigate to JA location page
navigate(tab_id, "https://www.jullien-allix.fr/annonce/location")
time.sleep(5)
body = get_body(tab_id, 15000)
links = get_all_links(tab_id)

# Find JA listing links - they should contain /annonce-immobiliere/
ja_listing_links = [l for l in links if '/annonce-immobiliere/' in l.get('url','')]
print(f"JA listing links: {len(ja_listing_links)}")

# Parse each listing from body text
# Pattern: "XXX€/par mois CC\nA Louer Appartement De Type FX ... – LE HAVRE – ..."
listings_raw = re.findall(r'(\d+)€/par mois\s*CC\s*\n(A Louer [^\n]+)', body)

# Also get surface from body
# Each listing section has "m²" after the title
for prix_str, title in listings_raw:
    prix = int(prix_str)
    
    # Parse type (F1, F2, F3, etc.)
    tm = re.search(r'Type\s+(\w\d+)', title)
    typ = tm.group(1) if tm else ""
    
    # Parse quartier
    qm = re.search(r'–\s*LE HAVRE\s*–\s*(.+?)(?:\n|$)', title, re.IGNORECASE)
    quartier = qm.group(1).strip() if qm else ""
    
    # Find surface from body near this listing
    idx = body.find(title)
    nearby = body[idx:idx+600] if idx >= 0 else ""
    sm = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', nearby)
    surf = 0
    if sm:
        try: surf = int(float(sm.group(1).replace(',', '.')))
        except: pass
    
    # Find URL for this listing from links
    listing_url = ""
    # The title has key words we can match
    title_words = [w.lower() for w in title.split() if len(w) > 3]
    for l in ja_listing_links:
        ltext = l.get('text', '').lower()
        if any(w in ltext for w in title_words[:3]):
            listing_url = l['url']
            break
    
    # Extract slug from URL
    id_slug = ""
    if listing_url:
        m = re.search(r'/annonce-immobiliere/([^/]+)/?', listing_url)
        if m:
            id_slug = m.group(1)
    
    if not id_slug:
        # Generate slug from title
        id_slug = title.lower().replace(' ', '-').replace('–', '').replace(',', '')[:60]
        # Clean
        id_slug = re.sub(r'[^a-z0-9-]', '', id_slug)
    
    id_ = f"ja-{id_slug}"
    status = "SEEN" if id_ in seen_ids else "NEW"
    
    # Determine if F2+ (2 pieces minimum)
    is_t2_plus = typ in ['f2', 'f3', 'f4', 'f5', 'f6', 't2', 't3', 't4', 't5', 't6'] or (typ.startswith('f') and int(typ[1:]) >= 2) if typ else False
    
    # Check quartier acceptance
    accepted_quartiers = {
        'centre-ville', 'coty', 'massillon', 'eure', 'félix faure', 'felix faure',
        'perret', 'docks', 'rond point - observatoire', 'saint-françois - les docks',
        'saint-francois - les docks', 'danton', 'sanvic', 'bléville', 'bleville',
    }
    q_lower = quartier.lower()
    quartier_accepted = any(aq in q_lower for aq in accepted_quartiers)
    
    if prix <= 500 and is_t2_plus and surf >= 28:
        print(f"\n  {status}: {prix}€ | {typ} | {surf}m² | {quartier} | quartier_ok={quartier_accepted}")
        print(f"    ID: {id_}")
        if listing_url:
            print(f"    URL: {listing_url}")
        if status == "NEW" and quartier_accepted:
            print(f"    *** POTENTIAL MATCH! ***")