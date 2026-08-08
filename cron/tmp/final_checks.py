#!/usr/bin/env python3
"""Final checks: Bien'ici T2 listings, Foncia, Century21, and verify Saint Roch IDs."""
import json, subprocess, time, re

def navigate(tab_id, url):
    payload = json.dumps({'url': url, 'userId': 'hermes-veille'})
    subprocess.run(['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/navigate',
                    '-H', 'Content-Type: application/json', '-d', payload],
                   capture_output=True, text=True, timeout=30)

def get_body(tab_id, max_len=12000):
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
    js = '''JSON.stringify(Array.from(document.querySelectorAll("a")).map(function(a){var c=a.closest("[class]")||a.parentElement;var p=c?c.innerText:"";return{url:a.href,text:a.innerText.substring(0,200),parent:p.substring(0,300)}}).filter(function(x){return x.text.length>3 && x.url && x.url.indexOf("javascript")<0}))'''
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

# Check Saint Roch seen IDs
print("=== Saint Roch seen IDs ===")
stroch_seen = [s for s in seen_ids if s.startswith('stroch-')]
print(f"Count: {len(stroch_seen)}")
for s in sorted(stroch_seen):
    print(f"  {s}")

# Check if stroch-LA1658 is in seen
print(f"\nstroch-LA1658 in seen: {'stroch-LA1658' in seen_ids}")

# === Bien'ici ===
print("\n=== Bien'ici (filtered: prix-max=500, pieces-min=2) ===")
navigate(tab_id, "https://www.bienici.com/recherche/location/le-havre-76600/appartement?prix-max=500&pieces-min=2")
time.sleep(6)
body = get_body(tab_id, 12000)
links = get_all_links(tab_id)
# Filter for listing links
bi_listings = [l for l in links if '/annonce/location/' in l.get('url','')]
print(f"Body (first 2000): {body[:2000]}")
print(f"\nListing links: {len(bi_listings)}")
for l in bi_listings[:15]:
    url = l['url']
    # Extract ID from URL
    m = re.search(r'/annonce/location/.+/(.+)$', url)
    id_part = m.group(1) if m else ''
    id_ = f"bienici-{id_part}"
    status = "SEEN" if id_ in seen_ids else "NEW"
    
    parent = l.get('parent', '')
    text = l.get('text', '')
    # Extract pieces, surface, price
    pm = re.search(r'(\d+)\s*pi[èe]ces?\s*(\d+)\s*m', text + ' ' + parent)
    pieces = int(pm.group(1)) if pm else 0
    surf = int(pm.group(2)) if pm else 0
    
    prm = re.search(r'(\d+)\s*€', parent)
    prix = int(prm.group(1)) if prm else 0
    
    # Extract quartier
    qm = re.search(r'Le Havre\s*\(([^)]+)\)', parent + ' ' + text)
    quartier = qm.group(1) if qm else ""
    
    print(f"  {status}: {id_} | {prix}€ | {pieces}p | {surf}m² | {quartier[:30]} | {url[:80]}")

# === Foncia ===
print("\n=== Foncia ===")
navigate(tab_id, "https://fr.foncia.com/location/le-havre-76")
time.sleep(5)
body = get_body(tab_id, 8000)
links = get_all_links(tab_id)
listing_links = [l for l in links if any(k in l.get('parent','').lower() for k in ['€', 'mois', 'pièce', 'm²', 'appartement', 't2', 't3', 'f2', 'f3'])]
print(f"Body (first 2000): {body[:2000]}")
print(f"\nListing links: {len(listing_links)}")
for l in listing_links[:15]:
    url = l['url']
    m = re.search(r'/([^/]+)$', url)
    id_part = m.group(1) if m else url[-30:]
    id_ = f"foncia-{id_part}"
    status = "SEEN" if id_ in seen_ids else "NEW"
    parent = l.get('parent', '')
    prm = re.search(r'(\d+)\s*€', parent)
    prix = int(prm.group(1)) if prm else 0
    print(f"  {status}: {id_} | {prix}€ | {l['text'][:60]} | {url[:80]}")

# === Century21 ===
print("\n=== Century21 ===")
navigate(tab_id, "https://www.century21.fr/annonces/location-appartement/v-le+havre/")
time.sleep(5)
body = get_body(tab_id, 10000)
links = get_all_links(tab_id)
listing_links = [l for l in links if '/annonce/' in l.get('url','') and any(k in l.get('parent','').lower() for k in ['€', 'mois', 'pièce', 'm²', 'appartement'])]
print(f"Body (first 2000): {body[:2000]}")
print(f"\nListing links: {len(listing_links)}")
for l in listing_links[:15]:
    url = l['url']
    m = re.search(r'/annonce/([^/]+)', url)
    id_part = m.group(1) if m else ''
    id_ = f"c21-{id_part}"
    status = "SEEN" if id_ in seen_ids else "NEW"
    parent = l.get('parent', '')
    prm = re.search(r'(\d+)\s*€', parent)
    prix = int(prm.group(1)) if prm else 0
    print(f"  {status}: {id_} | {prix}€ | {l['text'][:60]} | {url[:80]}")