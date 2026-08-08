import re, html as htmllib

raw = open('/opt/data/tmp/veille/lp_p1.html').read()
html = htmllib.unescape(raw)
cards = re.split(r'class="card w-100 mb-5 item-annonce"', html)
print(f"Cards after unescape: {len(cards)}")
if len(cards) > 1:
    h2_m = re.search(r'<h2[^>]*>(.*?)</h2>', cards[1], re.DOTALL)
    if h2_m:
        h2_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h2_m.group(1))).strip()
        print(f"h2: '{h2_text}'")
        pm = re.search(r'(\d+)\s*pièces?', h2_text)
        print(f"pieces: {pm}")
        # Also try with \xa0
        pm2 = re.search(r'(\d+)[\s\xa0]*pièces?', h2_text)
        print(f"pieces with xa0: {pm2}")
        # Print repr
        print(f"repr: {repr(h2_text[:60])}")