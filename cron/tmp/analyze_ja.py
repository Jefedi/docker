import re, html as htmlmod, json

seen = json.load(open('/opt/data/cron/output/havre-rental-seen.json'))
seen_ids = seen['seen_ids']

# Jullien & Allix candidates - need to verify cuisine and chambre
# From the detail pages:

ja_candidates = [
    {
        'id': 'ja-a-louer-appartement-de-type-f3-harfleur-centre-ville',
        'url': 'https://www.jullien-allix.fr/annonce-immobiliere/a-louer-appartement-de-type-f3-harfleur-centre-ville.html',
        'pieces': 3,
        'surface': 66.81,
        'price': 440,
        'addr': '12/14 rue Gambetta, 76700 Harfleur',
        'desc': 'un sejour, une cuisine amenagee, 2 chambres, une salle de bains et un WC. Cave et emplacement de parking prive. 2eme etage avec ascenseur.',
        'dpe': 'C',
        'quartier': 'Harfleur Centre Ville (HORS critères: Harfleur pas Le Havre)'
    },
    {
        'id': 'ja-a-louer-appartement-meuble-de-type-f2-le-havre-marechal-joffre',
        'url': 'https://www.jullien-allix.fr/annonce-immobiliere/a-louer-appartement-meuble-de-type-f2-le-havre-marechal-joffre.html',
        'pieces': 2,
        'surface': 33.96,
        'price': 500,
        'addr': '101 rue Marechal Joffre, 76600 Le Havre',
        'desc': 'une entree, un sejour, une cuisine OUVERTE, une chambre, une salle de douche avec un WC. Chauffage electrique. 2eme etage sans ascenseur.',
        'dpe': 'C',
        'quartier': 'Maréchal Joffre (Centre-ville)'
    },
    {
        'id': 'ja-a-louer-appartement-type-f3-le-havre-quartier-mazeline',
        'url': 'https://www.jullien-allix.fr/annonce-immobiliere/a-louer-appartement-type-f3-le-havre-quartier-mazeline.html',
        'pieces': 3,
        'surface': 48.30,
        'price': 390,
        'addr': '8 Rue Denis Papin, 76600 Le Havre',
        'desc': 'une cuisine AMERICAINE, un sejour, 2 chambres, une salle de bains et des WC separees. Chauffage individuel electrique.',
        'dpe': 'D',
        'quartier': 'Quartier Mazeline (Danton/Centre-ville)'
    },
    {
        'id': 'ja-a-louer-appartement-de-type-f2-le-havre-cote-ouest-les-ormeaux',
        'url': 'https://www.jullien-allix.fr/annonce-immobiliere/a-louer-appartement-de-type-f2-le-havre-cote-ouest-les-ormeaux.html',
        'pieces': 2,
        'surface': 48.83,
        'price': 410,
        'addr': '19 rue Frederic Risson, 76600 Le Havre',
        'desc': 'un sejour, une cuisine amenagee, une chambre, une salle deau et un WC. Parking collectif. Chauffage et eau chaude individuels au gaz.',
        'dpe': 'E',
        'quartier': 'Cote Ouest / Les Ormeaux (HORS critères: pas dans Centre-ville/Sanvic/Bléville)'
    },
    {
        'id': 'ja-a-louer-appartement-de-type-f2-le-havre-centre-ville',
        'url': 'https://www.jullien-allix.fr/annonce-immobiliere/a-louer-appartement-de-type-f2-le-havre-centre-ville.html',
        'pieces': 2,
        'surface': 45.54,
        'price': 450,
        'addr': '27 rue du Chillou, 76600 Le Havre',
        'desc': 'une entree, une cuisine INDEPENDANTE, un sejour, une chambre, une salle deau, un WC et une cave. Chauffage et eau chaude collectifs. 2eme etage sans ascenseur.',
        'dpe': 'E',
        'quartier': 'Centre-ville'
    },
]

# Apply filters:
# 1. T2+ (2 pièces minimum) ✓
# 2. Loyer ≤ 500€/mois ✓
# 3. Surface ≥ 28m² ✓
# 4. Quartiers acceptés: Centre-ville, Sanvic, Bléville
# 5. Cuisine séparée (PAS cuisine ouverte/américaine/kitchenette)
# 6. Chambre fermée (pas coin nuit/canapé-lit)

print("=== JULLIEN & ALLIX — Analyse détaillée des candidats ===\n")

valid_quartiers = ['centre-ville', 'sanvic', 'bleville', 'coty', 'massillon', 'eure', 
                   'felix faure', 'perret', 'docks', 'rond-point', 'saint-francois', 'danton',
                   'marechal joffre', 'mazeline', 'chillou', 'observatoire']

for c in ja_candidates:
    print(f"\n--- {c['id']} ---")
    print(f"  T{c['pieces']} {c['surface']}m² | {c['price']}€/mois | DPE {c['dpe']}")
    print(f"  Adresse: {c['addr']}")
    print(f"  Quartier: {c['quartier']}")
    print(f"  Description: {c['desc']}")
    
    # Check filters
    issues = []
    
    # Quartier check
    q_lower = c['quartier'].lower()
    quartier_ok = False
    for q in valid_quartiers:
        if q in q_lower:
            quartier_ok = True
            break
    if not quartier_ok:
        issues.append(f"❌ Quartier non accepté: {c['quartier']}")
    else:
        print(f"  ✅ Quartier OK")
    
    # Cuisine check
    desc_lower = c['desc'].lower()
    if 'cuisine ouverte' in desc_lower or 'cuisine americaine' in desc_lower or 'kitchenette' in desc_lower:
        issues.append("❌ Cuisine ouverte/américaine")
    elif 'cuisine amenagee' in desc_lower or 'cuisine indépendante' in desc_lower or 'cuisine independante' in desc_lower:
        print(f"  ✅ Cuisine séparée")
    else:
        print(f"  ⚠️ Cuisine non précisée")
    
    # Chambre check
    if 'chambre' in desc_lower:
        print(f"  ✅ Chambre fermée")
    else:
        issues.append("❌ Pas de chambre mentionnée")
    
    # Check seen
    is_new = c['id'] not in seen_ids
    print(f"  {'🆕 NOUVELLE' if is_new else '👁️ DÉJÀ VUE'}")
    
    if issues:
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"  ✅ PASSE TOUS LES FILTRES")
    
    print()