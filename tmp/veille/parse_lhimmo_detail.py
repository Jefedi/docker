import re, html as htmllib, json

sources = {
    'lhimmo_t2_danton': '/opt/data/tmp/veille/lhimmo_t2_danton.html',
    'lhimmo_t2_univ': '/opt/data/tmp/veille/lhimmo_t2_univ.html',
}

for name, path in sources.items():
    raw = open(path).read()
    page = htmllib.unescape(raw)
    
    # Look for price
    prices = re.findall(r'(\d{3,4})\s*€', raw)
    # Look for surface
    surfaces = re.findall(r'(\d+[,.]?\d*)\s*m²', page)
    # Look for "location" / "loyer"
    loyer = re.findall(r'loyer[^0-9]*(\d+)', page, re.IGNORECASE)
    # Look for description
    desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', raw, re.IGNORECASE)
    desc = desc_m.group(1) if desc_m else ''
    # Title
    title_m = re.search(r'<title>([^<]+)</title>', raw)
    title = title_m.group(1).strip() if title_m else ''
    
    print(f"\n=== {name} ===")
    print(f"Title: {title}")
    print(f"Prices: {prices[:10]}")
    print(f"Surfaces: {surfaces[:10]}")
    print(f"Loyer: {loyer[:5]}")
    print(f"Desc: {desc[:300]}")
    
    # Look for "cuisine" in page
    cuisine = re.findall(r'cuisine[^<.]{0,60}', page, re.IGNORECASE)
    print(f"Cuisine: {cuisine[:5]}")
    
    # Look for "chambre"
    chambre = re.findall(r'chambre[^<.]{0,60}', page, re.IGNORECASE)
    print(f"Chambre: {chambre[:5]}")