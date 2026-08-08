#!/usr/bin/env python3
"""Scrape SquareHabitat, PAP, Citya, Foncia, Century21, Orpi, and local agencies."""
import json, subprocess, time, re

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
        return None
    except:
        return None

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

def get_body_text(tab_id):
    result = eval_js(tab_id, "document.body.innerText.substring(0, 8000)")
    return result if result else ""

# Use existing tab
tab_id = "41c46838-108d-4fd5-aa28-f27e490b615c"

# === SquareHabitat ===
print("=== SquareHabitat ===")
navigate(tab_id, "https://www.squarehabitat.fr/annonces/location/bien/appartement/immobilier/normandie/seine-maritime/le-havre-76600")
time.sleep(5)
snap = get_snapshot(tab_id)
snap_text = snap.get('snapshot', '')
print(f"Snapshot len: {len(snap_text)}")
# Extract listings from snapshot
# SquareHabitat uses links with /annonces/location/ pattern
entries = re.findall(r'(\d+)[\s,]*m[\xb2\s].*?(\d+)\s*€.*?(?:/annonces/location/|/bien/)([a-f0-9-]+)', snap_text, re.DOTALL)
if not entries:
    # Try alternate pattern
    links = re.findall(r'/url: (.*?squarehabitat.*?location.*?([a-f0-9-]+).*?)$', snap_text, re.MULTILINE)
    for l in links:
        print(f"  Link: {l}")
# Print relevant section
idx = snap_text.find('heading')
if idx > 0:
    print(snap_text[idx:idx+2000])
else:
    print(snap_text[:2000])