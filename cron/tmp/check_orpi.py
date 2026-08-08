#!/usr/bin/env python3
"""Check Orpi listing prices by visiting each ad."""
import json, subprocess, time, re

def navigate(tab_id, url):
    payload = json.dumps({'url': url, 'userId': 'hermes-veille'})
    subprocess.run(['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/navigate',
                    '-H', 'Content-Type: application/json', '-d', payload],
                   capture_output=True, text=True, timeout=30)

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

# Orpi candidates (Le Havre only, T2+, 28m²+)
candidates = [
    {"id": "orpi-fe039240-8ac", "pieces": 3, "surf": 56, "quartier": "Centre-ville", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-fe039240-8ac"},
    {"id": "orpi-b3dd06ab-75f", "pieces": 2, "surf": 40, "quartier": "Saint-François - Les Docks", "url": "https://www.orpi.com/annonce-location-appartement-t2-le-havre-76600-b3dd06ab-75f"},
    {"id": "orpi-5bdf2d74-8e5", "pieces": 3, "surf": 78, "quartier": "Coty", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-5bdf2d74-8e5"},
    {"id": "orpi-d94480cc-dfe", "pieces": 3, "surf": 59, "quartier": "Rond point - Observatoire", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-d94480cc-dfe"},
    {"id": "orpi-cab26761-0eb", "pieces": 4, "surf": 81, "quartier": "Les Ormeaux - Maréchal Joffre", "url": "https://www.orpi.com/annonce-location-appartement-t4-le-havre-76600-cab26761-0eb"},
    {"id": "orpi-aabc2df5-791", "pieces": 2, "surf": 42, "quartier": "Graville", "url": "https://www.orpi.com/annonce-location-appartement-t2-le-havre-76600-aabc2df5-791"},
    {"id": "orpi-4c1c8618-f31", "pieces": 3, "surf": 58, "quartier": "Centre-ville", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-4c1c8618-f31"},
    {"id": "orpi-3ccc38ca-99e", "pieces": 3, "surf": 61, "quartier": "Saint-François - Les Docks", "url": "https://www.orpi.com/annonce-location-appartement-t3-le-havre-76600-3ccc38ca-99e"},
    {"id": "orpi-45580ff2-c2c", "pieces": 2, "surf": 49, "quartier": "Centre-ville", "url": "https://www.orpi.com/annonce-location-appartement-t2-le-havre-76600-45580ff2-c2c"},
    {"id": "orpi-094f3534-529", "pieces": 2, "surf": 29, "quartier": "Sainte-Anne", "url": "https://www.orpi.com/annonce-location-appartement-t2-le-havre-76600-094f3534-529"},
]

# Accepted quartiers
accepted_quartiers = {
    'centre-ville', 'coty', 'massillon', 'eure', 'félix faure', 'felix faure',
    'perret', 'docks', 'rond point - observatoire', 'saint-françois - les docks',
    'saint-francois - les docks', 'danton', 'sanvic', 'bléville', 'bleville',
}

def is_accepted_quartier(q):
    qn = q.lower().strip()
    for aq in accepted_quartiers:
        if aq in qn or qn in aq:
            return True
    return False

qualifying = []

for c in candidates:
    print(f"\n--- Checking {c['id']} ---")
    navigate(tab_id, c['url'])
    time.sleep(4)
    body = get_body(tab_id, 6000)
    
    # Find price
    pm = re.search(r'(\d+)\s*€', body)
    prix = int(pm.group(1)) if pm else 0
    
    # Find details about cuisine, chambre
    body_lower = body.lower()
    cuisine_sep = 'cuisine séparée' in body_lower or 'cuisine indépendante' in body_lower or 'cuisine fermée' in body_lower
    cuisine_ouverte = 'cuisine ouverte' in body_lower or 'cuisine américaine' in body_lower or 'cuisine équipée ouverte' in body_lower
    chambre = 'chambre' in body_lower and not 'séjour chambre' in body_lower
    
    print(f"  Prix: {prix}€ | Cuisine séparée: {cuisine_sep} | Cuisine ouverte: {cuisine_ouverte} | Chambre: {chambre}")
    print(f"  Quartier: {c['quartier']} | Accepté: {is_accepted_quartier(c['quartier'])}")
    
    if prix > 0:
        print(f"  Body excerpt: {body[:500]}")
    
    if prix > 0 and prix <= 500 and c['pieces'] >= 2 and c['surf'] >= 28 and is_accepted_quartier(c['quartier']):
        qualifying.append({
            **c,
            'prix': prix,
            'cuisine_sep': cuisine_sep,
            'cuisine_ouverte': cuisine_ouverte,
            'chambre': chambre,
            'body_excerpt': body[:1000]
        })
        print(f"  ✅ QUALIFIES!")
    else:
        reasons = []
        if prix > 500:
            reasons.append(f"prix {prix}>500")
        if not is_accepted_quartier(c['quartier']):
            reasons.append(f"quartier non accepté")
        print(f"  ❌ Does not qualify: {', '.join(reasons)}")

print(f"\n=== QUALIFYING LISTINGS: {len(qualifying)} ===")
for q in qualifying:
    print(f"  {q['id']} | {q['prix']}€ | {q['pieces']}p | {q['surf']}m² | {q['quartier']}")
    print(f"    Cuisine: {'séparée' if q['cuisine_sep'] else 'ouverte' if q['cuisine_ouverte'] else 'non vérifié'}")
    print(f"    Chambre: {'oui' if q['chambre'] else 'non vérifié'}")
    print(f"    URL: {q['url']}")

with open('/opt/data/cron/tmp/orpi_qualifying.json', 'w') as f:
    json.dump(qualifying, f, indent=2, ensure_ascii=False)