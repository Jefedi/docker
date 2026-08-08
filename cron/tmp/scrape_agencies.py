#!/usr/bin/env python3
"""Scrape Citya, Century21, Orpi, LH Immo, HEUZE, Jullien-Allix, Saint Roch, Bien'ici, Foncia."""
import json, subprocess, time, re

def navigate(tab_id, url):
    payload = json.dumps({'url': url, 'userId': 'hermes-veille'})
    subprocess.run(['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/navigate',
                    '-H', 'Content-Type: application/json', '-d', payload],
                   capture_output=True, text=True, timeout=30)

def get_snapshot(tab_id):
    result = subprocess.run(
        ['curl', '-s', f'http://127.0.0.1:9377/tabs/{tab_id}/snapshot?userId=hermes-veille'],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout)
    except:
        return {}

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
    js = '''JSON.stringify(Array.from(document.querySelectorAll("a")).map(function(a){return{url:a.href,text:a.innerText.substring(0,150)}}).filter(function(x){return x.text && x.url}))'''
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

# Load seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

sources = [
    ("Citya", "https://www.citya.com/annonces/location/appartement/le-havre-76351", "citya"),
    ("Century21", "https://www.century21.fr/annonces/location-appartement/v-le+havre/", "c21"),
    ("Orpi", "https://www.orpi.com/location-immobiliere-le-havre/louer-appartement/", "orpi"),
    ("Bien'ici", "https://www.bienici.com/recherche/location/le-havre-76600/appartement?prix-max=500&pieces-min=2", "bienici"),
    ("Foncia", "https://fr.foncia.com/location/le-havre-76", "foncia"),
    ("LH Immo", "https://www.lhimmo.com", "lhimmo"),
    ("HEUZE", "https://www.heuze-immo.fr", "heuze"),
    ("Jullien-Allix", "https://www.jullien-allix.fr/annonce/location", "ja"),
    ("Saint Roch", "https://www.saintrochimmo.com", "stroch"),
]

all_new = []

for name, url, prefix in sources:
    print(f"\n=== {name} ===")
    navigate(tab_id, url)
    time.sleep(5)
    
    # Try snapshot first
    snap = get_snapshot(tab_id)
    snap_text = snap.get('snapshot', '')
    body = get_body(tab_id, 12000)
    
    # Check if blocked
    if 'security' in body.lower() or 'captcha' in body.lower() or 'bot' in body.lower():
        print(f"  BLOCKED: {body[:200]}")
        continue
    
    # Get all links
    links = get_all_links(tab_id)
    
    # Filter for listing links
    listing_links = []
    for l in links:
        text_lower = l.get('text', '').lower()
        url_lower = l.get('url', '').lower()
        # Look for rental-related links
        if any(k in url_lower for k in ['location', 'louer', 'rent', 'annonce', 'bien', 'a-louer']):
            if any(k in text_lower for k in ['€', 'euros', 'pièce', 'm²', 'm2', 'appartement', 't2', 't3', 'f2', 'f3']):
                listing_links.append(l)
    
    print(f"  Total links: {len(links)}, Listing-like: {len(listing_links)}")
    for ll in listing_links[:20]:
        print(f"    {ll['text'][:80]} -> {ll['url'][:80]}")
    
    if not listing_links:
        # Print body to see what's there
        print(f"  Body (first 2000): {body[:2000]}")