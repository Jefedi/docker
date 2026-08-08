import re
import html as h

html_content = open('/tmp/veille/lhimmo_annonces.html').read()
for pos_match in re.finditer(r'(\d+)\s*€\s*/mois', html_content):
    pos = pos_match.start()
    price = pos_match.group(1)
    chunk = html_content[max(0,pos-3000):pos+2000]
    link_m = re.search(r'href="(https://www[^\"]+/annonce/[^\"]+)"', chunk)
    link = link_m.group(1) if link_m else 'NO LINK'
    
    text = re.sub(r'<[^>]+>', ' ', chunk)
    text = h.unescape(re.sub(r'\s+', ' ', text)).strip()
    
    surf_m = re.search(r'(\d+)\s*m2', text, re.I)
    surface = surf_m.group(1) if surf_m else '?'
    
    print(f'PRICE={price} | surface={surface} | LINK={link}')
    print(f'  TEXT: {text[:500]}')
    print()