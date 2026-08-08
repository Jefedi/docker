#!/usr/bin/env python3
"""Parse all LBC listings, filter by criteria, check against seen file."""
import json, re

# Load seen IDs
with open('/opt/data/cron/output/havre-rental-seen.json') as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get('seen_ids', []))

# Accepted quartiers (Centre-ville sub-labels + Sanvic + Bléville)
accepted_quartiers = {
    'centre-ville', 'coty', 'massillon', 'eure', 'félix faure', 'felix faure',
    'perret', 'docks', 'rond point - observatoire', 'saint-françois - les docks',
    'saint-francois - les docks', 'danton', 'sanvic', 'bléville', 'bleville',
}

# All LBC listings from 3 pages
all_listings = [
    ("lbc-3214573571", 476, 2, 29, "Eure", "https://www.leboncoin.fr/ad/locations/3214573571"),
    ("lbc-3237765019", 500, 2, 44, "Graville", "https://www.leboncoin.fr/ad/locations/3237765019"),
    ("lbc-3246508832", 450, 2, 19, "Les Ormeaux - Maréchal Joffre", "https://www.leboncoin.fr/ad/locations/3246508832"),
    ("lbc-3246464426", 380, 2, 26, "Les Ormeaux - Maréchal Joffre", "https://www.leboncoin.fr/ad/locations/3246464426"),
    ("lbc-3114599423", 455, 2, 31, "Coty", "https://www.leboncoin.fr/ad/locations/3114599423"),
    ("lbc-2978416071", 465, 2, 25, "Massillon", "https://www.leboncoin.fr/ad/locations/2978416071"),
    ("lbc-3246191490", 450, 2, 35, "Eure", "https://www.leboncoin.fr/ad/locations/3246191490"),
    ("lbc-3235187047", 476, 2, 20, "Université - Sainte-Marie", "https://www.leboncoin.fr/ad/locations/3235187047"),
    ("lbc-3229022454", 449, 2, 24, "Université - Sainte-Marie", "https://www.leboncoin.fr/ad/locations/3229022454"),
    ("lbc-3237765020", 500, 2, 44, "Graville", "https://www.leboncoin.fr/ad/locations/3237765020"),
    ("lbc-3209055272", 470, 2, 20, "Université - Sainte-Marie", "https://www.leboncoin.fr/ad/locations/3209055272"),
    ("lbc-3245913837", 490, 2, 36, "Université - Sainte-Marie", "https://www.leboncoin.fr/ad/locations/3245913837"),
    ("lbc-3245819710", 480, 2, 30, "Université - Sainte-Marie", "https://www.leboncoin.fr/ad/locations/3245819710"),
    ("lbc-3225885761", 490, 2, 42, "Graville", "https://www.leboncoin.fr/ad/locations/3225885761"),
    ("lbc-3245699657", 429, 2, 32, "Eure", "https://www.leboncoin.fr/ad/locations/3245699657"),
    ("lbc-3206014055", 490, 2, 23, "Saint-Roch", "https://www.leboncoin.fr/ad/locations/3206014055"),
    ("lbc-3171888088", 395, 2, 22, "Eure", "https://www.leboncoin.fr/ad/locations/3171888088"),
    ("lbc-3245646772", 475, 2, 35, "Félix Faure", "https://www.leboncoin.fr/ad/locations/3245646772"),
    ("lbc-3245645303", 480, 2, 33, "Félix Faure", "https://www.leboncoin.fr/ad/locations/3245645303"),
    ("lbc-3236957272", 420, 2, 27, "Rond point - Observatoire", "https://www.leboncoin.fr/ad/locations/3236957272"),
    ("lbc-3214369980", 363, 2, 35, "Centre-ville", "https://www.leboncoin.fr/ad/locations/3214369980"),
    ("lbc-3240426512", 440, 2, 34, "Les Ormeaux - Maréchal Joffre", "https://www.leboncoin.fr/ad/locations/3240426512"),
    ("lbc-3213020854", 476, 2, 30, "Sainte-Anne", "https://www.leboncoin.fr/ad/locations/3213020854"),
    ("lbc-3245402762", 495, 2, 30, "Saint-François - Les Docks", "https://www.leboncoin.fr/ad/locations/3245402762"),
    ("lbc-3166993605", 470, 2, 34, "Les Ormeaux - Maréchal Joffre", "https://www.leboncoin.fr/ad/locations/3166993605"),
    ("lbc-3245020013", 500, 2, 20, "Coty", "https://www.leboncoin.fr/ad/locations/3245020013"),
    ("lbc-2932371645", 440, 2, 18, "Coty", "https://www.leboncoin.fr/ad/locations/2932371645"),
    ("lbc-3225853352", 430, 2, 33, "Sainte-Anne", "https://www.leboncoin.fr/ad/locations/3225853352"),
    ("lbc-3223323830", 395, 2, 23, "Université - Sainte-Marie", "https://www.leboncoin.fr/ad/locations/3223323830"),
    # Page 2
    ("lbc-3242301814", 485, 2, 32, "Coty", "https://www.leboncoin.fr/ad/locations/3242301814"),
    ("lbc-3244834386", 390, 2, 27, "Rond point - Observatoire", "https://www.leboncoin.fr/ad/locations/3244834386"),
    ("lbc-3244828763", 390, 2, 27, "Rond point - Observatoire", "https://www.leboncoin.fr/ad/locations/3244828763"),
    ("lbc-3244825216", 395, 2, 34, "Rond point - Observatoire", "https://www.leboncoin.fr/ad/locations/3244825216"),
    ("lbc-3244820840", 482, 2, 41, "Saint-François - Les Docks", "https://www.leboncoin.fr/ad/locations/3244820840"),
    ("lbc-3229591468", 490, 2, 30, "Rond point - Observatoire", "https://www.leboncoin.fr/ad/locations/3229591468"),
    ("lbc-3237764951", 500, 2, 44, "Graville", "https://www.leboncoin.fr/ad/locations/3237764951"),
    ("lbc-3229817725", 449, 2, 33, "Centre-ville", "https://www.leboncoin.fr/ad/locations/3229817725"),
    ("lbc-3197373339", 395, 2, 35, "Eure", "https://www.leboncoin.fr/ad/locations/3197373339"),
    ("lbc-3244321696", 483, 2, 36, "Sainte-Anne", "https://www.leboncoin.fr/ad/locations/3244321696"),
    ("lbc-3219073825", 430, 2, 28, "Eure", "https://www.leboncoin.fr/ad/locations/3219073825"),
    ("lbc-3244263245", 500, 2, 31, "Université - Sainte-Marie", "https://www.leboncoin.fr/ad/locations/3244263245"),
    ("lbc-3196913879", 470, 2, 41, "Eure", "https://www.leboncoin.fr/ad/locations/3196913879"),
    ("lbc-3229817723", 449, 2, 20, "Université - Sainte-Marie", "https://www.leboncoin.fr/ad/locations/3229817723"),
    ("lbc-3221348340", 495, 2, 26, "Massillon", "https://www.leboncoin.fr/ad/locations/3221348340"),
    ("lbc-3243253059", 470, 2, 30, "Coty", "https://www.leboncoin.fr/ad/locations/3243253059"),
    ("lbc-3235600057", 450, 2, 23, "Saint-François - Les Docks", "https://www.leboncoin.fr/ad/locations/3235600057"),
    ("lbc-3242915625", 390, 2, 37, "Rond point - Observatoire", "https://www.leboncoin.fr/ad/locations/3242915625"),
    ("lbc-3242315235", 450, 2, 28, "Coty", "https://www.leboncoin.fr/ad/locations/3242315235"),
    ("lbc-3241893358", 450, 2, 222, "Saint-Vincent - Plage", "https://www.leboncoin.fr/ad/locations/3241893358"),
    ("lbc-3241786702", 500, 2, 30, "Sainte-Anne", "https://www.leboncoin.fr/ad/locations/3241786702"),
    ("lbc-3241640668", 470, 2, 30, "Coty", "https://www.leboncoin.fr/ad/locations/3241640668"),
    ("lbc-3239908144", 500, 2, 26, "Sainte-Anne", "https://www.leboncoin.fr/ad/locations/3239908144"),
    ("lbc-3239789200", 50, 2, 30, "Les Ormeaux - Maréchal Joffre", "https://www.leboncoin.fr/ad/locations/3239789200"),
    ("lbc-2700598455", 460, 2, 22, "Université - Sainte-Marie", "https://www.leboncoin.fr/ad/locations/2700598455"),
    ("lbc-3124692218", 458, 2, 31, "Massillon", "https://www.leboncoin.fr/ad/locations/3124692218"),
    ("lbc-3232726225", 480, 2, 32, "Rond point - Observatoire", "https://www.leboncoin.fr/ad/locations/3232726225"),
    ("lbc-3124327523", 455, 2, 25, "Eure", "https://www.leboncoin.fr/ad/locations/3124327523"),
    ("lbc-3231545596", 410, 2, 25, "Eure", "https://www.leboncoin.fr/ad/locations/3231545596"),
    ("lbc-3195554445", 500, 2, 22, "Saint-Vincent - Plage", "https://www.leboncoin.fr/ad/locations/3195554445"),
    ("lbc-3230590321", 470, 2, 25, "Université - Sainte-Marie", "https://www.leboncoin.fr/ad/locations/3230590321"),
    ("lbc-3195532015", 430, 2, 23, "Université - Sainte-Marie", "https://www.leboncoin.fr/ad/locations/3195532015"),
    # Page 3
    ("lbc-3230317171", 423, 2, 31, "Les Ormeaux - Maréchal Joffre", "https://www.leboncoin.fr/ad/locations/3230317171"),
    ("lbc-3192123110", 500, 2, 20, "Centre-ville", "https://www.leboncoin.fr/ad/locations/3192123110"),
    ("lbc-3227985533", 500, 2, 27, "Sainte-Anne", "https://www.leboncoin.fr/ad/locations/3227985533"),
    ("lbc-3221276592", 450, 2, 23, "Rond point - Observatoire", "https://www.leboncoin.fr/ad/locations/3221276592"),
    ("lbc-3220617676", 370, 2, 9, "Graville", "https://www.leboncoin.fr/ad/locations/3220617676"),
]

def is_accepted_quartier(q):
    qn = q.lower().strip()
    for aq in accepted_quartiers:
        if aq in qn or qn in aq:
            return True
    return False

new_listings = []
already_seen = []
rejected = []

for listing in all_listings:
    id_, prix, pieces, surf, quartier, url = listing
    if id_ in seen_ids:
        already_seen.append(listing)
        continue
    reasons = []
    if prix > 500:
        reasons.append(f"prix {prix}>500")
    if surf < 28:
        reasons.append(f"surface {surf}<28")
    if pieces < 2:
        reasons.append(f"pièces {pieces}<2")
    if not is_accepted_quartier(quartier):
        reasons.append(f"quartier '{quartier}' non accepté")
    if reasons:
        rejected.append((listing, reasons))
    else:
        new_listings.append(listing)

print(f"TOTAL LBC: {len(all_listings)} | SEEN: {len(already_seen)} | REJECTED: {len(rejected)} | NEW: {len(new_listings)}")
print()
for l in new_listings:
    id_, prix, pieces, surf, quartier, url = l
    print(f"NEW: {id_} | {prix}€ | {pieces}p | {surf}m² | {quartier}")
    print(f"  URL: {url}")
print()
print("=== REJECTED (new, not matching criteria) ===")
for l, reasons in rejected:
    id_, prix, pieces, surf, quartier, url = l
    print(f"  {id_} | {prix}€ | {surf}m² | {quartier} -> {', '.join(reasons)}")

import json
with open('/opt/data/cron/tmp/lbc_new_candidates.json', 'w') as f:
    json.dump([{"id": l[0], "prix": l[1], "pieces": l[2], "surf": l[3], "quartier": l[4], "url": l[5]} for l in new_listings], f, indent=2, ensure_ascii=False)