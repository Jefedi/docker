#!/usr/bin/env python3
"""Check Orpi listing prices by visiting each ad, clicking past cookie dialog."""
import json, subprocess, time, re

def navigate(tab_id, url):
    payload = json.dumps({'url': url, 'userId': 'hermes-veille'})
    result = subprocess.run(['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/navigate',
                    '-H', 'Content-Type: application/json', '-d', payload],
                   capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout) if result.stdout else {}

def click_ref(tab_id, ref):
    payload = json.dumps({'userId': 'hermes-veille', 'ref': ref})
    result = subprocess.run(['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/click',
                    '-H', 'Content-Type: application/json', '-d', payload],
                   capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout) if result.stdout else {}

def get_snapshot(tab_id):
    result = subprocess.run(
        ['curl', '-s', f'http://127.0.0.1:9377/tabs/{tab_id}/snapshot?userId=hermes-veille'],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout)
    except:
        return {}

def get_body(tab_id, max_len=8000):
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

# Orpi candidates in accepted quartiers only
candidates = [
    {"id": "orpi-fe039240-8ac", "pieces": 3, "surf": 56, "quartier": "Centre-ville", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-fe039240-8ac"},
    {"id": "orpi-b3dd06ab-75f", "pieces": 2, "surf": 40, "quartier": "Saint-François - Les Docks", "url": "https://www.orpi.com/annonce-location-appartement-t2-le-havre-76600-b3dd06ab-75f"},
    {"id": "orpi-5bdf2d74-8e5", "pieces": 3, "surf": 78, "quartier": "Coty", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-5bdf2d74-8e5"},
    {"id": "orpi-d94480cc-dfe", "pieces": 3, "surf": 59, "quartier": "Rond point - Observatoire", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-d94480cc-dfe"},
    {"id": "orpi-4c1c8618-f31", "pieces": 3, "surf": 58, "quartier": "Centre-ville", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-4c1c8618-f31"},
    {"id": "orpi-3ccc38ca-99e", "pieces": 3, "surf": 61, "quartier": "Saint-François - Les Docks", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-3ccc38ca-99e"},
    {"id": "orpi-45580ff2-c2c", "pieces": 2, "surf": 49, "quartier": "Centre-ville", "url": "https://www.orpi.com/annonce-location-appartement-t2-le-havre-76600-45580ff2-c2c"},
]

qualifying = []

for c in candidates:
    print(f"\n--- Checking {c['id']} ---")
    nav_result = navigate(tab_id, c['url'])
    time.sleep(4)
    
    # Click "Continuer sans accepter" to dismiss cookie dialog
    snap = get_snapshot(tab_id)
    snap_text = snap.get('snapshot', '')
    if 'Continuer sans accepter' in snap_text:
        # Find the ref
        m = re.search(r'button "Continuer sans accepter" \[e(\d+)\]', snap_text)
        if m:
            ref = m.group(1)
            click_ref(tab_id, ref)
            time.sleep(2)
    
    # Now get body text
    body = get_body(tab_id, 8000)
    
    # Find price - look for patterns like "XXX €" or "Loyer : XXX €"
    prices = re.findall(r'(\d+)\s*€', body)
    prix = 0
    if prices:
        # Usually the loyer is one of the first prices mentioned
        # Try to find "Loyer" context
        lm = re.search(r'[Ll]oyer\s*:?\s*(\d+)\s*€', body)
        if lm:
            prix = int(lm.group(1))
        else:
            # Take first reasonable price (not too high)
            for p in prices:
                p_int = int(p)
                if 100 < p_int < 5000:
                    prix = p_int
                    break
    
    body_lower = body.lower()
    cuisine_sep = any(k in body_lower for k in ['cuisine séparée', 'cuisine indépendante', 'cuisine fermée', 'cuisine: séparée'])
    cuisine_ouverte = any(k in body_lower for k in ['cuisine ouverte', 'cuisine américaine', 'cuisine équipée ouverte', 'cuisine aménagée ouverte', 'pièce de vie avec cuisine ouverte', 'séjour cuisine ouvert'])
    chambre = 'chambre' in body_lower
    
    print(f"  Prix: {prix}€ | Cuisine séparée: {cuisine_sep} | Cuisine ouverte: {cuisine_ouverte} | Chambre mentionnée: {chambre}")
    print(f"  Body (first 800): {body[:800]}")
    
    if prix > 0 and prix <= 500:
        qualifying.append({
            **c,
            'prix': prix,
            'cuisine_sep': cuisine_sep,
            'cuisine_ouverte': cuisine_ouverte,
            'chambre': chambre,
            'body_excerpt': body[:1500]
        })
        print(f"  ✅ QUALIFIES (prix <= 500)!")
    elif prix > 500:
        print(f"  ❌ Prix trop élevé: {prix}€")
    else:
        print(f"  ❌ Prix non trouvé")

print(f"\n=== QUALIFYING: {len(qualifying)} ===")
for q in qualifying:
    print(f"  {q['id']} | {q['prix']}€ | {q['pieces']}p | {q['surf']}m² | {q['quartier']}")

with open('/opt/data/cron/tmp/orpi_qualifying.json', 'w') as f:
    json.dump(qualifying, f, indent=2, ensure_ascii=False)