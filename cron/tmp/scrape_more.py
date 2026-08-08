#!/usr/bin/env python3
"""Scrape PAP, Citya, Century21, Orpi, LH Immo, HEUZE, Jullien-Allix, Saint Roch, Bien'ici, Foncia."""
import json, subprocess, time, re

def navigate(tab_id, url):
    payload = json.dumps({'url': url, 'userId': 'hermes-veille'})
    result = subprocess.run(['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/navigate',
                    '-H', 'Content-Type: application/json', '-d', payload],
                   capture_output=True, text=True, timeout=30)
    try:
        return json.loads(result.stdout)
    except:
        return {}

def get_snapshot(tab_id):
    result = subprocess.run(
        ['curl', '-s', f'http://127.0.0.1:9377/tabs/{tab_id}/snapshot?userId=hermes-veille'],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout)
    except:
        return {}

def get_body(tab_id, max_len=10000):
    payload = json.dumps({'userId': 'hermes-veille', 'expression': 'document.body.innerText.substring(0, ' + str(max_len) + ')'})
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

def get_links(tab_id, url_pattern):
    js = f'''JSON.stringify(Array.from(document.querySelectorAll("a")).filter(function(a){{return a.href.indexOf("{url_pattern}")>-1}}).map(function(a){{return{{url:a.href,text:a.innerText.substring(0,200)}}}}))'''
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

# === PAP.fr ===
print("\n=== PAP.fr ===")
navigate(tab_id, "https://www.pap.fr/annonce/locations-appartement-le-havre-76600-g43635")
time.sleep(5)
snap = get_snapshot(tab_id)
snap_text = snap.get('snapshot', '')
print(f"Snapshot len: {len(snap_text)}")
# Find listings
links = re.findall(r'/url: (https://www\.pap\.fr/annonce/locations/[^"\n]+)', snap_text)
prices = re.findall(r'(\d+)\s*€', snap_text)
# Print relevant section
idx = snap_text.find('heading')
if idx > 0:
    relevant = snap_text[idx:idx+3000]
    print(relevant[:2000])
else:
    print(snap_text[:2000])

# Get all listing links with text
body = get_body(tab_id, 15000)
print(f"\nBody text (first 3000): {body[:3000]}")