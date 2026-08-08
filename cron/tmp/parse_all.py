import re, html, json, os, glob

sources = {
    'pap': '/tmp/src_b0d3af2a.html',
    'c21': '/tmp/src_cfdcccb9.html',
    'orpi': '/tmp/src_a559eead.html',
    'ja': '/tmp/src_b82d1c6c.html',
    'lhimmo': '/tmp/src_2e98521d.html',
    'stroch': '/tmp/src_e842bf55.html',
    'heuze': '/tmp/src_b330aec7.html',
    'citya': '/tmp/src_7d2dca6d.html',
    'foncia': '/tmp/src_8e80d1f0.html',
    'sqhab': '/tmp/src_a8dd5e22.html',
    'bienici': '/tmp/src_49afa3e7.html',
}

for name, path in sources.items():
    try:
        s = open(path).read()
    except:
        print(f"\n=== {name}: FILE NOT FOUND ===")
        continue
    print(f"\n=== {name} ({len(s)} bytes) ===")
    # Find all prices
    prices = re.findall(r'(\d[\d\s]{2,5})\s*€', s)
    print(f"  Prices: {len(prices)} -> {prices[:10]}")
    # Find all links with location/appartement or annonce
    links = re.findall(r'href="([^"]*(?:location|annonce|louer|appartement|bien)[^"]*)"', s, re.I)
    print(f"  Links: {len(links)} -> {links[:10]}")
    # Find headings
    h2s = re.findall(r'<h[23456][^>]*>(.*?)</h[23456]>', s, re.DOTALL)
    print(f"  Headings: {len(h2s)}")
    for h in h2s[:10]:
        t = html.unescape(re.sub('<[^>]+>','',h)).strip()
        if t: print(f"    {t[:120]}")
    # Look for JSON data
    for pattern in [r'"price"\s*:\s*(\d+)', r'"loyer"\s*:\s*(\d+)', r'"surface"\s*:\s*(\d+)', r'"pieces"\s*:\s*(\d+)']:
        matches = re.findall(pattern, s)
        if matches:
            print(f"  {pattern[:20]}: {matches[:10]}")