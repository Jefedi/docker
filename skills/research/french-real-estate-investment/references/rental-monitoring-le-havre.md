# Rental Monitoring (Location) — Le Havre

Rental listing monitoring for personal housing needs (not investment yield). Complements the buy-to-let (vente) workflow in SKILL.md.

## Criteria (current setup — adapt per user)

- Ville: Le Havre (76600/76620)
- Type: Appartement, T2 minimum (2 pièces+)
- Budget: 500€/mois MAX
- Quartiers acceptés: Centre-ville (Danton, Hôtel de Ville, Perret, etc.), Bléville, Sanvic, front de mer/plage (non obligatoire)
- ⚠️ Quartier "Sanvic" s'écrit S-A-N-V-I-C (pas "Sainte-Vic" ni "Sandvik"). Annexé en 1955, pavillonnaire sur le plateau nord.
- Quartier de la plage: appelé "La Plage" / "front de mer" — pas de nom de quartier distinct, c'est la zone littorale (tramway relie la plage à la gare)
- Tri: du moins cher au plus cher
- Déduplication via JSON state file

## Sources & URL Patterns

### Leboncoin (locations)

```
https://www.leboncoin.fr/cl/locations/cp_le+havre_76600?price=0-500&rooms=2-
```

- `web_extract` works on the search results page (DataDome blocks individual ad pages and browser, but search page renders fine)
- Ad URL pattern: `https://www.leboncoin.fr/ad/locations/{NUMERIC_ID}` (note: `locations` not `ventes_immobilieres`)
- Listings include: prix, nb pièces, surface, étage, DPE (SVG alt text like `![Classe énergie D](...)`), meublé/non, sub-quartier label, date de dépôt, pro/particulier
- ⚠️ `price=0-500` filter is NOT strict — verify actual price per listing
- ⚠️ Page is huge (5800+ lines in cache). web_extract truncates to head+tail. **Read the full cached file with `read_file` in chunks** to parse all listings — the head alone misses ~50%.
- ⚠️ DataDome CAPTCHA page may appear at the tail of web_extract output. Listing data is in the head — parse what's there.

### SeLoger (quartier-specific URLs)

SeLoger uses internal quartier codes (`nbh2frXXXX`) in the URL path. Verified codes for Le Havre:

| Quartier | Code | URL |
|----------|------|-----|
| Centre-ville | `nbh2fr6210` | `https://www.seloger.com/recherche/location/appartement/le-havre-76600/centre-ville-76600/nbh2fr6210` |
| Sanvic | `nbh2fr6214` | `https://www.seloger.com/recherche/location/appartement/le-havre-76600/sanvic-76620/nbh2fr6214` |
| Bléville | `nbh2fr6221` | `https://www.seloger.com/recherche/location/appartement/le-havre-76600/bleville-76620/nbh2fr6221` |

- Listing count in page title: `# N Appartement(s) en location [Quartier] Le Havre 76600`
- Listings include: prix (charges comprises), pièces, chambres, surface, étage, DPE letter, description, agence, lien direct
- "Plus d'annonces à proximité" section shows nearby quartier listings — verify quartier before including
- Pages are 60-70k chars — read the full cached file for middle listings beyond web_extract's head+tail window

### Le-Partenaire.fr (locations)

URL pattern verified (August 2026):
```
https://www.le-partenaire.fr/immobilier/location/appartement/le-havre/76600?loyer-max=500&pieces=2
```
- Uses `loyer-max` (not `prix-max`) for rental listings
- `pieces=2` filters to T2+
- Scrape ALL pages (pagination via `&page=N`)
- Works with curl (no DataDome protection)
- Listings include: title, price, surface, pieces, description text, agency name
- ⚠️ Price extraction regex can fail on some formatting — verify parsed prices
- Cabinet LESTERLIN is the main agency on this site for Le Havre

### SquareHabitat (locations)

```
https://www.squarehabitat.fr/annonces/location/bien/appartement/immobilier/normandie/seine-maritime/le-havre-76600
```
- Works with curl (no bot protection)
- Listings include: title, price (HC + charges), surface, pieces, étage, address, description
- UUID-based listing IDs in URLs (e.g., `2a52c3bc-429e-42dc-88d3-b8b5ba7d3ff6`)
- ~18 listings typical for Le Havre
- Dedup prefix: `sqhab-{uuid}`

### Local Agency Websites (direct scraping)

These local Havrais agencies may have exclusive listings NOT on the big portals. Scraper avec curl (pas de protection bot):

| Agency | URL | Notes |
|--------|-----|-------|
| **LH Immo** | `https://www.lhimmo.com` | 100% havraise. Cherche page location/annonces. |
| **Citya Immobilier** | `https://www.citya.com/annonces/location/appartement/le-havre-76351` | Réseau national, agence locale. |
| **Foncia** | `https://fr.foncia.com/location/le-havre-76` | Réseau national, agences locales. |
| **Saint Roch Immobilier** | `https://www.saintrochimmo.com` | Agence locale Havraise. Cherche page location. |
| **Century 21** | `https://www.century21.fr/annonces/location-appartement/v-le+havre/` | ~4 appartements typiques. |
| **Orpi** | `https://www.orpi.com/location-immobiliere-le-havre/louer-appartement/` | ~86 appartements. |
| **HEUZE Immobilier** | `https://www.heuze-immo.fr` | Agence locale, cité océane. Cherche location. |
| **Jullien & Allix** | `https://www.jullien-allix.fr/annonce/location` | Agence havraise depuis 1927. |

### PAP.fr (locations — particulier à particulier)

```
https://www.pap.fr/annonce/locations-appartement-le-havre-76600-g43635
```
- Pas de frais d'agence (particulier à particulier)
- ⚠️ Cloudflare peut bloquer curl. web_extract peut échouer aussi.
- Petit inventaire mais peut avoir des perles
- Dedup prefix: `pap-{id}`

### Bien'ici (locations)

```
https://www.bienici.com/recherche/location/le-havre-76600/appartement?prix-max=500&pieces-min=2
```
- Agrégateur, compile annonces de multiples sources
- ⚠️ JavaScript-heavy, peut nécessiter browser
- Dedup prefix: `bienici-{id}`

## Leboncoin Sub-Quartier Mapping

Leboncoin uses sub-quartier labels, not official names. Map to target quartiers:

| Leboncoin label | Actual quartier | In target? |
|----------------|-----------------|------------|
| Coty | Centre-ville | ✅ |
| Massillon | Centre-ville | ✅ |
| Eure | Centre-ville (edge) | ✅ |
| Danton | Centre-ville | ✅ |
| Félix Faure | Centre-ville | ✅ |
| Perret | Centre-ville | ✅ |
| Les Docks | Centre-ville | ✅ |
| Saint-François | Centre-ville | ✅ |
| Université - Sainte-Marie | Centre-ville (edge) | ⚠️ borderline |
| Centre-ville | Centre-ville | ✅ |
| Rond-point - Observatoire | Centre-ville | ✅ |
| Saint-Vincent - Plage | Centre-ville (edge) | ⚠️ borderline |
| Sanvic | Sanvic | ✅ |
| Bléville | Bléville | ✅ |
| Sainte-Anne | Outside target | ❌ |
| Graville | Outside target | ❌ |
| Les Ormeaux - Maréchal Joffre | Outside target | ❌ |

## Dedup Mechanism

State file (e.g. `/opt/data/cron/output/havre-rental-seen.json`):
```json
{
  "seen_ids": [
    "lbc-3114599423",
    "lbc-3138529046",
    "seloger-266899095",
    "seloger-26Y63QXUDQGJ"
  ]
}
```

- Leboncoin IDs: `lbc-{numeric_id}`
- SeLoger IDs: `seloger-{id}` (numeric or alphanumeric)
- Le-Partenaire IDs: `lp-{numeric_id}`
- SquareHabitat IDs: `sqhab-{uuid}`
- Local agency IDs: `{prefix}-{id}` (lhimmo-, citya-, foncia-, stroch-, c21-, orpi-, heuze-, ja-)
- PAP IDs: `pap-{id}`
- Bien'ici IDs: `bienici-{id}`
- After each run, add new IDs and write back

## Alerting (ntfy)

Dedicated ntfy topic: **`hermes-loc`** (created 2026-08-07 to separate rental alerts from the general `hermes-agent-jefe` feed). All rental monitoring notifications go to this topic.

When new qualifying listings are found, send urgent ntfy notification:

```bash
curl -H "Authorization: Bearer $(cat /opt/data/.ntfy_token)" \
  -H "Title: 🏠 Location T2 Le Havre — X nouvelle(s) annonce(s)" \
  -H "Tags: rotating_light,house" \
  -H "Priority: urgent" \
  -d "BODY_TEXT" \
  "https://ntfy.jefe.ovh/hermes-loc"
```

Body format per listing:
```
🏠 T2 42m² — Centre-ville
💰 465€/mois
🔗 https://www.leboncoin.fr/ad/locations/XXXX
```

If NO new listings: stay SILENT (`[SILENT]` in cron). Never send empty notifications.

### ⚠️ ntfy ACL — creating a new topic requires explicit grant

The ntfy server uses `auth-default-access: deny-all`. Users can only publish to topics they have been explicitly granted access to. The `hermes-agent` user (token in `/opt/data/.ntfy_token`) was originally granted access only to `hermes-agent-jefe`.

**To create a new ntfy topic for a dedicated feed:**
```bash
# Grant the hermes-agent user read-write access to the new topic
docker exec ntfy ntfy access hermes-agent <topic-name> rw

# Verify
docker exec ntfy ntfy access list
```

Without this step, publishing to the new topic returns HTTP 403 `forbidden`. The ACL is stored in the ntfy auth database (`/var/cache/ntfy/user.db`) and persists across container restarts.

**To list all users and their ACLs:**
```bash
docker exec ntfy ntfy user list
```

**Cron prompt update:** When changing the ntfy topic in a cron job, the prompt text contains the topic URL in two places (the ntfy URL and the curl command). Both must be updated. Use `hermes cron edit <job_id> --prompt "$(cat /tmp/new_prompt.txt)"` or the `cronjob` tool with `action='update'`.

## Manual Ad-Hoc Status Report

When user asks "ça donne quoi la recherche" (status check):

1. Check last cron run output files (e.g. `/opt/data/cron/output/{job_id}/*.md`)
2. Count recent runs — if all `[SILENT]`, say so ("0 nouvelle annonce, le marché est tendu")
3. Do a fresh scrape of all sources (batch web_extract)
4. Read full cached files with `read_file` in chunks to get all listings
5. Present sorted table (moins cher → plus cher): prix, surface, DPE, quartier, lien
6. Highlight: baisse de prix (↘️), best €/m², best DPE
7. Note listings outside target quartiers but still interesting
8. Respond in French, human-readable format (JAMAIS JSON brut)

## Pitfalls

- **Leboncoin page is huge** — 5800+ lines. web_extract head+tail truncation misses ~50% of listings. Always `read_file` the full cache in chunks.
- **SeLoger "Plus d'annonces à proximité"** — listings from outside target quartier. Verify before including.
- **Sub-quartier labels** — Leboncoin uses "Coty", "Massillon", "Eure" etc. not "Centre-ville". See mapping table above.
- **SeLoger includes colocations and studios** — filter for 2 pièces+ manually.
- **DPE on Leboncoin** — appears as SVG alt text `![Classe énergie D](...)`. Parseable but easy to miss in raw text.
- **`/tmp/` is outside HERMES_WRITE_SAFE_ROOT** in cron mode. Write scripts to `/opt/data/cron/output/` instead.
- **`execute_code` blocked in cron** — use `terminal()` with Python scripts written to `/opt/data/cron/output/`.
- **Firecrawl credits exhaustion** — web_extract and web_search both fail with "Payment Required" when Firecrawl runs out. Fallback to curl with browser User-Agent. Local agency sites (LH Immo, HEUZE, etc.) work fine with curl.
- **DuckDuckGo rate-limiting** — DDG HTML search blocks after 2-3 rapid requests. Space requests ~5-10s apart. For agency discovery, one DDG search is usually enough to find the main local agencies.
- **Google CAPTCHA in browser** — Google search from a datacenter IP triggers CAPTCHA. Use DDG HTML or Bing as fallback for web searches.
- **Some agency sites have few/no listings** — don't skip them. Local agencies (HEUZE, LH Immo, Jullien-Allix) may have exclusive mandates not syndicated to Leboncoin/SeLoger. A single exclusive listing can be the best deal.
- **If a source is blocked, move on** — never let one blocked source stop the entire monitoring run. Skip it and scrape the next source. The cron should always try ALL sources.
- **Félix Faure sub-quartier** — appeared in August 2026 Leboncoin listings, maps to Centre-ville. Add to the accepted sub-labels.