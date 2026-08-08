#!/usr/bin/env python3
"""Parse rental listings from multiple sources for Le Havre T2+ ≤500€."""
import re, json, os

def parse_le_partenaire(filepath):
    listings = []
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
        listings.append({
            'source': 'lp', 'id': listing_id, 'pieces': pieces, 'surface': surface,
            'price': price, 'description': desc[:600],
            'url': f'https://www.le-partenaire.fr/immobilier/location/appartement/havre/76600/{pieces}pieces/{listing_id}'
        })
    return listings

def parse_citya(filepath):
    listings = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'\{"@context":"https:\\/\\/schema\.org","@type":\["RealEstateListing","OfferCatalog"\].*?\]\}</script>', content, re.DOTALL)
    if m:
        try:
            text = m.group(0).replace('</script>', '')
            data = json.loads(text)
            for offer in data.get('offers', []):
                url = offer.get('url', '')
                price = offer.get('price', 0)
                name = offer.get('itemOffered', {}).get('name', '')
                np = re.search(r'(\d+)\s*pi\u00e8ces?\s*de\s*([\d.]+)m', name)
                if np:
                    pieces = int(np.group(1))
                    surface = float(np.group(2))
                    listing_id = url.split('/')[-1]
                    listings.append({
                        'source': 'citya', 'id': listing_id, 'pieces': pieces,
                        'surface': surface, 'price': price, 'url': url, 'description': name
                    })
        except json.JSONDecodeError as e:
            print(f"Citya JSON parse error: {e}")
    return listings

def parse_orpi(filepath):
    listings = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Extract URLs with T-type and price from JSON-LD
    m = re.search(r'"itemListElement":\[(.*?)\]\}</script>', content, re.DOTALL)
    if m:
        text = '{"itemListElement":[' + m.group(1) + ']}'
        try:
            data = json.loads(text)
            for item in data.get('itemListElement', []):
                url = item.get('url', '')
                product = item.get('item', {})
                price = product.get('offers', {}).get('price', 0)
                t_match = re.search(r'-t(\d+)-le-havre-76600-([a-f0-9-]+)/', url)
                if t_match:
                    pieces = int(t_match.group(1))
                    listing_id = t_match.group(2)
                    listings.append({
                        'source': 'orpi', 'id': listing_id, 'pieces': pieces,
                        'surface': None, 'price': price, 'url': url, 'description': ''
                    })
        except json.JSONDecodeError as e:
            print(f"Orpi JSON parse error: {e}")
    return listings

def parse_squarehabitat(filepath):
    listings = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'"@type":"ItemList".*?"itemListElement":\[(.*?)\]\}</script>', content, re.DOTALL)
    if m:
        text = '{"@context":"https://schema.org",' + m.group(0) + '}'
        try:
            data = json.loads(text)
            for item in data.get('itemListElement', []):
                product = item.get('item', {})
                name = product.get('name', '')
                price = product.get('offers', {}).get('price', 0)
                if 'Studio' in name:
                    pieces = 1
                else:
                    p = re.search(r'(\d+)\s*pièces', name)
                    pieces = int(p.group(1)) if p else 0
                listings.append({
                    'source': 'sqhab', 'id': f'pos-{item.get("position", 0)}',
                    'pieces': pieces, 'surface': None, 'price': price,
                    'url': '', 'description': name
                })
        except json.JSONDecodeError as e:
            print(f"SquareHabitat JSON parse error: {e}")
    return listings

def parse_jullien_allix(filepath):
    listings = []
    with open(filepath, 'r', encoding='utf-8') as f:
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
            if 'F2' in title or 'T2' in title:
                pieces = 2
            elif 'F3' in title or 'T3' in title:
                pieces = 3
            elif 'F4' in title or 'T4' in title:
                pieces = 4
            elif 'F5' in title or 'T5' in title:
                pieces = 5
            elif 'F6' in title or 'T6' in title:
                pieces = 6
            else:
                pieces = 0
            surface_match = re.search(r'([\d.]+)\s*</span>', block)
            surface = None
            if surface_match:
                try: surface = float(surface_match.group(1))
                except: pass
            listings.append({
                'source': 'ja', 'id': listing_id, 'pieces': pieces,
                'surface': surface, 'price': price, 'url': url, 'description': title
            })
    return listings

# ====== MAIN ======
all_listings = []

for p in range(1, 7):
    if p == 1:
        filepath = '/tmp/rental/lp.html'
    else:
        filepath = f'/tmp/rental/lp_p{p}.html'
    if os.path.exists(filepath):
        listings = parse_le_partenaire(filepath)
        print(f"Le-Partenaire page {p}: {len(listings)} listings")
        all_listings.extend(listings)

citya_listings = parse_citya('/tmp/rental/citya.html')
print(f"Citya: {len(citya_listings)} listings")
all_listings.extend(citya_listings)

orpi_listings = parse_orpi('/tmp/rental/orpi.html')
print(f"Orpi: {len(orpi_listings)} listings")
all_listings.extend(orpi_listings)

sqhab_listings = parse_squarehabitat('/tmp/rental/sqhab.html')
print(f"SquareHabitat: {len(sqhab_listings)} listings")
all_listings.extend(sqhab_listings)

ja_listings = parse_jullien_allix('/tmp/rental/ja.html')
print(f"Jullien-Allix: {len(ja_listings)} listings")
all_listings.extend(ja_listings)

print("\n===== T2+ ≤500€ =====")
candidates = []
for l in all_listings:
    if l['pieces'] >= 2 and l['price'] <= 500:
        if l['surface'] is not None and l['surface'] < 28:
            continue
        candidates.append(l)
        print(f"  {l['source']}-{l['id']}: T{l['pieces']} {l.get('surface','?')}m² {l['price']}€ — {l.get('description','')[:100]}")

print(f"\nTotal candidates (T2+ ≤500€): {len(candidates)}")

# Dedup
seen_file = '/opt/data/cron/output/havre-rental-seen.json'
with open(seen_file, 'r') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

print("\n===== NEW (not in seen) =====")
new_candidates = []
for c in candidates:
    prefixed_id = f"{c['source']}-{c['id']}"
    if prefixed_id not in seen_ids and c['id'] not in seen_ids:
        new_candidates.append(c)
        print(f"  NEW: {prefixed_id}: T{c['pieces']} {c.get('surface','?')}m² {c['price']}€ — {c.get('description','')[:120]}")

print(f"\nTotal NEW candidates: {len(new_candidates)}")