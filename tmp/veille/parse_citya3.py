import re, html as htmllib, json

raw = open('/opt/data/tmp/veille/citya.html').read()
# Extract JSON-LD from script 8
ld_m = re.search(r'<script[^>]*>\s*(\{"@context".*?"OfferCatalog".*?\})\s*</script>', raw, re.DOTALL)
if not ld_m:
    # try broader
    ld_m = re.search(r'(\{"@context":"https:\\\\/\\\\/schema\.org".*?"OfferCatalog".*?\})\s*</script>', raw, re.DOTALL)

if ld_m:
    json_text = ld_m.group(1)
    try:
        data = json.loads(json_text)
        offers = data.get('offers', [])
        print(f"Offers: {len(offers)}")
        for o in offers[:30]:
            price = o.get('price', o.get('priceSpecification', {}).get('price', ''))
            name = o.get('name', '')
            url = o.get('url', '')
            desc = o.get('description', '')
            print(f"  {name[:60]} | {price}€ | url={url[:80]}")
            print(f"    desc: {desc[:120]}")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Text preview: {json_text[:500]}")
else:
    print("No JSON-LD found")
    # Try script 8 by index
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', raw, re.DOTALL)
    for i, s in enumerate(scripts):
        if 'OfferCatalog' in s or 'RealEstateListing' in s:
            print(f"Found in script {i}, len={len(s)}")
            # Try to parse
            s2 = s.strip()
            try:
                data = json.loads(s2)
                offers = data.get('offers', [])
                print(f"Offers: {len(offers)}")
                for o in offers[:30]:
                    price = o.get('price', '')
                    name = o.get('name', '')
                    url = o.get('url', '')
                    desc = o.get('description', '')
                    print(f"  {name[:60]} | {price}€ | url={url[:80]}")
                    print(f"    desc: {desc[:120]}")
            except:
                print(f"Parse failed, preview: {s2[:300]}")