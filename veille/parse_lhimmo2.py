import re, html as h

html_content = open('/tmp/veille/lhimmo_annonces.html').read()
for pos_match in re.finditer(r'(\d+)\s*€\s*/mois', html_content):
    pos = pos_match.start()
    price = pos_match.group(1)
    chunk = html_content[max(0,pos-3000):pos+2000]
    text = re.sub(r'<[^>]+>', ' ', chunk)
    text = h.unescape(re.sub(r'\s+', ' ', text)).strip()
    link_m = re.search(r'href="(https://www\.lhimmo\.com/annonce/[^"]+)"', chunk)
    link = link_m.group(1) if link_m else 'NO LINK'
    surf_m = re.search(r'(\d+)\s*m[²2]', text)
    surface = surf_m.group(1) if surf_m else '?'
    print(f'PRICE={price}€ | surface={surface}m²')
    print(f'  LINK: {link}')
    print(f'  TEXT: {text[:400]}')
    print()