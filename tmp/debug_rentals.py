#!/usr/bin/env python3
"""Debug: check which new LBC IDs are not in seen list and why they fail filters"""
import json

SEEN_FILE = "/opt/data/cron/output/havre-rental-seen.json"
with open(SEEN_FILE, "r") as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get("seen_ids", []))

# All LBC IDs from this run
lbc_ids = [
    "3243119818", "3243118723", "3114599423", "3214369980", "3240426512",
    "2978416071", "3206014055", "3225885761", "3242915625", "3171888088",
    "3242893363", "3236957272", "3183706861", "3242751208", "3008426681",
    "3225853352", "3138529046",
    # Additional
    "3222895244", "3020670214", "3230697352", "3242316355", "3242315235",
    "3242301814", "3223323830", "3197074083", "3229817725", "3166993605",
    "3213020854", "3241893358", "3197373339", "3229591468", "3241786702",
    "3241640668", "3241474418"
]

print("=== NEW LBC IDs NOT IN SEEN LIST ===")
new_ids = []
for lid in lbc_ids:
    full_id = f"lbc-{lid}"
    if full_id not in seen_ids and lid not in seen_ids:
        new_ids.append(lid)
        print(f"  NEW: lbc-{lid}")

print(f"\nTotal new: {len(new_ids)}")

# Now check which ones are in accepted quartiers and pass basic filters
# Quartier mapping: accepted = Centre-ville (incl sub-labels), Bléville, Sanvic
listings_detail = {
    "3243119818": (480, 2, 35, "Félix Faure", "3/3", True, "Dernier étage"),
    "3243118723": (475, 2, 33, "Félix Faure", "", True, ""),
    "3114599423": (455, 2, 31, "Coty", "2/2", True, "Dernier étage"),
    "3240426512": (440, 2, 34, "Les Ormeaux - Maréchal Joffre", "2/3", True, ""),
    "2978416071": (465, 2, 25, "Massillon", "2/4", True, ""),
    "3242915625": (390, 2, 37, "Rond point - Observatoire", "RDC/3", True, ""),
    "3171888088": (395, 2, 22, "Eure", "1/2", True, ""),
    "3242893363": (339, 2, 25.4, "Eure", "RDC/3", False, ""),
    "3236957272": (420, 2, 27, "Rond point - Observatoire", "4/4", False, "Dernier étage"),
    "3183706861": (440, 2, 18, "Coty", "2/2", True, "Dernier étage"),
    "3242751208": (440, 2, 29, "Eure", "RDC/3", True, ""),
    "3225853352": (380, 2, 30, "Sainte-Anne", "1/4", False, ""),
    "3138529046": (430, 2, 33, "Sainte-Anne", "2", False, ""),
    "3222895244": (460, 2, 18, "Eure", "RDC/2", True, ""),
    "3020670214": (450, 2, 24, "Eure", "1", True, ""),
    "3230697352": (495, 2, 35, "Centre-ville", "", True, "Balcon"),
    "3242316355": (410, 2, 20, "Université - Sainte-Marie", "4", False, ""),
    "3242315235": (500, 2, 30, "Sainte-Anne", "1/1", True, "Dernier étage"),
    "3242301814": (450, 2, 28, "Coty", "2/3", False, ""),
    "3223323830": (485, 2, 32, "Coty", "1", False, "Terrasse"),
    "3197074083": (395, 2, 23, "Université - Sainte-Marie", "4/4", False, "Dernier étage"),
    "3229817725": (450, 2, 38, "Coty", "", False, ""),
    "3166993605": (449, 2, 33, "Centre-ville", "1", True, ""),
    "3213020854": (470, 2, 34, "Les Ormeaux - Maréchal Joffre", "2", False, ""),
    "3241893358": (476, 2, 32, "Le Havre 76600", "RDC", False, ""),
    "3197373339": (450, 2, 222, "Saint-Vincent - Plage", "RDC/2", True, ""),
    "3229591468": (395, 2, 35, "Eure", "4", False, ""),
    "3241786702": (490, 2, 30, "Rond point - Observatoire", "3", True, ""),
    "3241640668": (500, 2, 30, "Sainte-Anne", "2", True, ""),
    "3241474418": (470, 2, 30, "Coty", "RDC/3", False, ""),
}

# Accepted quartiers
accepted_quartiers_map = {
    "félix faure": "Centre-ville",
    "felix faure": "Centre-ville",
    "coty": "Centre-ville",
    "massillon": "Centre-ville",
    "eure": "Centre-ville",
    "rond point - observatoire": "Centre-ville",
    "les ormeaux - maréchal joffre": "Centre-ville",
    "centre-ville": "Centre-ville",
    "centre ville": "Centre-ville",
    "bleville": "Bléville",
    "sanvic": "Sanvic",
}

def normalize(s):
    return s.lower().strip()

print("\n=== FILTER ANALYSIS FOR NEW IDs ===")
for lid in new_ids:
    if lid not in listings_detail:
        continue
    price, pieces, surface, quartier, etage, meuble, desc = listings_detail[lid]
    q = normalize(quartier)
    
    # Check quartier
    accepted = None
    for key, val in accepted_quartiers_map.items():
        if key in q:
            accepted = val
            break
    
    reasons = []
    if price > 500:
        reasons.append(f"PRICE {price}€ > 500€")
    if pieces < 2:
        reasons.append(f"PIECES {pieces} < 2")
    if surface < 28:
        reasons.append(f"SURFACE {surface}m² < 28m²")
    if not accepted:
        reasons.append(f"QUARTIER '{quartier}' NOT ACCEPTED")
    
    # Check luminosity
    luminous = False
    if desc:
        d = desc.lower()
        if any(c in d for c in ["lumineux", "lumineuse", "luminosité", "lumière",
            "dernier étage", "balcon", "terrasse", "vue dégagée", "exposition",
            "exposé sud"]):
            luminous = True
    if etage and "dernier" in etage.lower():
        luminous = True
    if not luminous:
        reasons.append("NOT LUMINEUX")
    
    if reasons:
        print(f"  ❌ lbc-{lid}: {price}€ {pieces}p {surface}m² {quartier} — REJECT: {'; '.join(reasons)}")
    else:
        print(f"  ✅ lbc-{lid}: {price}€ {pieces}p {surface}m² {quartier} — PASSES ALL FILTERS!")