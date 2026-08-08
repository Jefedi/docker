import re, html as htmlmod

content = open('/tmp/lp1.html').read()
# Let's extract each listing block more carefully
sections = re.split(r'(<h2)', content)
for i, sec in enumerate(sections[1:], 1):
    if i > 20:
        break
    full = '<h2' + sec[:5000]
    # Clean HTML
    text = re.sub(r'<[^>]+>', ' ', full)
    text = htmlmod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find link
    link_match = re.search(r'href="(/immobilier/location/appartement/havre/76600/[^"]+)"', full)
    link = link_match.group(1) if link_match else 'NONE'
    
    print(f"\n=== Listing {i} ===")
    print(f"Text: {text[:600]}")
    print(f"Link: {link}")