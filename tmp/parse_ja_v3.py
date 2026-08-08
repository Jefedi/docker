#!/usr/bin/env python3
"""Parse JA individual listing pages using actual filenames."""
import re, html as h, os, glob

ja_files = sorted(glob.glob('/tmp/scrape/ja_*.html'))
# Remove the listings page
ja_files = [f for f in ja_files if 'listings' not in f]

ja_slugs_map = {
    '48a0437eb1887ec70bfc3abaf4466905': ('F2 Jardins d\'Ostara - Saint-Nicolas', 'a-louer-appartement-de-type-f2-residence-les-jardins-dostara-le-havre-quartier-saint-nicolas'),
    '96b3f0fbb140a589ae8773fa8479654e': ('F2 Rénové - Maréchal Joffre', 'a-louer-appartement-de-type-f2-entierement-renove-le-havre-marechal-joffre'),
    '13dda58a6e6315d3ac3ab34c2eb34a97': ('F2 Meublé - Maréchal Joffre', 'a-louer-appartement-meuble-de-type-f2-le-havre-marechal-joffre'),
    'e8ce304e49f4d9f0cece2d40d7c90311': ('F2 Côte Ouest Ormeaux', 'a-louer-appartement-de-type-f2-le-havre-cote-ouest-les-ormeaux'),
    'ac2de9423a18973ef8a057af773207a8': ('F2 Demidoff', 'a-louer-appartement-de-type-f2-le-havre-quartier-demidoff'),
    '2248594667ea000f68c4b64922017680': ('F2 Docks Vauban', 'a-louer-appartement-de-type-f2-le-havre-secteur-docks-vauban'),
    'af6c35229929c2bc7a8f827b30ac9081': ('F2 Proximité Pasino', 'a-louer-appartement-de-type-f2-le-havre-proximite-pasino'),
    '9096376229f47580f1342e0b1febf8ac': ('F2 Centre-ville', 'a-louer-appartement-de-type-f2-le-havre-centre-ville'),
}

for fpath in ja_files:
    basename = os.path.basename(fpath).replace('ja_', '').replace('.html', '')
    info = ja_slugs_map.get(basename, ('Unknown', basename))
    title, slug = info
    
    with open(fpath, 'r', errors='replace') as f:
        raw = f.read()
    
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = h.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find all € amounts in first 8000 chars
    euros = re.findall(r'(\d[\d\s\xa0]*)\s*€', text[:8000])
    euro_nums = []
    for e in euros:
        nums = re.sub(r'[\s\xa0]', '', e)
        try:
            n = int(nums)
            if 100 < n < 3000:  # Reasonable rent range
                euro_nums.append(n)
        except:
            pass
    
    # Find surface
    surfaces = re.findall(r'(\d[\d,\.]*)\s*m[²2]', text[:8000])
    
    # Check cuisine
    cuisine_sep = bool(re.search(r'cuisine\s*(?:s[ée]par[ée]e|ind[ée]pendante|ferm[ée]e)', text, re.I))
    cuisine_ouverte = bool(re.search(r'cuisine\s*(?:ouverte|am[ée]ricaine)|kitchenette|coin cuisine', text, re.I))
    
    # Find loyer context
    loyer_pos = text.find('Loyer')
    if loyer_pos < 0:
        loyer_pos = text.find('loyer')
    context = text[max(0,loyer_pos-50):loyer_pos+300] if loyer_pos >= 0 else 'N/A'
    
    print(f"=== {title} ===")
    print(f"  URL: https://www.jullien-allix.fr/annonce-immobiliere/{slug}.html")
    print(f"  Euro amounts (rent range): {euro_nums[:5]}")
    print(f"  Surfaces: {surfaces[:5]}")
    print(f"  Cuisine séparée: {cuisine_sep} | Cuisine ouverte: {cuisine_ouverte}")
    print(f"  Loyer context: {context[:200]}")
    print()