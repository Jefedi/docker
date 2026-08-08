import re, html as htmllib, json

# Parse SquareHabitat
raw = open('/opt/data/tmp/veille/sqhab.html').read()
page = htmllib.unescape(raw)

# Look for JSON-LD
scripts = re.findall(r'<script[^>]*>(.*?)</script>', raw, re.DOTALL)
for i, s in enumerate(scripts):
    if 'OfferCatalog' in s or 'RealEstateListing' in s or '"offers"' in s.lower():
        print(f"Script {i} has listing data, len={len(s)}")
        try:
            data = json.loads(s.strip())
            offers = data.get('offers', [])
            print(f"  Offers: {len(offers)}")
            for o in offers[:5]:
                print(f"  {o.get('name','')[:60]} | {o.get('price','')}€ | {o.get('url','')[:80]}")
        except:
            print(f"  Parse failed, preview: {s[:300]}")

# Also look for listing cards/links
links = re.findall(r'href="(/annonces/location/[^"]+)"', page)
print(f"\nLinks: {len(links)}")
for l in list(set(links))[:20]:
    print(f"  {l}")

# Look for price/pieces in text
pieces_prices = re.findall(r'(\d+)\s*pièces?\s*.*?(\d+)\s*€', page[:50000])
print(f"\nPieces+prices: {len(pieces_prices)}")

# Try to find listing data in any other format
jsons = re.findall(r'\{[^{}]*"(?:price|loyer|surface)"[^{}]*\}', raw)
print(f"\nJSON blobs: {len(jsons)}")
for j in jsons[:5]:
    print(f"  {j[:200]}")