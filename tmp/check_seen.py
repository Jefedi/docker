import json

# From the analysis, the REAL T2+ listings ≤500€ with surface ≥28m² on Le-Partenaire:
# The prix-max=500 filter is NOT strict. Many listings are above 500€.
# Let me manually compile the ones that are actually ≤500€ and T2+ and ≥28m²:

# Page 1:
# - 24461152: T2 28m² 480€ "F2 MEUBLE Entièrement refait Proche Université. Cuisine ouverte sur séjour avec bar, chambre avec penderie" → cuisine OUVERTE → FAILS cuisine séparée criterion
# - 20963104: T6 98m² 350€ → colocation, 5 chambres → FAILS (colocation, not regular apartment)

# Page 2:
# - 23946724: T2 37m² 465€ → "T1 bis", "grande cuisine / salle à manger indépendante", "salon et un coin bureau / chambre" → possible but "coin bureau/chambre" = chambre pas vraiment fermée?
# - 24231161: T4 60m² 420€ → "COLOCATION" → FAILS (colocation)

# Page 3:
# - 23599098: T2 41m² 380€ → "non meublé de 41 m²" → needs individual ad visit for cuisine/chambre details

# Page 4:
# - 24576565: T2 36m² → "505€" → above 500 budget
# - 21644266: T2 18m² 500€ → surface < 28m² → FAILS
# - 20369313: T4 105m² 390€ → colocation ("Chambre accès privée") → FAILS

# So the real candidates from Le-Partenaire that might pass:
real_candidates = {
    "lp-23946724": {  # T2 37m² 465€
        "title": "T2 37m² — Le Havre",
        "price": 465,
        "surface": 37,
        "rooms": 2,
        "url": "https://www.le-partenaire.fr/immobilier/location/appartement/havre/76600/2pieces/23946724",
        "desc": "T1 bis, grande cuisine/salle à manger indépendante, salon, coin bureau/chambre, salle de douche, WC séparés. Dernier étage.",
        "cuisine_separee": True,  # "grande cuisine / salle à manger indépendante"
        "chambre_fermee": None,  # "coin bureau / chambre" — uncertain
        "lumineux": None,
        "quartier": None,  # not mentioned
        "notes": "Cuisine indépendante confirmée. Chambre: 'coin bureau/chambre' = incertain. Quartier non mentionné."
    },
    "lp-23599098": {  # T2 41m² 380€
        "title": "T2 41m² — Le Havre",
        "price": 380,
        "surface": 41,
        "rooms": 2,
        "url": "https://www.le-partenaire.fr/immobilier/location/appartement/havre/76600/2pieces/23599098",
        "desc": "T2 non meublé 41m², disponible immédiatement. LocService (particulier). Pas de détails sur cuisine/chambre dans le résumé.",
        "cuisine_separee": None,
        "chambre_fermee": None,
        "lumineux": None,
        "quartier": None,
        "notes": "Annonce LocService — détails limités. Cuisine et chambre non vérifiables depuis le résumé."
    }
}

# Check which are already seen
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen = json.load(f)
seen_ids = set(seen['seen_ids'])

for id, info in real_candidates.items():
    is_seen = id in seen_ids
    print(f"{id}: {'SEEN' if is_seen else 'NEW'} — {info['price']}€ {info['surface']}m² {info['url']}")