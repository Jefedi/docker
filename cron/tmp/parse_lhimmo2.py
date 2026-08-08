import re, html as htmlmod

# Parse LH Immo listings from all pages
lhimmo_urls = [
    'https://www.lhimmo.com/annonce/appartement-t2-quartier-danton-2/',
    'https://www.lhimmo.com/annonce/appartement-t2-quartier-universite-le-havre/',
    'https://www.lhimmo.com/annonce/appartement-t2-lumineux-le-havre/',
    'https://www.lhimmo.com/annonce/appartement-t2-meuble/',
    'https://www.lhimmo.com/annonce/appartement-t3-au-pied-de-lespace-coty/',
    'https://www.lhimmo.com/annonce/appartement-t3-square-saint-roch-le-havre/',
    'https://www.lhimmo.com/annonce/appartement-t3-avec-balcon-et-parking/',
    'https://www.lhimmo.com/annonce/appartement-t3-duplex-le-havre/',
    'https://www.lhimmo.com/annonce/appartement-hyper-centre-ville-le-havre/',
    'https://www.lhimmo.com/annonce/hyper-centre-ville-appartement-t4/',
    'https://www.lhimmo.com/annonce/appartement-t4-centre-ville/',
    'https://www.lhimmo.com/annonce/appartement-3-pieces-de-7040-m2-parking-le-havre/',
    'https://www.lhimmo.com/annonce/porte-oceane-plage-appartement-t3/',
    'https://www.lhimmo.com/annonce/233708/',
]

# Extract titles and check which ones mention T2 or more
for url in lhimmo_urls:
    slug = url.split('/annonce/')[1].rstrip('/')
    # Check if it's T2+ and could be a rental
    if any(t in slug.lower() for t in ['t2', 't3', 't4', 't5', '3-pieces', '4-pieces', 'hyper-centre', 'porte-oceane', '233708', 'appartement-t3', 'appartement-t4']):
        print(f"  POTENTIAL: {slug}")

# Let's check the actual pages for rent and details
# But we already have the listing pages cached. Let's get text from all 3 pages
for fname in ['/tmp/lhimmo_annonces.html', '/tmp/lhimmo_p2.html', '/tmp/lhimmo_p3.html']:
    content = open(fname).read()
    text = re.sub(r'<[^>]+>', ' ', content)
    text = htmlmod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find listings with rent info
    # Pattern: title + price + "à louer" or "Loyer"
    listings = re.findall(r'(Appartement\s+T[23456][^|]*?|Hyper[^|]*?Appartement[^|]*?|Porte[^|]*?Appartement[^|]*?)(?:\|)', text)
    
    # Actually, let's look for the listing cards
    # Each card seems to have title, price, and description
    card_pattern = re.findall(r'(appartement\s+T[23456][^"]*?|hyper[- ]centre[^"]*?appartement[^"]*?|porte[^"]*?appartement[^"]*?)\s*(?:"|Loyer|à louer|€)', text, re.I)
    
    # Find rent prices near T2/T3 mentions
    for t in ['T2', 'T3', 'T4']:
        idx = 0
        while True:
            pos = text.find(t, idx)
            if pos == -1:
                break
            context = text[max(0,pos-50):pos+200]
            # Look for price nearby
            price_match = re.search(r'(\d{3,4})\s*€', context)
            if price_match:
                print(f"  {t} near {price_match.group(0)}: ...{context[:150]}...")
            idx = pos + 1
            if idx > len(text):
                break
    break  # Only need to do this once across all pages