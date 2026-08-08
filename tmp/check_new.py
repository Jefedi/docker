#!/usr/bin/env python3
"""Check all sources for NEW T2+ ≤500€ ≥28m² candidates."""
import re, json, os

seen_file = '/opt/data/cron/output/havre-rental-seen.json'
with open(seen_file, 'r') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

all_new = []

# === Le-Partenaire pages 1-6 ===
for p in range(1, 7):
    if p == 1:
        filepath = '/tmp/rental/lp.html'
    else:
        filepath = f'/tmp/rental/lp_p{p}.html'
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = re.split(r'<div class="card w-100 mb-5 item-annonce">', content)
    for block in blocks[1:]:
        h2_match = re.search(r'à Le Havre (\d+)\s*&nbsp;pièces?\s*\|\s*(\d+)\s*&nbsp;m²', block)
        if not h2_match:
            continue
        pieces = int(h2_match.group(1))
        surface = int(h2_match.group(2))
        price_match = re.search(r'<span class="prix">([\d\s]+)&nbsp;€</span>', block)
        if not price_match:
            continue
        price = int(re.sub(r'\s', '', price_match.group(1)))
        url_match = re.search(r'href="/immobilier/location/appartement/havre/76600/\dpieces/(\d+)"', block)
        if not url_match:
            continue
        listing_id = url_match.group(1)
        desc_match = re.search(r'<p class="card-text crop-text-4"[^>]*>(.*?)</p>', block, re.DOTALL)
        desc = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip() if desc_match else ''
        desc = re.sub(r'\s+', ' ', desc)
        
        if pieces >= 2 and price <= 500 and surface >= 28:
            sid = f'lp-{listing_id}'
            is_new = sid not in seen_ids and listing_id not in seen_ids
            if is_new:
                all_new.append({
                    'source': 'lp', 'id': listing_id, 'pieces': pieces,
                    'surface': surface, 'price': price, 'description': desc,
                    'url': f'https://www.le-partenaire.fr/immobilier/location/appartement/havre/76600/{pieces}pieces/{listing_id}'
                })
                print(f'NEW LP: {sid} T{pieces} {surface}m² {price}€')
                print(f'  Desc: {desc[:300]}')
                print()

# === Citya ===
with open('/tmp/rental/citya.html', 'r') as f:
    content = f.read()
m = re.search(r'<script type="application/ld\+json">\s*(\{"@context.*?RealEstateListing.*?\})\s*</script>', content, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    for offer in data.get('offers', []):
        url = offer.get('url', '')
        price = offer.get('price', 0)
        name = offer.get('itemOffered', {}).get('name', '')
        np = re.search(r'(\d+)\s*pi\u00e8ces?\s*de\s*([\d.]+)m', name)
        if np:
            pieces = int(np.group(1))
            surface = float(np.group(2))
            listing_id = url.split('/')[-1]
            if pieces >= 2 and price <= 500 and surface >= 28:
                sid = f'citya-{listing_id}'
                is_new = sid not in seen_ids and listing_id not in seen_ids
                if is_new:
                    all_new.append({
                        'source': 'citya', 'id': listing_id, 'pieces': pieces,
                        'surface': surface, 'price': price, 'url': url, 'description': name
                    })
                    print(f'NEW CITYA: {sid} T{pieces} {surface}m² {price}€')

# === Orpi (pages 1-6) ===
for p in range(1, 7):
    if p == 1:
        filepath = '/tmp/rental/orpi.html'
    else:
        filepath = f'/tmp/rental/orpi_p{p}.html'
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r') as f:
        content = f.read()
    m = re.search(r'("@type":"ItemList".*?"itemListElement":\[.*?\])\}', content, re.DOTALL)
    if m:
        text = '{' + m.group(1) + '}'
        try:
            data = json.loads(text)
            for item in data.get('itemListElement', []):
                url = item.get('url', '')
                price = item.get('item', {}).get('offers', {}).get('price', 0)
                t_match = re.search(r'-t(\d+)-le-havre-76600-([a-f0-9-]+)/', url)
                if t_match:
                    pieces = int(t_match.group(1))
                    listing_id = t_match.group(2)
                    if pieces >= 2 and price <= 500:
                        sid = f'orpi-{listing_id}'
                        is_new = sid not in seen_ids and listing_id not in seen_ids
                        if is_new:
                            all_new.append({
                                'source': 'orpi', 'id': listing_id, 'pieces': pieces,
                                'surface': None, 'price': price, 'url': url, 'description': ''
                            })
                            print(f'NEW ORPI: {sid} T{pieces} {price}€ — {url}')
        except:
            pass

# === SquareHabitat (pages 1-2) ===
for filepath in ['/tmp/rental/sqhab.html', '/tmp/rental/sqhab_p2.html']:
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r') as f:
        content = f.read()
    m = re.search(r'<script id="ng-state" type="application/json">(.*?)</script>', content, re.DOTALL)
    if m:
        data = json.loads(m.group(1))
        for key in data:
            if 'apiBienUrl/bien' == key:
                biens = data[key].get('biens', [])
                for b in biens:
                    code_ref = b.get('codeRef', '')
                    nb_pieces = b.get('nbPieces', 0)
                    surface = b.get('surfaceHabitable', 0)
                    prix = b.get('prix', 0)
                    texte = b.get('texteAnnonce', '')
                    cp = b.get('codePostal', '')
                    if nb_pieces >= 2 and prix <= 500 and surface >= 28:
                        sid = f'sqhab-{code_ref}'
                        is_new = sid not in seen_ids
                        if is_new:
                            all_new.append({
                                'source': 'sqhab', 'id': code_ref, 'pieces': nb_pieces,
                                'surface': surface, 'price': prix, 'description': texte,
                                'url': f'https://www.squarehabitat.fr/annonces/location/bien/appartement/{code_ref}',
                                'cp': cp
                            })
                            print(f'NEW SQHAB: {sid} T{nb_pieces} {surface}m² {prix}€ CP={cp}')
                            print(f'  Texte: {texte[:400]}')
                            print()

# === Jullien-Allix ===
with open('/tmp/rental/ja.html', 'r') as f:
    content = f.read()
blocks = re.split(r'<div class="item-listing-wrap', content)
for block in blocks[1:]:
    price_match = re.search(r'<span class="price">(\d+)€</span>', block)
    link_match = re.search(r'href="(https://www\.jullien-allix\.fr/annonce-immobiliere/[^"]+)"', block)
    title_match = re.search(r'>(A Louer [^<]+|A louer [^<]+)</a>', block)
    if price_match and link_match:
        price = int(price_match.group(1))
        url = link_match.group(1)
        listing_id = url.split('/')[-1].replace('.html', '')
        title = title_match.group(1) if title_match else ''
        if 'F2' in title or 'T2' in title: pieces = 2
        elif 'F3' in title or 'T3' in title: pieces = 3
        elif 'F4' in title or 'T4' in title: pieces = 4
        elif 'F5' in title or 'T5' in title: pieces = 5
        elif 'F6' in title or 'T6' in title: pieces = 6
        else: pieces = 0
        if pieces >= 2 and price <= 500:
            sid = f'ja-{listing_id}'
            is_new = sid not in seen_ids and listing_id not in seen_ids
            if is_new:
                all_new.append({
                    'source': 'ja', 'id': listing_id, 'pieces': pieces,
                    'surface': None, 'price': price, 'url': url, 'description': title
                })
                print(f'NEW JA: {sid} T{pieces} {price}€ — {title}')

print(f'\n===== TOTAL NEW: {len(all_new)} =====')
for n in all_new:
    print(f"  {n['source']}-{n['id']}: T{n['pieces']} {n.get('surface','?')}m² {n['price']}€")