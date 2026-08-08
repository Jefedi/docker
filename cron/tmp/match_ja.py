import re

content = open('/tmp/ja.html').read()
links = re.findall(r'href="/annonce-immobiliere/(a-louer-[^"]+)"', content)
unique_links = list(dict.fromkeys(links))

listings = [
    {"title": "F3 HARFLEUR Centre Ville", "slug_hint": "f3-harfleur-centre-ville"},
    {"title": "MEUBLE F2 Marechal Joffre", "slug_hint": "meuble-de-type-f2-le-havre-marechal-joffre"},
    {"title": "F3 Quartier Mazeline", "slug_hint": "type-f3-le-havre-quartier-mazeline"},
    {"title": "F2 COTE OUEST LES ORMEAUX", "slug_hint": "f2-le-havre-cote-ouest-les-ormeaux"},
    {"title": "F2 Centre Ville 27 rue du Chillou", "slug_hint": "f2-le-havre-centre-ville"},
]

for l in listings:
    found = None
    for link in unique_links:
        if l['slug_hint'] in link:
            found = link
            break
    if not found:
        for link in unique_links:
            words = l['slug_hint'].split('-')
            if all(w in link for w in words[:3]):
                found = link
                break
    l['slug'] = found
    print(f"{l['title']} -> {found}")