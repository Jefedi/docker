import re, html as htmllib, json

raw = open('/opt/data/tmp/veille/c21.html').read()

# Look for all JSON-LD blocks
scripts = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.DOTALL)
print(f"JSON-LD scripts: {len(scripts)}")
for i, s in enumerate(scripts):
    try:
        data = json.loads(s.strip())
        print(f"  Script {i}: type={data.get('@type','')} keys={list(data.keys())[:10]}")
        if 'itemListElement' in data:
            items = data['itemListElement']
            print(f"    Items: {len(items)}")
            for item in items[:5]:
                p = item.get('item', item)
                print(f"    name={p.get('name','')[:60]} price={p.get('offers',{}).get('price','') if isinstance(p.get('offers'), dict) else ''}")
    except:
        print(f"  Script {i}: parse failed, {s[:200]}")

# Also look for data in any script
all_scripts = re.findall(r'<script[^>]*>(.*?)</script>', raw, re.DOTALL)
for i, s in enumerate(all_scripts):
    if '"price"' in s and len(s) > 200:
        print(f"\n  Script {i} has price, len={len(s)}")
        # Try to find price patterns
        price_matches = re.findall(r'"price"\s*:\s*"?(\d+)"?', s)
        print(f"    Prices: {price_matches[:20]}")

# Look for listing card data in the HTML
# Century21 uses Tailwind classes (tw-). Find cards with data
cards = re.findall(r'class="[^"]*tw-[^"]*"[^>]*>.*?(?=class="[^"]*tw-)', raw[:50000], re.DOTALL)
print(f"\nCards: {len(cards)}")

# Find all data attributes with listing info
data_attrs = re.findall(r'data-(?:price|surface|pieces|rooms|type)="([^"]*)"', raw)
print(f"Data attrs: {len(data_attrs)}")
for d in data_attrs[:20]:
    print(f"  {d}")