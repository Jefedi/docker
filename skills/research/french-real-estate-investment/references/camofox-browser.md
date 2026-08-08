# Camofox Browser — Navigateur Stealth Anti-Détection

> **Port :** `9377` (bind `127.0.0.1`, loopback only — pas d'API key requise)
> **Engine :** Camoufox (Firefox modifié anti-fingerprinting) + Playwright
> **Container :** `camofox-browser` (`ghcr.io/jo-inc/camofox-browser:latest`)
> **Version testée :** 1.13.0 (`@askjo/camofox-browser`)

## Pourquoi Camofox plutôt que curl ou FlareSolverr

- **curl** est bloqué par DataDome (Leboncoin, SeLoger) et Cloudflare (PAP.fr)
- **FlareSolverr** timeout fréquemment sur DataDome (testé 60s timeout sur Leboncoin → échec)
- **Camofox** contourne DataDome ET Cloudflare, avec en plus : snapshot parsé, clic, scroll, evaluate JS

## API — Endpoints essentiels

### Health / Start / Stop
```bash
curl -s http://127.0.0.1:9377/health
# → {"ok":true,"engine":"camoufox","browserConnected":true,...}

curl -s -X POST http://127.0.0.1:9377/start
# → {"ok":true,"profile":"camoufox"}

curl -s -X POST http://127.0.0.1:9377/stop
```

### Workflow complet (open → navigate → snapshot → evaluate → close)
```bash
# 1. Open tab
TAB=$(curl -s -X POST http://127.0.0.1:9377/tabs \
  -H "Content-Type: application/json" \
  -d '{"userId":"hermes-veille","sessionKey":"havre"}' | jq -r .tabId)

# 2. Navigate
curl -s -X POST "http://127.0.0.1:9377/tabs/$TAB/navigate" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.leboncoin.fr/cl/locations/cp_le+havre_76600?price=0-500&rooms=2-","userId":"hermes-veille"}'
# → {"ok":true,"tabId":"...","url":"...","refsAvailable":true}

# 3. Get snapshot (accessibility tree — contient les annonces avec ref IDs)
curl -s "http://127.0.0.1:9377/tabs/$TAB/snapshot?userId=hermes-veille"
# → {"url":"...","snapshot":"- banner:\n  - ...\n- main:\n  - list:\n    - listitem:\n      - article \"Appartement, 2 pièces, 30 mètres carrés.\":\n...","refsCount":55}

# 4. Extract structured data via JS evaluation
curl -s -X POST "http://127.0.0.1:9377/tabs/$TAB/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"userId":"hermes-veille","expression":"document.querySelector(\"script[type=application/ld+json]\")?.textContent || \"{}\""}'

# 5. Click on a listing to see details (ref from snapshot)
curl -s -X POST "http://127.0.0.1:9377/tabs/$TAB/click" \
  -H "Content-Type: application/json" \
  -d '{"userId":"hermes-veille","ref":"e9"}'

# 6. Scroll down for more listings
curl -s -X POST "http://127.0.0.1:9377/tabs/$TAB/scroll" \
  -H "Content-Type: application/json" \
  -d '{"userId":"hermes-veille","direction":"down"}'

# 7. Close tab
curl -s -X DELETE "http://127.0.0.1:9377/tabs/$TAB?userId=hermes-veille"
```

### Autres endpoints utiles
- `POST /tabs/:id/type` — taper du texte dans un champ (ref required)
- `POST /tabs/:id/press` — press keyboard key
- `POST /tabs/:id/back` / `/forward` / `/refresh` — navigation
- `GET /tabs/:id/screenshot` — capture d'écran
- `GET /tabs/:id/links` — extraire tous les liens
- `GET /tabs/:id/images` — extraire images
- `GET /tabs` — lister tous les onglets ouverts

## Sites testés avec succès (août 2026)

| Site | Protection | Camofox | curl seul | FlareSolverr |
|------|-----------|---------|-----------|-------------|
| leboncoin.fr | DataDome | ✅ annonces visibles | ❌ DataDome | ❌ timeout 60s |
| seloger.com | DataDome | ✅ 96 listings | ❌ DataDome | non testé |
| pap.fr | Cloudflare | ✅ (attendu) | ❌ Cloudflare | non testé |
| le-partenaire.fr | Aucune | ✅ | ✅ | ✅ |
| squarehabitat.fr | Aucune | ✅ | ✅ | ✅ |

## Règles d'usage

1. **Toujours `POST /start`** au début d'une session de scraping
2. **Toujours fermer les onglets** (`DELETE /tabs/:id`) après chaque source — fuite mémoire sinon
3. **Toujours `POST /stop`** à la fin — libère le process Firefox
4. Pour les sites **sans protection anti-bot** (Le-Partenaire, SquareHabitat, Citya, Orpi), curl est plus rapide — réserver camofox aux sites bloqués
5. Le snapshot est au format YAML (accessibility tree) — parsable directement, contient les ref IDs `[e1]` pour les interactions
6. `evaluate` permet d'extraire le JSON-LD embarqué dans les pages — utile pour les données structurées (prix, surface, etc.)

## Limitations

- Pas de proxy/VPN — loopback only (contrairement à FlareSolverr derrière gluetun)
- `newPageTimeoutMs: 10000` — timeout court, certains sites lourds peuvent échouer
- RAM : ~120-130 MB au repos + par tab ouvert
- Le browser ne démarre pas automatiquement au boot du container — il faut `POST /start`