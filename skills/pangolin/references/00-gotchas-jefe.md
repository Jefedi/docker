# Pangolin — Field Knowledge (Jefe's Infrastructure)

Savoir terrain absent de la doc officielle, compilé depuis les skills existantes
(`pangolin-proxy-wizard`, `homelab-mesh-connect`, `service-removal`) et sessions passées.

## Infrastructure Map

| Site ID | Name | newtId | Machine | IP |
|---------|------|--------|---------|-----|
| 28 | Hermes VPN | `fjuyrsrb09ufxq3` | VPS Hermes Agent | 178.105.179.232 |
| 6 | Hetzner | `ist4scbqlgo0yvc` | Hetzner server | 37.27.126.113 |
| 18 | Jnas | `jxwosr4te0n24bs` | NAS | 100.64.0.3 |
| 1 | homeassistant | `5dz1vc8kmn5fj6y` | HA VM | 100.64.0.8 |
| 29 | jTower | `Y7/khtREIx/Kygi2VbLxFQuSXyolwiPHcoeExBn2vAw=` | Windows daily driver | 192.168.1.12 |

| Domain | Domain ID | Usage |
|--------|-----------|-------|
| `*.jefe.al` | `domain2` (changes after restart — verify via API) | Internal services |
| `*.jefe.ovh` | `domain1` | Secondary (n8n, arr stack) |
| `*.losgalactique.fr` | `51vbysoaydeg6cr` | Public (Pterodactyl, Paymenter) |
| `*.trakii.tv` | `domain4` | Trakii project |

- API base: `https://api.jefe.ovh/v1`
- Org: `jorganisation`
- Pangolin dashboard: `https://pangolin.jefe.ovh`
- API key: stored in `/opt/data/.env` as `PANGOLIN_API_KEY` (also `~/.hermes/*.txt` historically)

## Critical: Three-Layer Pattern for HTTP Resources on Newt Sites

**Creating a public resource + target is NOT sufficient for HTTP services on a Newt site.**
You MUST also create a **site resource** — otherwise the Newt client never gets the
routing rule to forward traffic from the exit node to the local service.

| Layer | What it does | API call |
|-------|-------------|----------|
| Public resource (org) | DNS, SSL, auth config | `PUT /org/{orgId}/resource` |
| Target (on resource) | Tells Pangolin WHERE to forward | `PUT /resource/{id}/target` |
| Site resource (on site) | Tells Newt HOW to route from exit node | `PUT /org/{orgId}/site-resource` |

**Symptoms of missing site resource:** "no available server" to authenticated users,
Newt logs show `Started tcp proxy to 127.0.0.1:PORT` but NO `Added target subnet` line.

## Critical: Tailscale Conflict on Dual-Mesh Hosts

If Tailscale runs on the same host as the Pangolin CLI client (Olm), its `ts-input`
iptables chain drops all CGNAT return traffic from the `pangolin` interface.

**Fix:**
```bash
iptables -I ts-input 1 -i pangolin -j ACCEPT
```

Without this, the mesh shows connected but all private resource traffic times out silently.

## Critical: Site Identification

**Never assume the site from a hostname.** Docker containers can have generic hostnames.
Always check external IP first:
```bash
curl -s https://api.ipify.org
# 37.27.126.113 → site 6 (Hetzner)
# 178.105.179.232 → site 28 (Hermes VPN)
```
Then cross-reference with `cat /root/.config/newt-client/config.json` (look for `id` field)
against the Pangolin sites API.

## Newt Tunnel Auto-Start & Restart Danger

The Newt tunnel does NOT auto-start after reboot. Recovery:
```bash
newt client  # or systemctl restart newt-client
# Wait ~3s for "Tunnel connection established"
```

If the Newt tunnel is down, targets through that site return **504 Gateway Timeout**.

**⚠️ DANGER: Unrestart Newt peut casser le tunnel WireGuard** (`WireGuard device
is not initialized` + `timed out` sur `wg/register`). Le problème est côté VPS
Pangolin (Gerbil relay), pas côté Newt. Fix: restart le stack Pangolin entier
sur le VPS : `docker compose down && docker compose up -d`. Newt récupère le
tunnel automatiquement après.

## Broken API Endpoint

`PUT org/{orgId}/site/{siteId}/resource` is broken — always returns
"Validation error: Unrecognized key: 'siteId'" regardless of body. Do NOT use it.

## Target IP Choice

- Site 28 (Newt on same machine): use `127.0.0.1` (loopback, more secure)
- Other sites: use their local IPs (e.g. `100.64.0.9`)
- If Newt tunnel is DOWN: use public IP as TEMPORARY workaround only

## SSO Consistency for Dev Subdomains

When creating a dev subdomain (e.g. `dev.trakii.tv`) on an existing domain, check the
parent resource's `sso` field first. If parent has `sso: false`, the dev subdomain
should also have `sso: false` — otherwise Pocket-ID auth is required on dev but not prod.

## Newt Restart After New Resource

After creating a brand-new resource + target, the Newt client on the target site may
need a restart to discover it:
```bash
systemctl restart newt-client && sleep 5
journalctl -u newt-client --since "5 seconds ago" | grep "Added target subnet"
```
Not needed when updating an existing target's port/IP — Newt picks those up within seconds.

## Windows Client : Conflit DNS avec YogaDNS / autres intercepteurs DNS

**Symptôme :** Le client Pangolin est connecté, `dnsOverride: true` activé, l'interface
Pangolin a bien son DNS (`100.96.128.1`), mais les ressources privées affichent
l'écran "Ce domaine est utilisé sur une ressource privée" — le navigateur ne passe
pas par le tunnel.

**Cause :** Un intercepteur DNS tiers (YogaDNS, YandexDNS, etc.) s'intercale au-dessus
du DNS système et capte toutes les requêtes **avant** Pangolin. Pangolin ne voit jamais
les requêtes pour les domaines privés → pas de résolution en IP de tunnel → le
navigateur se connecte à l'IP publique → Traefik affiche l'écran de maintenance.

**Diagnostic :**
1. `Get-Process | Where-Object { $_.Name -like "*yoga*" -or $_.Name -like "*dns*" }`
2. Vérifier `netsh interface ip show dns` — si l'interface Pangolin a bien `100.96.128.1`
   mais qu'un process DNS tourne encore, c'est lui le coupable.
3. Vérifier aussi le DoH du navigateur (Chrome/Edge/Firefox) qui peut contourner le
   DNS système.

**Fix :**
1. `Stop-Process -Name "YogaDNS" -Force` (ou équivalent)
2. Désactiver le démarrage auto (Task Manager → Startup ou settings de l'app)
3. `ipconfig /flushdns`
4. Fermer/rouvrir complètement le navigateur (vider cache DNS navigateur)

**Note :** Technitium DNS sur le serveur n'est PAS concerné — il continue de tourner
pour les autres appareils. Le conflit est local au client Windows. NextDNS peut être
utilisé comme upstream Pangolin (`primaryDNS`) pour garder les blocklists.

**Config Pangolin Windows qui marche :**
```json
{
  "dnsOverride": true,
  "dnsTunnel": false,
  "primaryDNS": "45.90.28.167",
  "mtu": 1280
}
```

## Windows Client : Coexistence YogaDNS + Pangolin (solution finale)

Il EST possible de garder YogaDNS ET Pangolin ensemble. La solution : créer des
règles **Bypass** dans YogaDNS pour les domaines Pangolin. Le bypass laisse la
requête DNS passer au DNS système (Pangolin), qui la résout en IP de tunnel.

**Configuration YogaDNS :**
1. Configuration → Rules → Add pour chaque domaine Pangolin :
   - `*.jefe.al` → Action: Bypass
   - `*.jefe.ovh` → Action: Bypass
   - `*.losgalactique.fr` → Action: Bypass
   - `*.trakii.tv` → Action: Bypass
2. Placer ces règles **au-dessus** de la règle Default (bouton Up)
3. La règle Default garde Technitium DoH (dns.jefe.al) pour tout le reste
4. Désactiver le DoH du navigateur (Chrome/Edge/Firefox) qui contourne le DNS système

**Résultat :**
- Domaines privés → Bypass → Pangolin → tunnel WireGuard ✅
- Tout le reste → YogaDNS → Technitium DoH → filtrage/blocklists ✅
- dns.jefe.al lui-même est bypass (résolu par Pangolin vers IP publique) puis
  YogaDNS s'y connecte en DoH normalement — le filtrage n'est pas cassé.

**Note :** Technitium sur le serveur ne peut PAS résoudre les domaines privés à la
place de Pangolin — les IPs de tunnel sont dynamiques et locales au client. Le
bypass YogaDNS est la seule solution.

## TODO: Wildcard Certs DNS-01 Cloudflare

The doc covers wildcard domains with Traefik DNS-01 challenges in
`self-host__advanced__wild-card-domains.md`. Jefe's setup uses Cloudflare for DNS.
TODO: document the exact Cloudflare API token permissions needed and the
`config/traefik/dynamic_config.yml` entries for Cloudflare DNS-01.

## TODO: CrowdSec + Traefik Log Rotation

Doc: `self-host__community-guides__crowdsec.md` + `self-host__advanced__traefik-log-rotation.md`.
TODO: document Jefe's CrowdSec deployment specifics (bouncers, decisions, Traefik middleware).

## TODO: Raw TCP/UDP Resources

Doc: `manage__resources__public__raw-resources.md`.
TODO: document Jefe's TCP/UDP raw resource usage (Wings/Pterodactyl ports, game servers).

## Path-Based Routing + Strip Prefix (Multi-Service on One Domain)

On peut servir plusieurs services backend sur un **même domaine** (ex: `hermes.jefe.al`)
en utilisant le **path-based routing** sur les targets. Exemple concret :

- **Target 1** : `localhost:9120` (dashboard Hermes) — pas de path match (catch-all)
- **Target 2** : `localhost:9119` (API Hermes) — Path: `/api`, Match: `prefix`, Rewrite: `stripPrefix`

Résultat :
- `hermes.jefe.al/` → dashboard (port 9120)
- `hermes.jefe.al/api/v1/responses` → `localhost:9119/v1/responses` (le `/api` est retiré)

**Étapes dans l'UI Pangolin :**
1. Sur la ressource existante, ajouter un nouveau target
2. Configurer l'IP/port du backend API
3. **Type de correspondance** = `prefix`
4. **Path** = `/api`
5. **Type de réécriture** = `Retirer le préfixe` (Strip Prefix)
6. Sauvegarder

**Piège :** Sans le Path Rewriting (Strip Prefix), Pangolin match bien le path mais
l'envoie tel quel au backend (ex: `/api/v1/responses` arrive sur Hermes qui retourne 404
parce qu'il attend `/v1/responses`). Le strip prefix est une étape **séparée** du path match.

**Vérification rapide :**
```bash
# Si strip prefix fonctionne, on obtient 200 (pas 404)
curl -s -o /dev/null -w "%{http_code}" -X POST "https://hermes.jefe.al/api/v1/responses" \
  -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{"input":"test"}'
```

## TODO: Gerbil / Without-Tunneling Mode

Doc: `self-host__advanced__without-tunneling.md`.
TODO: document if Jefe uses Pangolin as local-only reverse proxy on any host.

## Technitium DNS Server (dns.jefe.al)

| Élément | Valeur |
|---------|--------|
| Resource ID | 127 |
| Target 1 (DoH) | ID 152, port 8053, path `/dns-query`, prefix, priority 100 |
| Target 2 (Dashboard+API) | ID 153, port 5380, catch-all, priority 50 |
| Site resource ID | 52, ports `5380,8053` |
| API token | In Vaultwarden ("Technitium DNS API Token") |
| Forwarder | NextDNS DoH `https://dns1.nextdns.io/d3d958` |
| Blocklists | StevenBlack, URLhaus, AdGuard (auto-update 24h) |
| DNSSEC | Validation activé |
| DoH endpoint | `https://dns.jefe.al/dns-query` |

**⚠️ NE JAMAIS restart Newt pour Technitium** — le tunnel WireGuard peut casser.
Si `WireGuard device is not initialized` : restart le stack Pangolin entier sur le VPS.
Voir skill `technitium-dns` pour la procédure complète.