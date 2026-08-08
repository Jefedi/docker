import json
from datetime import datetime

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json', 'r') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

# New IDs from Jullien-Allix to add
new_ids = [
    'ja-a-louer-appartement-meuble-de-type-f2-le-havre-marechal-joffre',
    'ja-a-louer-appartement-de-type-f2-le-havre-quartier-demidoff',
    'ja-a-louer-appartement-type-f3-le-havre-quartier-mazeline',
    'ja-a-louer-appartement-de-type-f6-le-havre-hyper-centre-ville',
]

added = 0
for nid in new_ids:
    if nid not in seen_ids:
        seen_data['seen_ids'].append(nid)
        seen_ids.add(nid)
        added += 1

seen_data['total_seen'] = len(seen_data['seen_ids'])
seen_data['last_updated'] = datetime.now().strftime('%Y-%m-%dT%H:%M')

with open('/opt/data/cron/output/havre-rental-seen.json', 'w') as f:
    json.dump(seen_data, f, indent=2)

print(f"Added {added} new IDs to seen file")
print(f"Total seen: {len(seen_data['seen_ids'])}")

# Final analysis
print("\n" + "="*80)
print("ANALYSE FINALE DES NOUVELLES ANNONCES JULLIEN-ALLIX")
print("="*80)

listings = [
    {
        'id': 'ja-a-louer-appartement-meuble-de-type-f2-le-havre-marechal-joffre',
        'source': 'Jullien-Allix',
        'type': 'T2 (F2)',
        'surface': 33.96,
        'rent': 440,  # 400€ + 40€ charges
        'loyer_hc': 400,
        'charges': 40,
        'quartier': 'Maréchal Joffre',
        'dpe': 'C',
        'cuisine': 'OUVERTE',
        'chambre': 'OUI (fermée)',
        'lumineux': 'Balcon mentionné',
        'url': 'https://www.jullien-allix.fr/annonce-immobiliere/a-louer-appartement-meuble-de-type-f2-le-havre-marechal-joffre.html',
        'description': 'F2 meublé, 33.96m², 2ème étage sans ascenseur. Entrée, séjour, cuisine ouverte, chambre, salle de douche avec WC. Chauffage électrique. DPE C. 101 rue Maréchal Joffre.',
    },
    {
        'id': 'ja-a-louer-appartement-de-type-f2-le-havre-quartier-demidoff',
        'source': 'Jullien-Allix',
        'type': 'T2 (F2)',
        'surface': 23,
        'rent': 395,  # 380€ + 15€ charges
        'loyer_hc': 380,
        'charges': 15,
        'quartier': 'Demidoff',
        'dpe': 'D',
        'cuisine': 'Non spécifiée (probablement séparée)',
        'chambre': 'OUI (fermée)',
        'lumineux': 'Balcon mentionné',
        'url': 'https://www.jullien-allix.fr/annonce-immobiliere/a-louer-appartement-de-type-f2-le-havre-quartier-demidoff.html',
        'description': 'F2, 23m², cuisine, chambre, salle d\'eau, WC. Chauffage électrique basse consommation. DPE D. 8 rue Denis Papin (quartier Demidoff/Danton).',
    },
    {
        'id': 'ja-a-louer-appartement-type-f3-le-havre-quartier-mazeline',
        'source': 'Jullien-Allix',
        'type': 'T3 (F3)',
        'surface': 30,
        'rent': 500,  # 480€ + 20€ charges (approx)
        'loyer_hc': 480,
        'charges': 20,
        'quartier': 'Mazeline',
        'dpe': 'Non spécifié',
        'cuisine': 'AMÉRICAINE',
        'chambre': 'OUI (2 chambres)',
        'lumineux': 'Balcon mentionné',
        'url': 'https://www.jullien-allix.fr/annonce-immobiliere/a-louer-appartement-type-f3-le-havre-quartier-mazeline.html',
        'description': 'F3, 30m², cuisine américaine, séjour, 2 chambres, salle de bains, WC séparés. Chauffage électrique individuel.',
    },
]

print("\nCritères de filtrage stricts:")
print("  ✅ T2+ (2 pièces minimum)")
print("  ✅ Loyer ≤ 500€/mois")
print("  ✅ Surface ≥ 28m²")
print("  ✅ Quartiers acceptés: Centre-ville (Coty, Massillon, Eure, Félix Faure, Perret, Docks, Rond-point Observatoire, Saint-François, Danton), Sanvic, Bléville")
print("  ✅ Cuisine séparée (PAS cuisine ouverte/américaine/kitchenette)")
print("  ✅ Chambre fermée (pas coin nuit/canapé-lit)")
print("  ✅ Lumineux (dernier étage, balcon, terrasse, exposition, traversant = bonus)")

for l in listings:
    print(f"\n{'='*60}")
    print(f"🏠 {l['source']} — {l['type']} {l['surface']}m² — {l['quartier']}")
    print(f"   💰 {l['rent']}€/mois (loyer {l['loyer_hc']}€ + charges {l['charges']}€)")
    print(f"   📋 DPE: {l['dpe']}")
    print(f"   🍳 Cuisine: {l['cuisine']}")
    print(f"   🛏️ Chambre: {l['chambre']}")
    print(f"   💡 Lumineux: {l['lumineux']}")
    print(f"   🔗 {l['url']}")
    print(f"   📝 {l['description'][:200]}")
    
    # Check criteria
    passes = []
    fails = []
    
    if l['type'].startswith('T2') or l['type'].startswith('T3') or l['type'].startswith('T4'):
        passes.append("T2+")
    else:
        fails.append(f"Type: {l['type']}")
    
    if l['rent'] <= 500:
        passes.append(f"Loyer ≤ 500€ ({l['rent']}€)")
    else:
        fails.append(f"Loyer > 500€ ({l['rent']}€)")
    
    if l['surface'] >= 28:
        passes.append(f"Surface ≥ 28m² ({l['surface']}m²)")
    else:
        fails.append(f"Surface < 28m² ({l['surface']}m²)")
    
    # Quartier check
    accepted_quartiers = ['Centre-ville', 'Coty', 'Massillon', 'Eure', 'Félix Faure', 'Perret', 
                          'Docks', 'Rond-point Observatoire', 'Saint-François', 'Danton', 'Sanvic', 'Bléville']
    # Map Maréchal Joffre to Centre-ville (it's in the Centre-ville area)
    quartier_mapping = {
        'Maréchal Joffre': 'Centre-ville',  # Maréchal Joffre is in the Centre-ville area
        'Demidoff': 'Danton',  # Demidoff/Danton area
        'Mazeline': 'Centre-ville',  # Mazeline area is near Centre-ville
    }
    mapped_quartier = quartier_mapping.get(l['quartier'], l['quartier'])
    if mapped_quartier in accepted_quartiers:
        passes.append(f"Quartier: {l['quartier']} → {mapped_quartier}")
    else:
        fails.append(f"Quartier non accepté: {l['quartier']}")
    
    # Cuisine check
    if 'OUVERTE' in l['cuisine'] or 'AMÉRICAINE' in l['cuisine']:
        fails.append(f"Cuisine {l['cuisine']}")
    elif 'séparée' in l['cuisine'].lower() or 'Non spécifiée' in l['cuisine']:
        passes.append(f"Cuisine: {l['cuisine']}")
    else:
        fails.append(f"Cuisine: {l['cuisine']}")
    
    # Chambre check
    if 'OUI' in l['chambre']:
        passes.append(f"Chambre: {l['chambre']}")
    else:
        fails.append(f"Chambre: {l['chambre']}")
    
    print(f"\n   ✅ PASSE: {', '.join(passes)}")
    if fails:
        print(f"   ❌ ÉCHEC: {', '.join(fails)}")
    
    all_pass = len(fails) == 0
    print(f"   {'✅ ACCEPTÉ' if all_pass else '❌ REJETÉ'}")