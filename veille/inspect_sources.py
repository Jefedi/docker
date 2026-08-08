import re, html, json, sys, os

def clean_html(filename):
    with open(filename, encoding='utf-8', errors='replace') as f:
        content = f.read()
    content_clean = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content_clean = re.sub(r'<style[^>]*>.*?</style>', '', content_clean, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', content_clean)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Parse each source
sources = {
    'sqhab': '/tmp/veille/sqhab.html',
    'citya': '/tmp/veille/citya.html',
    'c21': '/tmp/veille/c21.html',
    'orpi': '/tmp/veille/orpi.html',
    'lhimmo': '/tmp/veille/lhimmo.html',
    'stroch': '/tmp/veille/stroch.html',
    'heuze': '/tmp/veille/heuze.html',
    'ja': '/tmp/veille/ja.html',
    'pap': '/tmp/veille/pap.html',
    'bienici': '/tmp/veille/bienici.html',
}

for name, fn in sources.items():
    if not os.path.exists(fn):
        print(f"\n=== {name}: FILE NOT FOUND ===")
        continue
    text = clean_html(fn)
    print(f"\n=== {name} ({len(text)} chars) ===")
    # Just show first 3000 chars to inspect structure
    print(text[:3000])
    print("...")