# Homelab Inventory — Jefe

## Nodes

| Node | Hardware | OS | Headscale IP | SSH | Rôle |
|------|----------|-----|-------------|-----|------|
| AX42 | Hetzner dedicated, Ryzen 7 PRO 8700GE, 64GB RAM | Debian Trixie | 100.64.0.2 | port 2242 (port 22 = endlessh tarpit) | Docker principal, Hermes, n8n, services |
| jNas | UGREEN DXP4800 Plus | TrueNAS SCALE | 100.64.0.4 | port 4235, user ax42 | Stockage, Immich, backups Borg |
| VPS CX23 | Hetzner cloud | Debian | 100.64.0.1 | — | Pangolin (reverse proxy, wildcard TLS) |
| Pi HA | Raspberry Pi 4 | HAOS | 100.64.0.8 | — | Home Assistant |
| jTower | Desktop | Windows | LAN 192.168.1.12 | — | Daily driver (migrated from Zorin OS 18.1) |

## Domaines

- `jefe.al`, `jefe.ovh`, `losgalactique.fr` — wildcard Cloudflare → VPS Pangolin
- Tous les services exposés via Pangolin (jamais IP publique directe)

## Services sur AX42

n8n, Immich, FreshRSS, Overseerr, ntfy, Paperless-ngx, Obsidian (LiveSync), Radicale (ical.jefe.al), Termix, SearXNG (search.jefe.al), Hermes Agent (Docker), LiteLLM proxy, Qdrant

## Services sur jNas

Immich (restored from Borg backup after ST6000DM003 disk failure), TrueNAS SCALE storage

## Infrastructure clé

- **Pangolin VPS** : wildcard TLS via Cloudflare DNS-01. Resource hermes.jefe.al → 127.0.0.1:9120 (dashboard), /api → 9119 (API server). SSO off.
- **Headscale mesh** : ACL + Headplane configurés. VPS=100.64.0.1, AX42=100.64.0.2, jNas=100.64.0.4, Pi HA=100.64.0.8, iPhone15ProMax=100.64.0.3.
- **Borgmatic backup** : multi-node, sub1-sub4 Hetzner Storage Box par node. Repo ~97GB. Passphrase: /root/.borg-passphrase (raw) + /root/.borg-passphrase.env (systemd K= format).
- **Hermes Docker** : network_mode:host, NO socket. Dashboard=9120, API=9119.
- **LiteLLM proxy** : 127.0.0.1:4000, route tout le trafic LLM. Master key sur l'hôte (inaccessible depuis container Hermes).

## ntfy

- URL: `ntfy.jefe.ovh/hermes-agent-jefe`
- Auth: Bearer token dans `/opt/data/.ntfy_token`
- **JAMAIS restart Hermes sans confirmation explicite**

## iOS Shortcut

- POST `/v1/responses` sur l'API Hermes
- HA `todo.add_item` sur `todo.liste_dachats` (liste de courses)

## n8n Workflows (IDs)

| Workflow | ID | Notes |
|----------|----|-------|
| iCal sync | `4CP4NStyjt7YhD25` | Radicale CalDAV |
| Trakt | `6DfjzsWXe4I0u5os` | — |
| RSS | `JAWwQaCUx1mN0IA7` | LoKan feed nécessite `/feed/` (301 sans slash) |
| WorkTime | `SJK4U7fWFyufakNF` | — |
| Spotify sync | `IDq7NyfY6iXAdvzj` | 2 branches (Liked Tracks + Artists), daily 8h — voir skill `spotify-library-management` |

## Cron veille immobilière (Le Havre)

T2+, ≤500€, Centre-ville / Bléville / Saint-Vincent. Notifs ntfy urgent.