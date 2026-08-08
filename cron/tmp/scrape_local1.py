#!/usr/bin/env python3
"""Scrape LH Immo, HEUZE, Jullien-Allix, Saint Roch, Foncia, Bien'ici."""
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
    js = '''JSON.stringify(Array.from(document.querySelectorAll("a")).map(function(a){return{url:a.href,text:a.innerText.substring(0,200)}}).filter(function(x){return x.text.length>5 && x.url}))'''
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

# === LH Immo ===
print("=== LH Immo ===")
navigate(tab_id, "https://www.lhimmo.com")
time.sleep(5)
body = get_body(tab_id, 5000)
links = get_all_links(tab_id)
# Find location page link
location_links = [l for l in links if 'location' in l.get('url','').lower() or 'louer' in l.get('text','').lower()]
print(f"Body: {body[:1000]}")
print(f"Location links: {len(location_links)}")
for l in location_links[:10]:
    print(f"  {l['text'][:60]} -> {l['url'][:80]}")

# Navigate to location page if found
if location_links:
    loc_url = location_links[0]['url']
    print(f"\nNavigating to: {loc_url}")
    navigate(tab_id, loc_url)
    time.sleep(5)
    body = get_body(tab_id, 8000)
    links = get_all_links(tab_id)
    # Find listing links
    listing_links = [l for l in links if any(k in l.get('text','').lower() for k in ['€', 'euros', 'pièce', 'm²', 'm2', 't2', 't3', 'appartement'])]
    print(f"Listing links: {len(listing_links)}")
    for l in listing_links[:20]:
        print(f"  {l['text'][:80]} -> {l['url'][:80]}")