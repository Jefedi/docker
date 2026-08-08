import re, html, os

all_t2 = []
for p in ['', '_p2', '_p3', '_p4', '_p5', '_p6']:
    filepath = f'/tmp/lp_rent{p}.html'
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    h2_positions = [(m.start(), m.end()) for m in re.finditer(r'<h2[^>]*>.*?</h2>', content, re.DOTALL)]
    for i, (start, end) in enumerate(h2_positions):
        block_start = start
        block_end = h2_positions[i+1][0] if i+1 < len(h2_positions) else len(content)
        block = content[block_start:block_end]
        h2_text = re.sub(r'<[^>]+>', '', content[start:end]).strip()
        h2_text = html.unescape(h2_text)
        h2_text = re.sub(r'\s+', ' ', h2_text)
        
        pieces_match = re.search(r'(\d+)\s*pi[eè]ces?', h2_text)
        pieces = int(pieces_match.group(1)) if pieces_match else None
        surface_match = re.search(r'(\d+)\s*m²', h2_text)
        surface = int(surface_match.group(1)) if surface_match else None
        
        link_match = re.search(r'href="(/immobilier/location/appartement/havre/76600/\d+pieces/\d+)"', block)
        lid = link_match.group(1).split('/')[-1] if link_match else ''
        
        if pieces == 2 and surface and surface >= 28:
            desc_text = re.sub(r'<[^>]+>', ' ', block)
            desc_text = html.unescape(desc_text)
            desc_text = re.sub(r'\s+', ' ', desc_text).strip()
            
            m = re.search(r'(\d{3,4})\s*€\s*mensuel', desc_text, re.IGNORECASE)
            real_price = m.group(1) if m else '?'
            
            print(f'ID: {lid} | T2 | {surface}m2 | real_price={real_price}EUR')
            print(f'  desc_start: {desc_text[:200]}')
            print()