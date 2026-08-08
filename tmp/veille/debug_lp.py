import re
html = open('/opt/data/tmp/veille/lp_p1.html').read()
cards = re.split(r'class="card w-100 mb-5 item-annonce"', html)
print(f"Cards: {len(cards)}")
for i, card in enumerate(cards[1:6]):
    h2_m = re.search(r'<h2[^>]*>(.*?)</h2>', card, re.DOTALL)
    if not h2_m: 
        print(f"  card {i}: no h2")
        continue
    h2_raw = h2_m.group(1)
    h2_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h2_raw)).strip()
    print(f"  card {i}: h2='{h2_text}'")
    # Check pieces with &nbsp;
    pm = re.search(r'(\d+)\s*&?nbsp;?\s*pièces?', h2_text)
    print(f"    pieces match: {pm}")