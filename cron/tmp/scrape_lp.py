#!/usr/bin/env python3
"""Scrape Le-Partenaire, SquareHabitat, and local agencies via camofox."""
import json, subprocess, time

def eval_js(tab_id, js_expr):
    payload = json.dumps({'userId': 'hermes-veille', 'expression': js_expr})
    result = subprocess.run(
        ['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/evaluate',
         '-H', 'Content-Type: application/json', '-d', payload],
        capture_output=True, text=True, timeout=30
    )
    try:
        data = json.loads(result.stdout)
        if data.get('ok'):
            return data.get('result', '[]')
        return '[]'
    except:
        return '[]'

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

# Get new tab
result = subprocess.run(
    ['curl', '-s', '-X', 'POST', 'http://127.0.0.1:9377/tabs',
     '-H', 'Content-Type: application/json',
     '-d', json.dumps({'userId': 'hermes-veille', 'sessionKey': 'havre'})],
    capture_output=True, text=True, timeout=30
)
tab_id = json.loads(result.stdout).get('tabId', '')
print(f"Tab: {tab_id}")

# === Le-Partenaire locations ===
print("\n=== Le-Partenaire locations ===")
navigate(tab_id, "https://www.le-partenaire.fr/immobilier/location/appartement/le-havre/76600?loyer-max=500&pieces=2")
time.sleep(4)
snap = get_snapshot(tab_id)
snapshot_text = snap.get('snapshot', '')
print(f"Snapshot length: {len(snapshot_text)}")
# Print relevant parts
import re
# Find listings
articles = re.findall(r'heading.*?(\d+p?\s*\d+m²|T\d.*?m²).*?(?=heading|$)', snapshot_text, re.DOTALL)
# Better: look for links
links = re.findall(r'link.*?/url: (.*?location/appartement/.*?)\n', snapshot_text)
for l in links[:20]:
    print(f"  Link: {l}")
# Also print a section of the snapshot
if len(snapshot_text) > 500:
    # Find listing area
    idx = snapshot_text.find('heading')
    if idx > 0:
        print(snapshot_text[idx:idx+3000])

# Check for multiple pages
page_links = re.findall(r'/url: .*?page=(\d+)', snapshot_text)
print(f"\nPage links found: {page_links}")