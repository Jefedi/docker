import re, html as htmllib, glob, os

f = '/opt/data/tmp/veille/lp_p1.html'
raw = open(f).read()
page = htmllib.unescape(raw)
cards = re.split(r'class="card w-100 mb-5 item-annonce"', page)
print(f"Cards: {len(cards)}")
for i, card in enumerate(cards[1:6]):
    h2_m = re.search(r'<h2[^>]*>(.*?)</h2>', card, re.DOTALL)
    if not h2_m:
        print(f"  card {i}: NO H2")
        continue
    h2_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h2_m.group(1))).strip()
    pm = re.search(r'(\d+)\s*pièces?', h2_text)
    pieces = int(pm.group(1)) if pm else 0
    link_m = re.search(r'href="(/immobilier/location/appartement/(?:havre|le-havre)/76600/[^"]+)"', card)
    print(f"  card {i}: h2='{h2_text[:50]}' pieces={pieces} link={'YES' if link_m else 'NO'}")
    if link_m:
        id_m = re.search(r'/(\d+)(?:\?|$|"|/)', link_m.group(1))
        print(f"    id={id_m.group(1) if id_m else 'NONE'}")