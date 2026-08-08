import re, html as htmllib, json, glob, os

BASE = "https://www.le-partenaire.fr"
listings = []
seen_ids = set()

for f in sorted(set(glob.glob('/opt/data/tmp/veille/lp_p*.html') + ['/opt/data/tmp/veille/lp.html'])):
    if not os.path.exists(f): continue
    raw = open(f).read()
    page = htmllib.unescape(raw)
    cards = re.split(r'class="card w-100 mb-5 item-annonce"', page)
    for card in cards[1:]:
        h2_m = re.search(r'<h2[^>]*>(.*?)</h2>', card, re.DOTALL)
        if not h2_m: continue
        h2_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h2_m.group(1))).strip()
        pm = re.search(r'(\d+)\s*pièces?', h2_text)
        sm = re.search(r'(\d+)\s*m²', h2_text)
        pieces = int(pm.group(1)) if pm else 0
        surface = int(sm.group(1)) if sm else 0
        
        link_m = re.search(r'href="(/immobilier/location/appartement/(?:havre|le-havre)/76600/[^"]+)"', card)
        if not link_m: continue
        link = link_m.group(1)
        # Extract the LAST number in the URL path as the listing ID
        nums = re.findall(r'/(\d+)(?:/|$)', link)
        listing_id = nums[-1] if nums else ''
        if not listing_id or listing_id == '76600':
            # try to get the very last numeric segment
            seg_m = re.search(r'/(\d+)\s*$', link.rstrip('/'))
            if seg_m: listing_id = seg_m.group(1)
            else: continue
        
        if listing_id in seen_ids: continue
        seen_ids.add(listing_id)
        
        price = 0
        price_m = re.search(r'<span class="prix">([\d\s.]+)€</span>', card)
        if price_m:
            ps = price_m.group(1).replace(' ', '').replace('.', '')
            try: price = int(ps)
            except: pass
        if not price:
            price_m2 = re.search(r'(\d[\d\s.]*)€\s*/\s*mois', card)
            if price_m2:
                ps = price_m2.group(1).replace(' ', '').replace('.', '')
                try: price = int(ps)
                except: pass
        
        desc_m = re.search(r'<p class="card-text[^"]*"[^>]*>(.*?)</p>', card, re.DOTALL)
        desc = ""
        if desc_m:
            desc = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', desc_m.group(1))).strip()
        
        dpe_m = re.search(r'DPE\s+([A-G])', desc)
        dpe = dpe_m.group(1) if dpe_m else ''
        
        full_url = BASE + link
        
        if pieces >= 2:
            listings.append({
                'id': f"lp-{listing_id}",
                'url': full_url,
                'pieces': pieces,
                'surface': surface,
                'price': price,
                'dpe': dpe,
                'desc': desc[:600],
            })

print(f"Le-Partenaire T2+ (all prices): {len(listings)}")
for l in listings:
    match = " *** MATCH ***" if (l['pieces']>=2 and l['surface']>=28 and 0<l['price']<=500) else ""
    print(f"  {l['id']} | T{l['pieces']} {l['surface']}m² | {l['price']}€ | DPE={l['dpe']}{match}")
    print(f"    {l['desc'][:120]}")

with open('/opt/data/tmp/veille/lp_listings_all.json', 'w') as f:
    json.dump(listings, f, indent=2)