import re, html as htmllib, json

# Parse JA F2 #5 (clinique Ormeaux) - full description
raw = open('/opt/data/tmp/veille/ja_f2_5.html').read()
page = htmllib.unescape(raw)

# Get full description
# Look for description content in the page body
desc_matches = re.findall(r'(?:description|contenu|annonce)[^<]*<[^>]*>([^<]{50,500})', page, re.IGNORECASE)
print("Desc matches:")
for d in desc_matches[:5]:
    print(f"  {d[:200]}")

# Look for cuisine mentions
cuisine_ctx = re.findall(r'.{0,60}cuisine.{0,60}', page, re.IGNORECASE)
print("\nCuisine contexts:")
for c in cuisine_ctx[:5]:
    c_clean = re.sub(r'\s+', ' ', c).strip()
    if not any(x in c_clean.lower() for x in ['font', 'css', 'script']):
        print(f"  {c_clean[:120]}")

# Look for "séjour" mentions
sejour_ctx = re.findall(r'.{0,30}séjour.{0,60}', page, re.IGNORECASE)
print("\nSéjour contexts:")
for s in sejour_ctx[:5]:
    s_clean = re.sub(r'\s+', ' ', s).strip()
    if not any(x in s_clean.lower() for x in ['font', 'css', 'script']):
        print(f"  {s_clean[:120]}")

# Look for meta description
meta_m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', raw, re.IGNORECASE)
if meta_m:
    print(f"\nMeta desc: {meta_m.group(1)}")

# Look for og:description
og_m = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', raw, re.IGNORECASE)
if og_m:
    print(f"\nOG desc: {og_m.group(1)}")

# Also check the full text of the listing
# Find the main content area
content_m = re.search(r'class="[^"]*content[^"]*"[^>]*>(.*?)(?:class="[^"]*footer|</body)', page, re.DOTALL | re.IGNORECASE)
if content_m:
    content = re.sub(r'<[^>]+>', ' ', content_m.group(1))
    content = re.sub(r'\s+', ' ', content).strip()
    # Find "cuisine" in content
    cuisine_in_content = re.findall(r'.{0,40}cuisine.{0,40}', content, re.IGNORECASE)
    print("\nCuisine in content:")
    for c in cuisine_in_content[:3]:
        print(f"  {c.strip()[:120]}")
    
    # Find "séjour" in content
    sejour_in_content = re.findall(r'.{0,40}séjour.{0,40}', content, re.IGNORECASE)
    print("\nSéjour in content:")
    for s in sejour_in_content[:3]:
        print(f"  {s.strip()[:120]}")