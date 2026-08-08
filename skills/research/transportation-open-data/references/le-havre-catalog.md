# Le Havre Seine Métropole — Full Open Data Catalog

## Portal

**URL**: https://data.lehavreseinemetropole.fr/
**Licence**: ODbL
**Total datasets**: 169 (as of July 2026)
**Platform**: Custom (jQuery-based, not OpenDataSoft)

## API discovery technique

The portal is a jQuery SPA that loads datasets via AJAX. The API is not documented but can be reverse-engineered:

1. Open browser console on the portal
2. Find `afficheData()` function in `script.min.js`
3. API endpoints follow this pattern:
   - Count: `api/v1/datas/search/{query}/theme/{theme}/count`
   - List: `api/v1/datas/search/{query}/theme/{theme}/?offset={n}&limit={n}`
   - Replace `coll` with `"PMES"` for the default collection
4. Response format is **XML** (not JSON despite `$.getJSON` — jQuery auto-parses XML+JSON content-type)
5. Use `%20` for spaces in URL path segments

```bash
curl -s -o /tmp/lh_data.json 'https://data.lehavreseinemetropole.fr/api/v1/datas/search/%20/theme/%20/?offset=0&limit=169'
```

Then parse with Python `xml.etree.ElementTree`.

## Catalog by category (169 datasets)

### Voirie transport et déplacement (17 datasets) — ALL semestrielle or annuelle
| Dataset | Fréquence | Gestionnaire |
|---|---|---|
| Accessibilité - Stationnement PMR | Semestrielle | Voirie Urbaine et Stationnement |
| Accessibilité - Traversées piétonnes sonorisées | Semestrielle | Voirie Urbaine et Stationnement |
| Aménagements linéaires de modération de vitesse | Semestrielle | Direction Voirie et Mobilité |
| Bornes de recharge électrique | Semestrielle | Direction Voirie et Mobilité |
| Emplacements de stationnement automobile | Semestrielle | Direction Voirie et Mobilité |
| Equipements du vélo | Semestrielle | Direction Voirie et Mobilité |
| Itinéraires de substitution | Semestrielle | Direction Voirie et Mobilité |
| Panneaux d'entrée et sortie de ville | Semestrielle | Direction Voirie et Mobilité |
| Parcs de stationnement | Semestrielle | Direction Voirie et Mobilité |
| Règlement de la circulation | Semestrielle | Direction Voirie et Mobilité |
| Réseau cyclable | Semestrielle | Direction Voirie et Mobilité |
| Stationnement - Horodateur | Annuelle | Direction surveillance espaces publics |
| Stationnement - Zone | Semestrielle | SIGU & Topographie |
| Transport en commun LIA - Arrêts | Semestrielle | Direction Voirie et Mobilité |
| Transports scolaires - arrêts | Annuelle | Direction Voirie et Mobilité |
| Tronçons de stationnement payant | Semestrielle | Direction Voirie et Mobilité |
| Zones de circulation apaisée | Semestrielle | Direction Voirie et Mobilité |

### Other categories (summary)
- **Budget et Finance**: 40 datasets (budgets, comptes administratifs 2014-2026)
- **Citoyenneté**: 18 (bureaux de vote, cantons, circonscriptions, panneaux affichage)
- **Économie Urbanisme et Habitat**: 31 (PLU, permis de construire 2010-2020, occupation du sol historique)
- **Environnement et cadre de vie**: 25 (bruit, espaces verts, déchets, canisites, cimetières)
- **Référentiel géographique**: 19 (adresses, bâtiments, voirie, courbes de niveau, communes)
- **Services au public**: 11 (écoles, collèges, défibrillateurs, structures petite enfance)
- **Culture tourisme sport**: 6 (circuits patrimoine, randonnée, sites remarquables)
- **Imagerie**: 2 (ortho 2014, photo aérienne 1947)

## Key finding

**Zero real-time data.** All datasets are semestrielle at best. No traffic state, no signal timing, no real-time mobility data. The closest relevant static datasets are:
- "Itinéraires de substitution" — likely bypass routes, static
- "Règlement de la circulation" — traffic regulations (one-way, restrictions), static
- "Zones de circulation apaisée" — zone 30 areas, static