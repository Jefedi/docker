# Technitium DNS — API Reference (v15+)

Source: https://github.com/TechnitiumSoftware/DnsServer/blob/master/APIDOCS.md

## Authentication

Header : `Authorization: Bearer <token>`
Query param : `?token=<token>` (backward compat)

Le token se crée via l'UI : Administration → API Tokens → Create Token.
Le token a les mêmes permissions que l'utilisateur qui l'a créé.

⚠️ **Piège diagnostique** : Avec un token valide, les endpoints inexistants
retournent **404** (content-length 0, pas de body). Avec un token invalide,
les endpoints existants retournent **200** avec `{"status":"invalid-token"}`.
Ne pas confondre un 404 (mauvais endpoint) avec un problème de token.
Pour vérifier que l'API est vivante : `curl -s http://127.0.0.1:5380/api/status`
→ doit retourner 200 sans auth.

## Endpoints validés (testés et fonctionnels)

### User

| Action | Endpoint | Params |
|--------|----------|--------|
| Status | `GET /api/status` | aucun (pas d'auth requis) |
| Login | `GET/POST /api/user/login` | `user`, `pass`, `includeInfo` (opt) |
| Session info | `GET /api/user/session/get` | auth |
| Create token | `GET/POST /api/user/createToken` | `tokenName`, ou `user`+`pass` |
| Logout | `POST /api/user/logout` | auth |
| Profile | `GET /api/user/profile/get` | auth |

### Zones

| Action | Endpoint | Params |
|--------|----------|--------|
| List zones | `GET /api/zones/list` | `pageNumber`, `zonesPerPage`, `filterName`, `filterType` (opt) |
| Create zone | `GET/POST /api/zones/create` | `zone`, `type` (Primary/Secondary/Stub/Forwarder) |
| Delete zone | `POST /api/zones/delete` | `zone` |
| Export zone | `GET /api/zones/export` | `zone` |
| Import zone | `POST /api/zones/import` | `zone`, `overwrite` (opt) |

### Records

| Action | Endpoint | Params |
|--------|----------|--------|
| Add record | `GET/POST /api/zones/records/add` | `zone`, `domain`, `type`, `value`, `ttl` |

Exemple :
```
POST /api/zones/records/add?zone=jefe.al&domain=crm.jefe.al&type=A&value=127.0.0.1&ttl=3600
```

### Blocked (domains manuels)

| Action | Endpoint | Params |
|--------|----------|--------|
| List blocked | `GET /api/blocked/list` | auth |
| Add blocked | `POST /api/blocked/add` | `domain` |
| Import blocked | `POST /api/blocked/import` | `blockedZones` |

### Settings

| Action | Endpoint | Params |
|--------|----------|--------|
| Get settings | `GET /api/settings/get` | auth |
| Set settings | `POST /api/settings/set` | key=value pairs (voir ci-dessous) |

### Dashboard

| Action | Endpoint | Params |
|--------|----------|--------|
| Stats | `GET /api/dashboard/stats/get` | `type` (LastHour/LastDay/LastWeek/LastMonth), `utc` |
| Top stats | `GET /api/dashboard/stats/getTop` | `type`, `statsType` (TopClients/TopDomains/TopBlockedDomains) |
| Metrics JSON | `GET /api/dashboard/metrics/json` | auth |

## Settings keys (via /api/settings/set)

| Key | Type | Description |
|-----|------|-------------|
| `blockListUrls` | comma-separated URLs | Blocklists externes (écrase !) |
| `enableBlocking` | bool | Activer le blocking |
| `blockingType` | string | `NxDomain` ou `CustomAddress` |
| `forwarders` | comma-separated | Forwarders externes (écrase !) |
| `forwarderProtocol` | string | `Udp`, `Tcp`, `Tls`, `Https`, `Quic` |
| `dnssecValidation` | bool | Validation DNSSEC |
| `recursion` | string | `Deny`, `Allow`, `AllowOnlyForPrivateNetworks`, `UseSpecifiedNetworkACL` |
| `enableDnsOverHttp` | bool | Activer DoH-over-HTTP |
| `dnsOverHttpPort` | int | Port DoH HTTP (default 8053) |
| `enableDnsOverHttpHelpRedirect` | bool | Rediriger /dns-query vers page d'aide |
| `dnsReverseProxyNetworkACL` | comma-separated CIDR | ACL pour reverse proxy |

⚠️ **`settings/set` écrase la valeur**. Pour modifier sans perdre la config
existante, faire d'abord `settings/get`, lire la valeur, puis renvoyer la
liste complète avec la modification.

## Endpoints QUI N'EXISTENT PAS (retournent 404)

- ~~`/api/zone/getZones`~~ → utiliser `/api/zones/list`
- ~~`/api/zone/createZone`~~ → utiliser `/api/zones/create`
- ~~`/api/zone/addRecord`~~ → utiliser `/api/zones/records/add`
- ~~`/api/user/info`~~ → utiliser `/api/user/session/get`
- ~~`/api/blocking/addBlocklist`~~ → utiliser `/api/settings/set?blockListUrls=...`
- ~~`/api/dashboard/getStats`~~ → utiliser `/api/dashboard/stats/get`
- ~~`/api/settings/setForwarders`~~ → utiliser `/api/settings/set?forwarders=...`

## Discussion GitHub : DoH avec Pangolin

https://github.com/TechnitiumSoftware/DnsServer/discussions/1586

Key findings :
1. TLS termination at Pangolin → use DNS-over-HTTP (plain) port, not DNS-over-HTTPS
2. Reverse Proxy Network ACL must include the proxy's IP range (`0.0.0.0/0` pour tester)
3. "Allow Recursion" must be set to "Allow All" (not just private networks)
4. 302 redirect on /dns-query is normal for browsers; DoH clients with proper
   Accept header get 200
5. Enable Redirect to Help Page must be disabled for DoH-only use