#!/usr/bin/env python3
"""Scrape LH Immo annonces page, HEUZE, Jullien-Allix, Saint Roch."""
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

# === LH Immo - annonces/location page ===
print("=== LH Immo - annonces page ===")
navigate(tab_id, "https://www.lhimmo.com/annonce/")
time.sleep(5)
links = get_all_links(tab_id)
# Filter for listing links (containing /annonce/ and price info)
listing_links = [l for l in links if '/annonce/' in l.get('url','') and any(k in l.get('parent','').lower() for k in ['€', 'mois', 'pièce', 'm²', 'm2', 't2', 't3', 'appartement'])]
print(f"Total links: {len(links)}, Listings: {len(listing_links)}")
for l in listing_links[:25]:
    url = l['url']
    # Extract ID from URL
    m = re.search(r'/annonce/([^/]+)/?', url)
    id_part = m.group(1) if m else ''
    id_ = f"lhimmo-{id_part}"
    status = "SEEN" if id_ in seen_ids else "NEW"
    
    # Parse parent text for details
    parent = l.get('parent', '')
    pm = re.search(r'(\d+)\s*€', parent)
    prix = int(pm.group(1)) if pm else 0
    sm = re.search(r'(\d+(?:[.,]\d+)?)\s*m', parent)
    surf = 0
    if sm:
        try: surf = int(float(sm.group(1).replace(',', '.')))
        except: pass
    
    print(f"  {status}: {id_} | {prix}€ | {surf}m² | {l['text'][:60]} | {url[:80]}")

# === HEUZE ===
print("\n=== HEUZE Immobilier ===")
navigate(tab_id, "https://www.heuze-immo.fr")
time.sleep(5)
body = get_body(tab_id, 5000)
links = get_all_links(tab_id)
# Find location/annonces links
loc_links = [l for l in links if 'location' in l.get('url','').lower() or 'louer' in l.get('url','').lower() or 'a-louer' in l.get('url','').lower() or 'annonce' in l.get('url','').lower()]
print(f"Body: {body[:500]}")
print(f"Location/annonce links: {len(loc_links)}")
for l in loc_links[:10]:
    print(f"  {l['text'][:60]} -> {l['url'][:80]}")

# Try to navigate to location page
if loc_links:
    # Prefer 'a-louer' or 'location' links
    best = [l for l in loc_links if 'a-louer' in l.get('url','').lower() or 'location' in l.get('url','').lower()]
    target = best[0] if best else loc_links[0]
    print(f"\nNavigating to: {target['url']}")
    navigate(tab_id, target['url'])
    time.sleep(5)
    body = get_body(tab_id, 8000)
    links = get_all_links(tab_id)
    listing_links = [l for l in links if any(k in l.get('parent','').lower() for k in ['€', 'mois', 'pièce', 'm²', 'm2', 't2', 't3', 'appartement', 'f2', 'f3'])]
    print(f"Listing links: {len(listing_links)}")
    for l in listing_links[:20]:
        url = l['url']
        m = re.search(r'/([^/]+)$', url)
        id_part = m.group(1) if m else url[-30:]
        id_ = f"heuze-{id_part}"
        status = "SEEN" if id_ in seen_ids else "NEW"
        parent = l.get('parent', '')
        pm = re.search(r'(\d+)\s*€', parent)
        prix = int(pm.group(1)) if pm else 0
        print(f"  {status}: {id_} | {prix}€ | {l['text'][:60]} | {url[:80]}")