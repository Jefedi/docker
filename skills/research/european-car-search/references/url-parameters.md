# URL Parameters pour les plateformes de recherche auto

## AutoScout24 (FR / DE / BE / .com)

Base URL: `https://www.autoscout24.{tld}/lst/audi/a7`

| Paramètre | Valeur | Effet |
|---|---|---|
| `sort=price` | — | Tri par prix croissant |
| `priceto=11500` | nombre | Prix max |
| `cy=D` | D, F, B, NL, A | Pays (DE, FR, BE, NL, AT) |
| `re=2015` | année | Première immatriculation (année simple : semble signifier "inclure cette année" et non "à partir de") |
| `atype=C` | C | Voitures d'occasion |
| `ocs_listing=include` | include | Inclure les annonces avec kilométrage inconnu |

URL type tous filtres : `https://www.autoscout24.de/lst/audi/a7?sort=price&priceto=11500&cy=D&re=2015&atype=C&ocs_listing=include`

⚠️ AutoScout24.com (européen) : le `re=` est souvent ignoré quand combiné avec `priceto=`. Vérifier manuellement les années.

## mobile.de

Base URL: `https://suchen.mobile.de/auto/audi-a7.html`

| Paramètre | Valeur | Effet |
|---|---|---|
| `isSearchRequest=true` | true | Active la recherche avancée |
| `sort=price` | price | Tri par prix |
| `maxPrice=11500` | nombre | Prix max |
| `minFirstRegDate=2015-01` | YYYY-MM | Première immatriculation min |

URL type : `https://suchen.mobile.de/auto/audi-a7.html?isSearchRequest=true&sort=price&maxPrice=11500&minFirstRegDate=2015-01`

⚠️ Le filtre prix est souvent ignoré. Vérifier les résultats manuellement.
⚠️ Le prix de départ du marché pour une A7 2015+ est ~18 600-20 000 €.

## leboncoin.fr

Base URL: `https://www.leboncoin.fr/c/voitures`

| Paramètre | Valeur | Effet |
|---|---|---|
| `car_brand=AUDI` | — | Marque |
| `car_model=AUDI_A7` | — | Modèle |
| `price=0-11500` | min-max | Fourchette de prix |
| `regdate=2015-min` | YYYY-min | Année minimum |

URL type : `https://www.leboncoin.fr/c/voitures?car_brand=AUDI&car_model=AUDI_A7&price=0-11500&regdate=2015-min`

⚠️ Les filtres ne sont pas toujours respectés — les résultats peuvent montrer des annonces hors-critères. Utiliser le navigateur si web_extract ne fonctionne pas.

## La Centrale

Base URL: `https://www.lacentrale.fr/occasion-voiture-modele-audi-a7.html`

| Paramètre | Valeur | Effet |
|---|---|---|
| `priceMax=11500` | nombre | Prix max |
| `yearMin=2015` | année | Année minimum |

URL type : `https://www.lacentrale.fr/occasion-voiture-modele-audi-a7.html?priceMax=11500&yearMin=2015`

⚠️ Le filtre priceMax est fréquemment ignoré. Ne pas se fier aux annonces affichées.

## LeParking

Base URL: `https://www.leparking.fr/voiture-occasion/audi-a7-sportback.html`

| Paramètre | Valeur | Effet |
|---|---|---|
| `priceMax=11500` | nombre | Prix max |
| `yearMin=2015` | année | Année minimum |

URL type : `https://www.leparking.fr/voiture-occasion/audi-a7-sportback.html?priceMax=11500&yearMin=2015`

Variantes :
- `audi-a7.html` (tous modèles A7)
- `audi-a7-sportback.html` (uniquement Sportback)
- `audi-a7-sportback-2015.html` (spécifique 2015)

⚠️ Les annonces sponsorisées en tête ne respectent PAS les filtres.
⚠️ LeParking agrège des annonces du monde entier — vérifier la localisation. Une voiture US nécessite importation.

## 2ememain.be (Belgique)

Base URL: `https://www.2ememain.be/l/autos/audi/f/a7/583/`

| Paramètre | Valeur | Effet |
|---|---|---|
| `priceTo=11500` | nombre | Prix max |
| `yearFrom=2015` | année | Année minimum |

URL type : `https://www.2ememain.be/l/autos/audi/f/a7/583/?priceTo=11500&yearFrom=2015`

⚠️ Le filtre `yearFrom` n'existe pas toujours — essayer sans ou avec `yearFrom`.
