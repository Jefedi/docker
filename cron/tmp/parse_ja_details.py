import re, html as htmlmod

files = {
    'ja_f3_harfleur': '/tmp/ja_f3_harfleur.html',
    'ja_f2_meuble_joffre': '/tmp/ja_f2_meuble_joffre.html',
    'ja_f3_mazeline': '/tmp/ja_f3_mazeline.html',
    'ja_f2_ormeaux': '/tmp/ja_f2_ormeaux.html',
    'ja_f2_centre': '/tmp/ja_f2_centre.html',
}

for name, fname in files.items():
    content = open(fname).read()
    text = re.sub(r'<[^>]+>', ' ', content)
    text = htmlmod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    print(f"\n=== {name} ===")
    
    # Find description - look for key terms
    for term in ['cuisine', 'chambre', 'pièce', 'étage', 'balcon', 'terrass', 'lumineux', 'exposition', 'traversant', 'DPE', 'classe']:
        pos = text.lower().find(term)
        if pos >= 0:
            context = text[max(0,pos-30):pos+100]
            print(f"  {term}: ...{context}...")
    
    # Find price
    price_match = re.search(r'(\d{3,4})\s*€\s*/?\s*(?:par\s*)?mois', text)
    if price_match:
        print(f"  Price: {price_match.group(0)}")
    
    # Find surface
    surface_match = re.search(r'(\d+(?:\.\d+)?)\s*m²', text)
    if surface_match:
        print(f"  Surface: {surface_match.group(0)}")