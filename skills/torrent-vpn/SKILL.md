---
name: torrent-vpn
description: >
  Torrent et VPN documentation expert. Covers qBittorrent (client torrent, WebUI, v5.x), Gluetun (VPN client Docker, WireGuard/OpenVPN, port forwarding, ProtonVPN), cross-seed (injection automatique de torrents cross-seed). Trigger words: qbittorrent, qbit, torrent, gluetun, vpn, wireguard, openvpn, protonvpn, port forwarding, cross-seed, injection, tracker, seed.
---

# Torrent-VPN Documentation Skill

## Mental Model

torrent-vpn = 3 composants en chaîne. **Gluetun** (conteneur VPN) → **qBittorrent** (client torrent routé via VPN) → **cross-seed** (recherche et injection de torrents matchant la bibliothèque existante). Gluetun gère le tunnel WireGuard/OpenVPN, le kill-switch firewall, et le port forwarding (ProtonVPN). qBittorrent télécharge via le réseau VPN. cross-seed surveille la bibliothèque et injecte des torrents correspondants pour booster le ratio. Le tout dans Docker avec des mounts `/data` partagés.

- **Gluetun** est le point d'entrée réseau. Tous les conteneurs qui doivent passer par le VPN utilisent `network_mode: "service:gluetun"`. Gluetun gère le kill-switch: si le VPN droppe, tout le trafic est bloqué.
- **qBittorrent** est connecté à Gluetun. Son port WebUI (8080) est exposé sur le conteneur Gluetun, pas sur qBittorrent lui-même. Le port forwarding du VPN est passé à qBittorrent via un hook (`VPN_PORT_FORWARDING_UP_COMMAND`).
- **cross-seed** s'interface avec qBittorrent via l'API WebUI pour injecter des torrents de cross-seed. Il partage le même mount `/data` pour le data-based matching et le linking.

## Routing Table

Load the reference file that matches the question domain. Always open the file before answering.

### qBittorrent

| Question domain | Reference file |
|---|---|
| qBittorrent overview, home | `qbt__home.md` |
| Bind qBittorrent to VPN (prevent IP leaks) | `qbt__how-to-bind-your-vpn-to-prevent-ip-leaks.md` |
| Anonymous mode | `qbt__anonymous-mode.md` |
| WebUI HTTPS with Let's Encrypt (NGINX) | `qbt__linux-webui-https-with-let's-encrypt-certificates-and-nginx-ssl-reverse-proxy.md` |
| WebUI HTTPS with Let's Encrypt (standalone) | `qbt__linux-webui-setting-up-https-with-let's-encrypt-certificates.md` |
| WebUI HTTPS with Caddy2 | `qbt__linux-webui-https-with-let's-encrypt-&-caddy2-reverse-proxy.md` |
| WebUI HTTPS self-signed | `qbt__linux-webui-setting-up-https-with-self-signed-ssl-certificates.md` |
| UI lock password recovery | `qbt__i-forgot-my-ui-lock-password.md` |
| Web UI password locked (nox) | `qbt__web-ui-password-locked-on-qbittorrent-no-x-(qbittorrent-nox).md` |
| OpenVPN + qBittorrent without X server | `qbt__openvpn-and-qbittorrent-without-x-server.md` |
| Running without X server (WebUI only) | `qbt__running-qbittorrent-without-x-server-(webui-only).md` |
| Running without X server (systemd, Ubuntu 15.04+) | `qbt__running-qbittorrent-without-x-server-(webui-only,-systemd-service-set-up,-ubuntu-15.04-or-newer).md` |
| WebUI API v5.0 (current) | `qbt__webui-api-(qbittorrent-5.0).md` |
| WebUI API v4.1 | `qbt__webui-api-(qbittorrent-4.1).md` |
| WebUI API v3.x | `qbt__webui-api-(qbittorrent-v3.1.x).md`, `qbt__webui-api-(qbittorrent-v3.2.0-v4.0.4).md` |
| API Key Authentication (≥v5.2.0) | `qbt__api-key-authentication-(≥v5.2.0).md` |
| Alternate WebUIs | `qbt__list-of-known-alternate-webuis.md`, `qbt__alternate-webui-usage.md` |
| Developing alternate WebUIs | `qbt__developing-alternate-webuis-(wip).md` |
| Custom themes | `qbt__create-custom-themes-for-qbittorrent.md`, `qbt__how-to-use-custom-ui-themes.md`, `qbt__list-of-known-qbittorrent-themes.md` |
| Portable mode | `qbt__how-to-use-portable-mode.md` |
| Disable DHT, PeX, LPD | `qbt__how-to-disable-dht,-pex,-and-lpd.md` |
| Disable auto-seed | `qbt__how-to-disable-auto-seed.md` |
| Disable connections not supported by proxies | `qbt__disable-connections-not-supported-by-proxies.md` |
| qBittorrent as tracker | `qbt__how-to-use-qbittorrent-as-a-tracker.md` |
| Speed issues | `qbt__qbittorrent-is-not-downloading-or-uploading-is-it-slow.md`, `qbt__things-we-need-to-know-to-help-you-with-'speed'-issues.md` |
| Missing files at startup | `qbt__status-of-missing-files-at-start-up-or-after-restart.md` |
| IO errors / crashes | `qbt__how-to-diagnose-io-errors.md`, `qbt__how-to-diagnose-io-error,-bsod,-crash-(windows).md`, `qbt__how-to-diagnostic-io-error,-bsod,-crash-[gnu-linux,-bsd,-etc.].md` |
| Reverse proxy (NGINX) | `qbt__nginx-reverse-proxy-for-web-ui.md` |
| Reverse proxy (Traefik) | `qbt__traefik-reverse-proxy-for-web-ui.md` |
| Reverse proxy (IIS ARR) | `qbt__iis-arr-reverse-proxy.md` |
| External programs | `qbt__external-programs-how-to.md`, `qbt__external-programs-savecategory.md` |
| Search plugins | `qbt__unofficial-search-plugins.md` |
| Unofficial WebAPI clients | `qbt__list-of-unofficial-webapi-clients.md` |
| GeoIP database | `qbt__how-to-use-maxmind's-geoip-database.md` |
| Installing qBittorrent | `qbt__installing-qbittorrent.md` |
| Compilation guides | `qbt__compilation-*.md` |

### Gluetun

| Question domain | Reference file |
|---|---|
| Gluetun overview / README | `gluetun__readme.md`, `gluetun__setup__readme.md` |
| Setup guide (WireGuard) | `gluetun__setup__wireguard.md` |
| Setup guide (AmneziaWG) | `gluetun__setup__amneziawg.md` |
| OpenVPN config file | `gluetun__setup__openvpn-configuration-file.md` |
| Connect a container to Gluetun | `gluetun__setup__connect-a-container-to-gluetun.md` |
| Connect a LAN device to Gluetun | `gluetun__setup__connect-a-lan-device-to-gluetun.md` |
| Port mapping (Docker) | `gluetun__setup__port-mapping.md` |
| Inter-container networking | `gluetun__setup__inter-containers-networking.md` |
| Popular apps setup | `gluetun__setup__popular-apps.md` |
| Docker image tags | `gluetun__setup__docker-image-tags.md` |
| Servers (filtering, selection) | `gluetun__setup__servers.md` |
| Test your setup | `gluetun__setup__test-your-setup.md` |
| Prerequisites (32bit, Synology) | `gluetun__setup__prerequisites__32bit.md`, `gluetun__setup__prerequisites__synology.md` |
| **VPN port forwarding (guide)** | `gluetun__setup__advanced__vpn-port-forwarding.md` |
| Port forwarding options (env vars) | `gluetun__setup__options__port-forwarding.md` |
| Control server (API) | `gluetun__setup__advanced__control-server.md`, `gluetun__setup__options__control-server.md` |
| WireGuard advanced | `gluetun__setup__advanced__wireguard.md`, `gluetun__setup__options__wireguard.md` |
| OpenVPN advanced (certs, keys) | `gluetun__setup__advanced__openvpn-client-certificate.md`, `gluetun__setup__advanced__openvpn-client-encrypted-key.md`, `gluetun__setup__advanced__openvpn-client-key.md` |
| OpenVPN options | `gluetun__setup__options__openvpn.md` |
| DNS options | `gluetun__setup__options__dns.md` |
| Firewall options | `gluetun__setup__options__firewall.md` |
| Healthcheck options | `gluetun__setup__options__healthcheck.md` |
| HTTP proxy | `gluetun__setup__options__http-proxy.md` |
| Shadowsocks | `gluetun__setup__options__shadowsocks.md` |
| Storage options | `gluetun__setup__options__storage.md` |
| Updater options | `gluetun__setup__options__updater.md` |
| VPN options (general) | `gluetun__setup__options__vpn.md` |
| IPv6 | `gluetun__setup__advanced__ipv6.md` |
| Docker secrets | `gluetun__setup__advanced__docker-secrets.md` |
| Kubernetes | `gluetun__setup__advanced__kubernetes.md` |
| Multiple Gluetun instances | `gluetun__setup__advanced__multiple-gluetun.md` |
| AmneziaWG options | `gluetun__setup__options__amneziawg.md` |
| Other options | `gluetun__setup__options__others.md` |
| **ProtonVPN setup** | `gluetun__setup__providers__protonvpn.md` |
| PIA setup | `gluetun__setup__providers__private-internet-access.md` |
| Other providers | `gluetun__setup__providers__*.md` |
| Custom provider | `gluetun__setup__providers__custom.md` |
| Firewall errors | `gluetun__errors__firewall.md` |
| OpenVPN errors | `gluetun__errors__openvpn.md` |
| Routing errors | `gluetun__errors__routing.md` |
| TUN errors | `gluetun__errors__tun.md` |
| Errors overview | `gluetun__errors__readme.md` |
| FAQ — bandwidth | `gluetun__faq__bandwidth.md` |
| FAQ — firewall | `gluetun__faq__firewall.md` |
| FAQ — healthcheck | `gluetun__faq__healthcheck.md` |
| FAQ — WireGuard | `gluetun__faq__wireguard.md` |
| FAQ — others | `gluetun__faq__others.md` |
| FAQ overview | `gluetun__faq__readme.md` |
| Contributing | `gluetun__contributing__*.md` |

### cross-seed

| Question domain | Reference file |
|---|---|
| cross-seed options (all settings) | `crossseed__basics__options.md` |
| Docker Compose setup | `crossseed__basics___docker-compose.md` |
| Common setup failures | `crossseed__basics__common-setup-failures.md` |
| FAQ & troubleshooting | `crossseed__basics__faq-troubleshooting.md` |
| Windows setup | `crossseed__basics__windows.md` |
| **Direct client injection** | `crossseed__tutorials__injection.md` |
| **Data-based matching** | `crossseed__tutorials__data-based-matching.md` |
| **Partial matching** | `crossseed__tutorials__partial-matching.md` |
| Linking (hardlinks, symlinks) | `crossseed__tutorials__linking.md` |
| Announce (IRC announces) | `crossseed__tutorials__announce.md` |
| ID searching | `crossseed__tutorials__id-searching.md` |
| Triggering searches | `crossseed__tutorials__triggering-searches.md` |
| Unraid setup | `crossseed__tutorials__unraid.md` |
| API reference | `crossseed__reference__api.md` |
| Architecture | `crossseed__reference__architecture.md` |
| Tracker impact | `crossseed__reference__tracker-impact.md` |
| Utils (CLI commands) | `crossseed__reference__utils.md` |
| v4 migration guide | `crossseed__legacy__v4-migration-guide.md` |
| v6 migration guide | `crossseed__v6-migration.md` |

### Field Knowledge

| Question domain | Reference file |
|---|---|
| **Jefe's field knowledge (gotchas)** | `00-gotchas-jefe.md` |

## Behavior Rule

**Never answer from memory about a configuration option, default value, or API field.** Always open the corresponding reference file and cite the exact value. If the answer is not in the reference files or the gotchas file, say so explicitly. Do not invent.

## Validation Questions

### Q1: Comment connecter qBittorrent à Gluetun pour que tout le trafic passe par le VPN ?

D'après `gluetun__setup__connect-a-container-to-gluetun.md`, il faut ajouter
`network_mode: "service:gluetun"` au conteneur qBittorrent dans le docker-compose.
Aucune section `depends_on` n'est nécessaire. Le port WebUI de qBittorrent (8080)
doit être exposé sur le conteneur **Gluetun** (section `ports` de Gluetun), pas
sur qBittorrent — voir `gluetun__setup__port-mapping.md`. Pour une connexion
externe (autre docker-compose), utiliser `network_mode: "container:gluetun"`.

Voir aussi `00-gotchas-jefe.md` → "qBittorrent WebUI Derrière Gluetun" pour le
docker-compose exact du setup de Jefe.

### Q2 (contre-intuitive): Pourquoi mon port forwarding ProtonVPN ne fonctionne pas alors que Gluetun affiche "connected" ?

Le VPN être "connected" ne suffit pas. D'après `gluetun__setup__options__port-forwarding.md`
et `gluetun__setup__providers__protonvpn.md`, le port forwarding requiert:

1. `VPN_PORT_FORWARDING=on` (la valeur est `on`, pas `enabled` — défaut: `off`)
2. Pour OpenVPN: ajouter `+pmp` au username OpenVPN (pas nécessaire en WireGuard)
3. Le port forwardé doit être passé à qBittorrent via un hook
   `VPN_PORT_FORWARDING_UP_COMMAND` — pas juste via le fichier
   `/tmp/gluetun/forwarded_port`

Le hook documenté dans `gluetun__setup__advanced__vpn-port-forwarding.md` appelle
l'API qBittorrent `setPreferences` avec le port forwardé. Requiert: WebUI sur
port 8080 + `bypass_local_auth` activé dans qBittorrent.

Sans ce hook, qBittorrent ne connaît pas le port forwardé et continue d'écouter
sur son port par défaut — les peers ne peuvent pas se connecter en incoming.

### Q3: cross-seed peut-il matcher des torrents qui ne sont pas exactement identiques à ma bibliothèque ?

Oui. D'après `crossseed__tutorials__partial-matching.md`, cross-seed v6 supporte
le **partial matching** via `matchMode: "partial"`. Ce mode ne requiert qu'une
correspondance partielle des fichiers (les petits fichiers comme `.nfo`, `.srt`
ou les samples peuvent différer). Cela peut doubler le nombre de cross-seeds
trouvés.

De plus, `crossseed__tutorials__data-based-matching.md` décrit le **data-based
matching** qui permet de matcher à partir des fichiers sur disque (sans avoir
besoin du fichier `.torrent` original), en analysant les données réelles.

Configuration clé pour le partial matching:
- `matchMode: "partial"` (défaut: `"strict"`)
- `fuzzySizeThreshold: 0.02` (2% de variance, défaut)
- Nécessite linking activé (`crossseed__tutorials__linking.md`)
- `seasonFromEpisodes` < 1 pour cross-seed des season packs incomplets