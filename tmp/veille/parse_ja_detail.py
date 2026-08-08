import re, html as htmllib, json, glob

ja_files = sorted(glob.glob('/opt/data/tmp/veille/ja_f2_*.html'))
listings = []
for f in ja_files:
    raw = open(f).read()
    page = htmllib.unescape(raw)
    
    # Title
    title_m = re.search(r'<title>([^<]+)</title>', raw)
    title = title_m.group(1).strip() if title_m else ''
    
    # Price - look for loyer or € pattern
    loyer_m = re.search(r'loyer[^0-9]*(\d+)', page, re.IGNORECASE)
    price = 0
    if loyer_m:
        price = int(loyer_m.group(1))
    if not price:
        # Try "€" near "mois" or "CC"
        price_m = re.search(r'(\d{3,4})\s*€\s*(?:/|par|mois|CC|HC)', page)
        if price_m:
            price = int(price_m.group(1))
    if not price:
        price_m = re.search(r'(\d{3,4})\s*€', raw)
        if price_m:
            p = price_m.group(1)
            if p != '000' and int(p) > 100:
                price = int(p)
    
    # Surface
    surf_m = re.search(r'(\d+[,.]?\d*)\s*m²', page)
    surface = 0
    if surf_m:
        s = surf_m.group(1).replace(',', '.')
        try: surface = int(float(s))
        except: pass
    
    # Cuisine
    cuisine_sep = 'cuisine indépendante' in page.lower() or 'cuisine séparée' in page.lower() or 'cuisine fermée' in page.lower()
    cuisine_ouverte = 'cuisine ouverte' in page.lower() or 'cuisine américaine' in page.lower() or 'cuisine équipée ouverte' in page.lower()
    
    # Chambre
    chambre = 'chambre' in page.lower()
    
    # Description
    desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', raw, re.IGNORECASE)
    desc = desc_m.group(1) if desc_m else ''
    
    # URL from filename
    url = ''
    url_m = re.search(r'href="(https://www\.jullien-allix\.fr/annonce-immobiliere/a-louer-appartement[^"]+)"', page)
    if url_m:
        url = url_m.group(1)
    
    # Extract slug from URL or title
    slug = ''
    slug_m = re.search(r'a-louer-(appartement[^.]+)', title.lower())
    
    print(f"\n=== {f} ===")
    print(f"Title: {title[:80]}")
    print(f"Price: {price}€")
    print(f"Surface: {surface}m²")
    print(f"Cuisine séparée: {cuisine_sep} | Cuisine ouverte: {cuisine_ouverte}")
    print(f"Chambre: {chambre}")
    print(f"Desc: {desc[:200]}")
    
    listings.append({
        'file': f,
        'title': title,
        'price': price,
        'surface': surface,
        'cuisine_sep': cuisine_sep,
        'cuisine_ouverte': cuisine_ouverte,
        'chambre': chambre,
        'desc': desc,
    })

with open('/opt/data/tmp/veille/ja_listings.json', 'w') as f:
    json.dump(listings, f, indent=2)