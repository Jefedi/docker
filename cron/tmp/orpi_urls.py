import re, json
s = open('/tmp/src_a559eead.html').read()
urls = re.findall(r'href="(/location-immobiliere/[^"]+)"', s)
unique = list(set(urls))
for u in sorted(unique):
    print(u)
# also look for listing-specific patterns - Orpi uses annonce URLs
urls2 = re.findall(r'href="(/annonces-immobilieres/[^"]+)"', s)
for u in sorted(set(urls2)):
    print(u)
# Try to find listing card structure
# Look for data attributes
cards = re.findall(r'data-(?:id|uuid|ref)="([^"]+)"', s)
print(f"\nData IDs: {cards[:20]}")
# Look for JSON-LD
ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.DOTALL)
print(f"\nJSON-LD blocks: {len(ld)}")
for b in ld[:3]:
    print(b[:300])