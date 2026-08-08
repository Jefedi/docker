import re, html as htmllib, json

raw = open('/opt/data/tmp/veille/orpi.html').read()
scripts = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.DOTALL)
data = json.loads(scripts[0].strip())
items = data['itemListElement']
print(f"Orpi items: {len(items)}")
for item in items:
    p = item.get('item', item)
    print(json.dumps(p, indent=2, ensure_ascii=False)[:500])
    print("---")