---
name: technitium-dns
description: Technitium DNS behind Pangolin with DoH and iOS profile.
---

# Technitium DNS Server derrière Pangolin

## Architecture

```
Client (iPhone/Firefox) ──DoH──→ Pangolin (TLS) ──HTTP──→ Technitium (x42)
                                                              ↓
                                                         NextDNS (forwarder)
```

Pangolin termine le TLS. Technitium reçoit du HTTP plain. Le DoH fonctionne
sur le port DNS-over-HTTP (pas HTTPS) de Technitium.

⚠️ **NE PAS créer de zones locales** si Technitium est sur un serveur distant
behind Pangolin. Les services ne sont pas en localhost pour les clients externes.
Les zones locales n'ont de sens que si Technitium est sur le même réseau que les
services qu'il résout. L'utilisateur l'a fait remarquer clairement.

## Docker Compose

```yaml
services:
  technitium-dns:
    image: technitium/dns-server:latest
    container_name: technitium-dns
    restart: unless-stopped
    ports:
      - "127.0.0.1:53:53/tcp"
      - "127.0.0.1:53:53/udp"
      - "127.0.0.1:5380:5380/tcp"    # Web console HTTP + API
      - "127.0.0.1:53443:53443/tcp"  # DoH HTTPS natif (non utilisé derrière proxy)
      - "127.0.0.1:8053:8053/tcp"    # DNS-over-HTTP (DoH behind proxy)
    volumes:
      - ./config:/etc/dns
    environment:
      - DNS_SERVER_DOMAIN=dns.jefe.al
```

⚠️ Port 5380 = web console + API. Port 8053 = DoH HTTP. Port 53443 = DoH HTTPS natif.
Derrière un reverse proxy, utiliser 8053 (DNS-over-HTTP) car le proxy termine le TLS.

## Configuration Technitium (ordre important)

### 1. Settings → Optional Protocols

- ✅ Cocher `Enable dns-over-HTTP protocol`
- DNS-over-HTTP Port → **8053**
- ❌ Décocher `Enable Redirect to Help Page` (setting: `enableDnsOverHttpHelpRedirect=false`)
  - Le 302 est normal pour les navigateurs. Le DoH répond 200 avec header `Accept: application/dns-message`.
- Reverse Proxy Network ACL → `0.0.0.0/0` et `::/0` (restreindre après)
- Real IP Header → `X-Real-IP`

### 2. Settings → Recursion

- Sélectionner **Allow Recursion** (pas "Only For Private Networks")
  - ⚠️ Restreindre avec ACL plus tard pour éviter DNS ouvert

### 3. Settings → Proxy & Forwarders

- NextDNS : `https://dns1.nextdns.io/d3d958` (DoH chiffré) ou IP `45.90.92.0` et `45.90.28.0`
- Protocol : HTTPS (chiffré entre Technitium et NextDNS)

### 4. Blocking (RPZ + Blocklists)

Configuré via API : `settings/set?blockListUrls=URL1,URL2,URL3`
- `enableBlocking=true` (déjà activé par défaut)
- `blockingType=NxDomain` (réponse NXDOMAIN pour les domaines bloqués)
- `blockListUpdateIntervalHours=24` (mise à jour auto toutes les 24h)

Listes recommandées :
- `https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts` (pubs + trackers)
- `https://urlhaus.abuse.ch/downloads/hostfile/` (malware)
- `https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt` (ads)

### 5. DNSSEC

Déjà activé par défaut : `dnssecValidation=true`. Protège contre le DNS spoofing.

## API Technitium (v15+)

⚠️ **TOUJOURS lire la doc officielle avant de deviner les endpoints.**
Doc : https://github.com/TechnitiumSoftware/DnsServer/blob/master/APIDOCS.md

Voir `references/api-reference.md` pour la liste complète des endpoints validés.

### Authentification

Header : `Authorization: Bearer <token>`
Ou query param : `?token=<token>`

Le token se crée via l'UI : Administration → API Tokens → Create Token.
Le token a les mêmes permissions que l'utilisateur qui l'a créé.

⚠️ **Piège** : Avec un token valide, les endpoints inexistants retournent **404**
(sans body). Avec un token invalide, les endpoints existants retournent **200**
avec `{"status":"invalid-token"}`. Ne pas confondre un 404 (mauvais endpoint)
avec un problème de token.

### Endpoints clés (CORRECTS — vérifiés sur la doc officielle)

| Action | Endpoint | Méthode |
|--------|----------|---------|
| Status | `/api/status` | GET |
| Login | `/api/user/login?user=admin&pass=XXX` | GET/POST |
| Session info | `/api/user/session/get` | GET |
| Lister zones | `/api/zones/list` | GET |
| Créer zone | `/api/zones/create?zone=jefe.al&type=Primary` | GET/POST |
| Supprimer zone | `/api/zones/delete?zone=jefe.al` | POST |
| Ajouter record | `/api/zones/records/add?zone=jefe.al&domain=x.jefe.al&type=A&value=1.2.3.4&ttl=3600` | GET/POST |
| Lister blocked | `/api/blocked/list` | GET |
| Ajouter blocked | `/api/blocked/add?domain=ads.com` | POST |
| Get settings | `/api/settings/get` | GET |
| Set settings | `/api/settings/set?key=value&key2=value2` | POST |
| Dashboard stats | `/api/dashboard/stats/get?type=LastHour` | GET |

⚠️ **MAUVAIS endpoints** (retournent 404, ne pas utiliser) :
- ~~`/api/zone/getZones`~~ → utiliser `/api/zones/list`
- ~~`/api/zone/createZone`~~ → utiliser `/api/zones/create`
- ~~`/api/user/info`~~ → utiliser `/api/user/session/get`
- ~~`/api/blocking/addBlocklist`~~ → utiliser `/api/settings/set?blockListUrls=...`

### Configurer settings via API

```
POST /api/settings/set?blockListUrls=URL1,URL2,URL3
POST /api/settings/set?forwarders=https://dns1.nextdns.io/ID&forwarderProtocol=Https
POST /api/settings/set?enableBlocking=true&blockingType=NxDomain
```

⚠️ `settings/set` **écrase** la valeur. Pour ajouter un forwarder sans écraser
les existants, récupérer d'abord la liste avec `settings/get` puis renvoyer
la liste complète. **Ne pas mettre de placeholder comme `TON_ID`** — récupérer
la vraie valeur d'abord.

## Configuration Pangolin (3 couches)

### Ressource publique + 2 targets avec path routing

- Target 1 (DoH, priorité 100) : port 8053, path `/dns-query`, pathMatchType `prefix`
- Target 2 (Dashboard + API, priorité 50) : port 5380, catch-all

### Site resource (OBLIGATOIRE)

- tcpPortRangeString doit inclure TOUS les ports : `5380,8053`

## ⚠️ Newt restart DANGER

**NE JAMAIS restart Newt sans raison valable.** Un `docker restart newt` peut casser
le tunnel WireGuard : `WireGuard device is not initialized` + `timed out` sur
`wg/register` + `wg/get-config`. Tous les services du site deviennent inaccessibles.

Si ça arrive :
1. Vérifier `docker logs newt` — si `WireGuard device is not initialized`
2. Le problème est côté **VPS Pangolin** (Gerbil relay), pas côté Newt
3. **Restart le stack Pangolin entier sur le VPS** : `docker compose down && docker compose up -d`
4. Patienter ~15s, Newt récupère le tunnel automatiquement

Un restart Newt n'est nécessaire que pour découvrir de **nouveaux** ports dans la
site resource. Même dans ce cas, vérifier d'abord si Newt a déjà picked up les
changements (logs `Added target subnet`).

## ⚠️ Domain IDs Pangolin — ne pas faire confiance au cache

Les domain IDs changent après un restart du stack Pangolin. Toujours récupérer le
`domainId` actuel via `GET /org/{orgId}/resources` et lire le champ `domainId` d'une
ressource existante sur le même domaine. Ne pas utiliser d'IDs cachés ni d'IDs du
fichier de gotchas Pangolin — ils peuvent être obsolètes.

Exemple : `*.jefe.al` était `ykx3vzina5zahuf`, est devenu `domain2` après restart.

## Profil iOS (.mobileconfig)

Le champ s'appelle `DNSProtocol` (pas `DNSSettingsType`).
`PayloadScope` = `System` obligatoire pour 4G/cellular.
Structure : `DNSSettings` dict → `DNSProtocol`, `ServerAddresses`, `ServerURL`.

## Test DoH

```bash
curl -s -H "Accept: application/dns-message" \
  "https://dns.jefe.al/dns-query?dns=EjQBAAABAAAAAAAAB2V4YW1wbGUDY29tAAABAAE=" \
  -o /dev/null -w "%{http_code} %{content_type}"
# Doit retourner: 200 application/dns-message
```

## Pièges

| Erreur | Solution |
|--------|----------|
| "DoH supported only on HTTPS" | ACL Reverse Proxy + `0.0.0.0/0` `::/0` |
| 302 sur /dns-query | `enableDnsOverHttpHelpRedirect=false` via settings/set |
| 403 Forbidden | ACL Reverse Proxy |
| 404 sur /dns-query | Port 8053 pas exposé dans Docker |
| 404 sur /api/* | Mauvais endpoint — lire APIDOCS.md officielle |
| 502 Bad Gateway | Port target Pangolin ≠ port Technitium |
| Newt tunnel cassé | Restart stack Pangolin sur VPS (pas juste Newt) |
| iOS "DNSSettings manquant" | Champ = `DNSProtocol` pas `DNSSettingsType` |
| iOS "profil non valid" | Manque `PayloadScope` = `System` |
| Domain ID not found | IDs changent après restart Pangolin → lister resources |
| settings/set écrase config | Récupérer valeurs existantes avec settings/get d'abord |

## Reset mot de passe admin

```bash
docker stop technitium-dns && docker rm technitium-dns
rm -rf /srv/docker/technitium-dns/config/*
docker compose up -d
```

## Infra Jefe

| Élément | Valeur |
|---------|--------|
| Serveur | x42 (Hetzner, 37.27.126.113) |
| Site Pangolin | 6 |
| Domaine | *.jefe.al (domainId: domain2 — verify, changes after restart) |
| API Pangolin | https://api.jefe.ovh/v1 |
| Org | jorganisation |
| Dashboard | https://dns.jefe.al |
| DoH | https://dns.jefe.al/dns-query |
| Forwarder | NextDNS (HTTPS) |
| Blocklists | StevenBlack, URLhaus, AdGuard |
| API token | Stocké dans Vaultwarden |
| Vaultwarden | https://vault.jefe.al (hermesagent@jefe.ovh) |

## Support files

- `references/api-reference.md` — API endpoints validés, pièges, discussion GitHub
- `templates/technitium-dns-jefe.mobileconfig` — iOS DoH profile template