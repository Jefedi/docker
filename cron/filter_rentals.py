#!/usr/bin/env python3
"""Filter Le Havre rental listings per strict criteria."""
import json

with open("/opt/data/cron/output/havre-rental-seen.json") as f:
    seen_data = json.load(f)
seen_ids = set(seen_data.get("seen_ids", []))

ACCEPTED_QUARTIERS = {"centre-ville", "bleville", "sanvic"}
SUBQUARTIER_MAP = {
    "centre-ville": "centre-ville", "coty": "centre-ville", "massillon": "centre-ville",
    "eure": "centre-ville", "danton": "centre-ville", "felix faure": "centre-ville",
    "saint-françois - les docks": "centre-ville", "saint-francois - les docks": "centre-ville",
    "université - sainte-marie": "centre-ville", "universite - sainte-marie": "centre-ville",
    "rond point - observatoire": "centre-ville",
    "bleville": "bleville", "sanvic": "sanvic",
    "le havre 76600": "centre-ville",  # generic, assume centre-ville
}

listings = [
    # === LEBONCOIN ===
    {"source":"lbc","id":"3229022454","price":449,"rooms":2,"surface":24,"quartier_raw":"Université - Sainte-Marie","etage":"Étage 4","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3229022454","description":""},
    {"source":"lbc","id":"2932371645","price":440,"rooms":2,"surface":18,"quartier_raw":"Coty","etage":"Étage 2/2","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/2932371645","description":""},
    {"source":"lbc","id":"3243253059","price":470,"rooms":2,"surface":30,"quartier_raw":"Coty","etage":"RDC/2","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3243253059","description":""},
    {"source":"lbc","id":"3235187047","price":476,"rooms":2,"surface":32,"quartier_raw":"Le Havre 76600","etage":"Étage 2","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3235187047","description":""},
    {"source":"lbc","id":"3195812292","price":465,"rooms":2,"surface":37,"quartier_raw":"Le Havre 76600","etage":"Étage 1/2","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3195812292","description":""},
    {"source":"lbc","id":"3243119818","price":450,"rooms":2,"surface":23,"quartier_raw":"Saint-François - Les Docks","etage":"Étage 2","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3243119818","description":""},
    {"source":"lbc","id":"3243118723","price":480,"rooms":2,"surface":35,"quartier_raw":"Félix Faure","etage":"Étage 3/3","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3243118723","description":""},
    {"source":"lbc","id":"3114599423","price":475,"rooms":2,"surface":33,"quartier_raw":"Félix Faure","etage":"","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3114599423","description":""},
    {"source":"lbc","id":"3214369980","price":455,"rooms":2,"surface":31,"quartier_raw":"Coty","etage":"Étage 2/2","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3214369980","description":""},
    {"source":"lbc","id":"3240426512","price":363,"rooms":2,"surface":27,"quartier_raw":"Le Havre 76600","etage":"Étage 1","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3240426512","description":""},
    {"source":"lbc","id":"2978416071","price":440,"rooms":2,"surface":34,"quartier_raw":"Les Ormeaux - Maréchal Joffre","etage":"Étage 2/3","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/2978416071","description":""},
    {"source":"lbc","id":"3206014055","price":465,"rooms":2,"surface":25,"quartier_raw":"Massillon","etage":"Étage 2/4","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3206014055","description":""},
    {"source":"lbc","id":"3225885761","price":490,"rooms":2,"surface":23,"quartier_raw":"Saint-Roch","etage":"RDC","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3225885761","description":""},
    {"source":"lbc","id":"3242915625","price":490,"rooms":2,"surface":42,"quartier_raw":"Graville","etage":"Étage 2","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3242915625","description":""},
    {"source":"lbc","id":"3171888088","price":390,"rooms":2,"surface":37,"quartier_raw":"Rond point - Observatoire","etage":"RDC/3","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3171888088","description":""},
    {"source":"lbc","id":"3242893363","price":395,"rooms":2,"surface":22,"quartier_raw":"Eure","etage":"Étage 1/2","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3242893363","description":""},
    {"source":"lbc","id":"3236957272","price":339,"rooms":2,"surface":25.4,"quartier_raw":"Eure","etage":"RDC/3","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3236957272","description":""},
    {"source":"lbc","id":"3183706861","price":420,"rooms":2,"surface":27,"quartier_raw":"Rond point - Observatoire","etage":"Étage 4/4","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3183706861","description":""},
    {"source":"lbc","id":"3242751208","price":440,"rooms":2,"surface":29,"quartier_raw":"Eure","etage":"RDC/3","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3242751208","description":""},
    {"source":"lbc","id":"3008426681","price":495,"rooms":2,"surface":21,"quartier_raw":"Sainte-Anne","etage":"RDC/2","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3008426681","description":""},
    {"source":"lbc","id":"3225853352","price":380,"rooms":2,"surface":30,"quartier_raw":"Sainte-Anne","etage":"Étage 1/4","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3225853352","description":""},
    {"source":"lbc","id":"3138529046","price":430,"rooms":2,"surface":33,"quartier_raw":"Sainte-Anne","etage":"Étage 2","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3138529046","description":""},
    {"source":"lbc","id":"3222895244","price":460,"rooms":2,"surface":18,"quartier_raw":"Eure","etage":"RDC/2","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3222895244","description":""},
    {"source":"lbc","id":"3020670214","price":450,"rooms":2,"surface":24,"quartier_raw":"Eure","etage":"Étage 1","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3020670214","description":""},
    {"source":"lbc","id":"3230697352","price":495,"rooms":2,"surface":35,"quartier_raw":"Centre-ville","etage":"","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3230697352","description":"Balcon. Centre-ville."},
    {"source":"lbc","id":"3242316355","price":410,"rooms":2,"surface":20,"quartier_raw":"Université - Sainte-Marie","etage":"Étage 4","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3242316355","description":""},
    {"source":"lbc","id":"3242315235","price":500,"rooms":2,"surface":30,"quartier_raw":"Sainte-Anne","etage":"Étage 1/1","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3242315235","description":""},
    {"source":"lbc","id":"3242301814","price":450,"rooms":2,"surface":28,"quartier_raw":"Coty","etage":"Étage 2/3","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3242301814","description":""},
    {"source":"lbc","id":"3223323830","price":485,"rooms":2,"surface":32,"quartier_raw":"Coty","etage":"Étage 1","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3223323830","description":"Terrasse."},
    {"source":"lbc","id":"3197074083","price":395,"rooms":2,"surface":23,"quartier_raw":"Université - Sainte-Marie","etage":"Étage 4/4","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3197074083","description":""},
    {"source":"lbc","id":"3229817725","price":450,"rooms":2,"surface":38,"quartier_raw":"Coty","etage":"","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3229817725","description":""},
    {"source":"lbc","id":"3166993605","price":449,"rooms":2,"surface":33,"quartier_raw":"Centre-ville","etage":"Étage 1","meuble":True,"link":"https://www.leboncoin.fr/ad/locations/3166993605","description":""},
    {"source":"lbc","id":"3213020854","price":470,"rooms":2,"surface":34,"quartier_raw":"Les Ormeaux - Maréchal Joffre","etage":"Étage 2","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3213020854","description":""},
    {"source":"lbc","id":"3241893358","price":476,"rooms":2,"surface":32,"quartier_raw":"Le Havre 76600","etage":"RDC","meuble":False,"link":"https://www.leboncoin.fr/ad/locations/3241893358","description":""},
    # === SELOGER ===
    {"source":"seloger","id":"seloger-26Y63QXUDQGJ","price":420,"rooms":2,"surface":22,"quartier_raw":"Sanvic","etage":"RDC/2","meuble":False,"link":"https://www.seloger.com/annonces/locations/appartement/le-havre-76/sanvic/26Y63QXUDQGJ.htm","description":"Sanvic, rue Clément Marical. 22 m². Deux pièces bien agencées. Salle de douche et toilettes séparées."},
    {"source":"seloger","id":"seloger-271834225","price":476,"rooms":2,"surface":31.6,"quartier_raw":"Centre-ville","etage":"2ème étage","meuble":False,"link":"https://www.seloger.com/annonces/locations/appartement/le-havre-76/271834225.htm","description":"114 cours de la république. A LOUER T2, refait à neuf, entrée, salon, cuisine indépendante, 1 chambre, salle de bains avec douche. Classe énergie D, Classe climat A"},
]

def normalize_quartier(q):
    q_lower = q.lower().strip()
    if q_lower in ACCEPTED_QUARTIERS:
        return q_lower
    return SUBQUARTIER_MAP.get(q_lower, None)

results = []
for l in listings:
    if l["price"] > 500:
        continue
    if l["rooms"] < 2:
        continue
    if l["surface"] < 28:
        continue
    quartier = normalize_quartier(l["quartier_raw"])
    if quartier is None:
        continue
    l["quartier"] = quartier
    desc_lower = l.get("description","").lower()
    if "cuisine ouverte" in desc_lower or "cuisine américaine" in desc_lower:
        continue
    lbc_id_alt = f"lbc-{l['id']}" if l["source"] == "lbc" else l["id"]
    if l["id"] in seen_ids or lbc_id_alt in seen_ids:
        continue
    results.append(l)

results.sort(key=lambda x: x["price"])
print(f"=== {len(results)} NEW qualifying listing(s) ===")
for r in results:
    print(json.dumps(r, ensure_ascii=False))

all_ids_this_run = set()
for l in listings:
    all_ids_this_run.add(l["id"])
    if l["source"] == "lbc":
        all_ids_this_run.add(f"lbc-{l['id']}")
print(f"\n=== Total IDs this run: {len(all_ids_this_run)} ===")