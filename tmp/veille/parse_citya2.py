import re, html as htmllib

raw = open('/opt/data/tmp/veille/citya.html').read()
# Look for listing IDs or references
refs = re.findall(r'(GES\d+-\d+)', raw)
print(f"Refs: {len(refs)}")
for r in set(refs):
    print(f"  {r}")

# Look for apartment titles
t2s = re.findall(r'T[23][^<]{0,80}', raw)
print(f"\nT2/T3 mentions: {len(t2s)}")
for t in t2s[:10]:
    print(f"  {t.strip()[:100]}")

# Look for prices
prices = re.findall(r'(\d{3,4})\s*€', raw)
print(f"\nPrices: {len(prices)}")
for p in prices[:20]:
    print(f"  {p}")

# Check for script tags with data
scripts = re.findall(r'<script[^>]*>(.*?)</script>', raw, re.DOTALL)
print(f"\nScripts: {len(scripts)}")
for i, s in enumerate(scripts):
    if len(s) > 100:
        print(f"  script {i}: {len(s)} chars, preview: {s[:200].strip()}")