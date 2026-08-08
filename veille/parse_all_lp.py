import re, html, json, sys

def parse_lp_page(filename):
    with open(filename, encoding='utf-8') as f:
        content = f.read()
    
    hrefs = re.findall(r'href="(/immobilier/location/appartement/[^"]+)"', content)
    listing_hrefs = [h for h in hrefs if h.count('/') > 5 and 'page' not in h.lower()]
    seen = set()
    unique = []
    for h in listing_hrefs:
        if h not in seen:
            seen.add(h)
            unique.append(h)
    
    content_clean = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content_clean = re.sub(r'<style[^>]*>.*?</style>', '', content_clean, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', content_clean)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    blocks = text.split("Voir l'annonce")
    
    listings = []
    for i, block in enumerate(blocks[:-1]):
        m = re.search(r'(\d+)\s*pi[èe]ces?\s*\|\s*(\d+)\s*m[²2]', block)
        if not m:
            continue
        pieces = int(m.group(1))
        surface = int(m.group(2))
        
        price_match = re.search(r'(\d+)\s+([\d ]+)\s*€\s*/\s*mois', block)
        if price_match:
            price = int(price_match.group(2).replace(' ', ''))
        else:
            pm = re.findall(r'(\d+)\s*€\s*/\s*mois', block)
            if not pm:
                continue
            price = int(pm[-1].replace(' ', ''))
        
        href_id = unique[i] if i < len(unique) else None
        
        bl = block.lower()
        has_cuisine_sep = 'cuisine indépendante' in bl or 'cuisine independante' in bl
        has_cuisine_ouverte = 'cuisine ouverte' in bl or 'cuisine américaine' in bl or 'kitchenette' in bl
        has_cuisine_eq = 'cuisine équipée' in bl or 'cuisine aménagée' in bl
        has_chambre = bool(re.search(r'\d+\s*chambre', bl)) or 'chambre avec' in bl or 'chambre fermée' in bl
        has_coin_nuit = 'coin nuit' in bl or 'canapé-lit' in bl or 'canapé lit' in bl
        
        quartier = 'unknown'
        qm = re.search(r'[Qq]uartier\s+([A-Z][a-zA-Z\- ]+?)[,\.\n]', block)
        if qm:
            quartier = qm.group(1).strip()
        
        dpe = 'unknown'
        dm = re.search(r'DPE\s*([A-G])\s', block) or re.search(r'Classe\s*([A-G])\s*[-–]\s*\d+\s*kWh', block)
        if dm:
            dpe = dm.group(1)
        
        date = 'unknown'
        dtm = re.search(r'Date de cr[ée]ation:\s*(\d{2}/\d{2}/\d{4})', block)
        if dtm:
            date = dtm.group(1)
        
        desc_start = block.find('€ / mois')
        if desc_start > 0:
            desc = block[desc_start:desc_start+800].strip()
        else:
            desc = block[-800:].strip()
        
        listings.append({
            'pieces': pieces,
            'surface': surface,
            'price': price,
            'href': href_id,
            'date': date,
            'quartier': quartier,
            'dpe': dpe,
            'cuisine_sep': has_cuisine_sep,
            'cuisine_ouverte': has_cuisine_ouverte,
            'cuisine_eq': has_cuisine_eq,
            'chambre': has_chambre,
            'coin_nuit': has_coin_nuit,
            'desc': desc[:600]
        })
    return listings

all_listings = []
for p in range(1, 9):
    fn = f'/tmp/veille/lp_page{p}.html' if p > 1 else '/tmp/veille/lp.html'
    try:
        listings = parse_lp_page(fn)
        all_listings.extend(listings)
    except Exception as e:
        print(f"Error page {p}: {e}", file=sys.stderr)

# Filter: T2+ (pieces >= 2), price <= 500, surface >= 28
# AND cuisine séparée (not ouverte/kitchenette)
# AND chambre fermée (not coin nuit)
qualifying = []
for l in all_listings:
    if l['pieces'] < 2:
        continue
    if l['price'] > 500:
        continue
    if l['surface'] < 28:
        continue
    # Cuisine: must be séparée, not ouverte/kitchenette
    if l['cuisine_ouverte'] and not l['cuisine_sep']:
        continue
    # Chambre fermée: must have chambre, not just coin nuit
    if l['coin_nuit'] and not l['chambre']:
        continue
    
    qualifying.append(l)

print(f"\n=== ALL LISTINGS ({len(all_listings)}) ===")
for l in all_listings:
    print(f"  {l['pieces']}p {l['surface']}m² {l['price']}€ | cs={l['cuisine_sep']} co={l['cuisine_ouverte']} ch={l['chambre']} cn={l['coin_nuit']} | {l['href']}")

print(f"\n=== QUALIFYING ({len(qualifying)}) ===")
for l in qualifying:
    print(json.dumps(l, ensure_ascii=False, indent=2))
    print()