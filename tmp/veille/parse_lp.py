import re, json, glob, os

all_l = set()
for f in sorted(glob.glob('/opt/data/tmp/veille/lp_p*.html')) + ['/opt/data/tmp/veille/lp.html']:
    if not os.path.exists(f): continue
    html = open(f).read()
    links = re.findall(r'href="(/immobilier/location/appartement/(?:havre|le-havre)/76600/[^"]+)"', html)
    all_l.update(links)
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
    prices = re.findall(r'(\d[\d\s.]*\d)\s*€', html)
    print(f"{os.path.basename(f)}: links={len(links)}, h2s={len(h2s)}, prices={len(prices)}")
    for h in h2s[:3]:
        print("  h2:", re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h)).strip()[:100])

print(f"\nUnique links: {len(all_l)}")
for l in sorted(all_l)[:30]:
    print(l)