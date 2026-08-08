---
name: european-car-search
description: Recherche de véhicules d'occasion sur les plateformes européennes (AutoScout24, mobile.de, leboncoin, La Centrale, LeParking, 2ememain). Approche multi-pays (FR, DE, BE, NL).
trigger: L'utilisateur cherche à acheter un véhicule d'occasion en Europe, ou demande une comparaison de prix entre marchés européens.
---

# European Car Search Skill

## Stratégie générale

1. **Identifier les plateformes cibles** selon les pays demandés :
   - France : AutoScout24.fr, leboncoin.fr, LaCentrale.fr, LeParking.fr
   - Allemagne : AutoScout24.de, mobile.de
   - Belgique : AutoScout24.be, 2ememain.be
   - Europe large : AutoScout24.com, LeParking.fr (paramètre pays), TheParking.eu

2. **Pour chaque plateforme**, procéder en 2 temps :
   - **Étape A** : `web_search(query="site:...")` pour confirmer que la plateforme existe et découvrir l'URL de recherche
   - **Étape B** : `web_extract(urls=[...])` avec l'URL de recherche filtrée (prix, année, etc.)
   - **Étape C (si nécessaire)** : Utiliser le navigateur pour les pages JS lourdes (leboncoin, mobile.de) qui ne rendent pas correctement les résultats filtrés via web_extract

3. **Compiler** TOUTE annonce trouvée dans le budget, même si elle dépasse légèrement. Lister : prix, année, kilométrage, localisation, lien direct.

## Paramètres d'URL par plateforme

Voir `references/url-parameters.md` pour la syntaxe détaillée de chaque plateforme.

## Pièges & Antipatterns

- **mobile.de** : le filtre prix est souvent ignoré par le moteur de rendu — utiliser `webSearchRequest` dans l'URL avec `maxPrice` et `minFirstRegDate`. Même avec ça, les résultats peuvent inclure des voitures bien au-dessus du budget. Toujours vérifier.
- **leboncoin.fr** : le filtre prix + année ne fonctionne pas correctement via web_extract — les résultats affichés sont souvent des annonces non filtrées. Utiliser le navigateur si nécessaire, ou noter que le résultat est peu fiable.
- **LeParking** : les annonces sponsorisées en tête de page ne respectent PAS les filtres. Descendre dans la page ou trier par prix pour voir les vraies annonces dans le budget.
- **La Centrale** : le filtre `priceMax` est fréquemment ignoré — ne pas se fier aux annonces affichées. Vérifier manuellement.
- **AutoScout24 France (re=2015)** : le paramètre `re=2015` semble signifier "inclure 2015" plutôt que "à partir de 2015" sur certaines sous-pages. Sur les pages avec `priceto=...`, le filtre année est parfois relâché pour montrer plus de résultats.
- **AutoScout24.com (Europe wide)** : le `re=` filtre est régulièrement ignoré quand combiné avec `priceto=`. Vérifier manuellement les années.
- **Annonces US sur LeParking** : LeParking agrège aussi des annonces américaines. Vérifier la localisation. Une voiture US à importer coûte cher (douane, homologation, modification des feux).

## Vérification des résultats

Après avoir collecté les annonces avec web_extract, toujours vérifier :
1. Que l'année est bien >= 2015 (le filtre peut ne pas s'appliquer)
2. Que le prix est bien dans le budget (certaines pages ignorent le filtre)
3. Que la localisation est en Europe (pas US, Japon, etc.)

## Format de réponse

Pour l'utilisateur (Jefe) — privilégier :
- Français
- Concis, sans blabla
- Liens en texte brut (copiables sur mobile)
- Tableau simple pour les annonces
- Si aucune annonce, dire clairement le prix de départ du marché

