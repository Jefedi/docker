#!/usr/bin/env python3
"""Scrape HEUZE location page, Jullien-Allix, Saint Roch."""
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
    js = '''JSON.stringify(Array.from(document.querySelectorAll("a")).map(function(a){var c=a.closest("[class]")||a.parentElement;var p=c?c.innerText:"";return{url:a.href,text:a.innerText.substring(0,200),parent:p.substring(0,300)}}).filter(function(x){return x.text.length>3 && x.url && x.url.indexOf("javascript")<0 && x.url.indexOf("#")<0}))'''
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

# === HEUZE location/appartement ===
print("=== HEUZE location/appartement/le-havre/76600 ===")
navigate(tab_id, "https://www.heuze-immo.fr/location/appartement/le-havre/76600")
time.sleep(5)
body = get_body(tab_id, 10000)
links = get_all_links(tab_id)
# Filter listing links
listing_links = [l for l in links if '/location/' in l.get('url','') and 'appartement' in l.get('url','').lower() and any(k in l.get('parent','').lower() for k in ['€', 'mois', 'pièce', 'm²', 't2', 't3', 'f2', 'f3'])]
print(f"Body: {body[:2000]}")
print(f"\nListing links: {len(listing_links)}")
for l in listing_links[:20]:
    url = l['url']
    # Extract ID
    m = re.search(r',(\w+)$', url)
    id_part = m.group(1) if m else ''
    id_ = f"heuze-{id_part}"
    status = "SEEN" if id_ in seen_ids else "NEW"
    
    parent = l.get('parent', '')
    pm = re.search(r'(\d+)\s*€', parent)
    prix = int(pm.group(1)) if pm else 0
    sm = re.search(r'(\d+(?:[.,]\d+)?)\s*m', parent)
    surf = 0
    if sm:
        try: surf = int(float(sm.group(1).replace(',', '.')))
        except: pass
    
    print(f"  {status}: {id_} | {prix}€ | {surf}m² | {l['text'][:60]} | {url[:80]}")

# === Jullien-Allix ===
print("\n=== Jullien-Allix ===")
navigate(tab_id, "https://www.jullien-allix.fr/annonce/location")
time.sleep(5)
body = get_body(tab_id, 10000)
links = get_all_links(tab_id)
# JA listing links
ja_listings = [l for l in links if '/annonce/' in l.get('url','') and 'location' in l.get('url','').lower()]
print(f"Body: {body[:2000]}")
print(f"\nJA listing links: {len(ja_listings)}")
for l in ja_listings[:25]:
    url = l['url']
    # Extract slug from URL
    m = re.search(r'/annonce/([^/]+)/?', url)
    id_part = m.group(1) if m else ''
    id_ = f"ja-{id_part}"
    status = "SEEN" if id_ in seen_ids else "NEW"
    
    parent = l.get('parent', '')
    pm = re.search(r'(\d+)\s*€', parent)
    prix = int(pm.group(1)) if pm else 0
    
    print(f"  {status}: {id_} | {prix}€ | {l['text'][:60]} | {url[:80]}")

# === Saint Roch ===
print("\n=== Saint Roch ===")
navigate(tab_id, "https://www.saintrochimmo.com")
time.sleep(5)
body = get_body(tab_id, 5000)
links = get_all_links(tab_id)
# Find location page
loc_links = [l for l in links if 'location' in l.get('url','').lower() or 'louer' in l.get('text','').lower() or 'a-louer' in l.get('url','').lower()]
print(f"Body: {body[:1000]}")
print(f"Location links: {len(loc_links)}")
for l in loc_links[:10]:
    print(f"  {l['text'][:60]} -> {l['url'][:80]}")

# Navigate to location page
if loc_links:
    target = loc_links[0]
    print(f"\nNavigating to: {target['url']}")
    navigate(tab_id, target['url'])
    time.sleep(5)
    body = get_body(tab_id, 8000)
    links = get_all_links(tab_id)
    listing_links = [l for l in links if any(k in l.get('parent','').lower() for k in ['€', 'mois', 'pièce', 'm²', 't2', 't3', 'appartement', 'f2', 'f3'])]
    print(f"Listing links: {len(listing_links)}")
    for l in listing_links[:25]:
        url = l['url']
        m = re.search(r'/([^/]+)$', url)
        id_part = m.group(1) if m else url[-30:]
        id_ = f"stroch-{id_part}"
        status = "SEEN" if id_ in seen_ids else "NEW"
        parent = l.get('parent', '')
        pm = re.search(r'(\d+)\s*€', parent)
        prix = int(pm.group(1)) if pm else 0
        print(f"  {status}: {id_} | {prix}€ | {l['text'][:60]} | {url[:80]}")