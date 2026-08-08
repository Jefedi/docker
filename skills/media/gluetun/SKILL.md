---
name: gluetun
description: Client VPN multi-fournisseurs en conteneur Docker. WireGuard/OpenVPN, port forwarding, DNS over TLS.
category: media
---

# Gluetun — Guide de référence

> **Site :** https://github.com/qdm12/gluetun  
> **Image :** `qmcgaw/gluetun`  
> **Port healthcheck :** `8080` (interne)

Client VPN dans un conteneur Docker, supportant de multiples fournisseurs VPN. Utilisé comme point d'entrée réseau pour les autres conteneurs via `network_mode: service:gluetun`.

---

## 1. Configuration Docker Compose

```yaml
  gluetun:
    image: qmcgaw/gluetun
    container_name: gluetun
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun:/dev/net/tun
    ports:
      - "127.0.0.1:PORT:PORT"      # Accès local
      - "100.64.0.2:PORT:PORT"     # Accès Tailscale/réseau secondaire
    volumes:
      - ./configs/gluetun:/gluetun
    environment:
      - VPN_SERVICE_PROVIDER=protonvpn
      - VPN_TYPE=wireguard
      - WIREGUARD_PRIVATE_KEY=${WIREGUARD_PRIVATE_KEY}
      - SERVER_COUNTRIES=Switzerland,Netherlands,Sweden,Iceland
      # Port forwarding (ProtonVPN)
      - VPN_PORT_FORWARDING=on
      - VPN_PORT_FORWARDING_UP_COMMAND=/bin/sh -c '...'
    restart: unless-stopped
```

## 2. Variables d'environnement

| Variable | Description |
|---|---|
| `VPN_SERVICE_PROVIDER` | `protonvpn`, `mullvad`, `nordvpn`, `pia`, `windscribe`, etc. |
| `VPN_TYPE` | `wireguard` ou `openvpn` |
| `WIREGUARD_PRIVATE_KEY` | Clé privée WireGuard |
| `SERVER_COUNTRIES` | Liste de pays séparés par des virgules |
| `VPN_PORT_FORWARDING` | `on` ou `off` (ProtonVPN, Mullvad...) |
| `VPN_PORT_FORWARDING_UP_COMMAND` | Commande exécutée quand le port forward est mis à jour |

## 3. Conteneurs derrière Gluetun

Les services qui doivent passer par le VPN utilisent :
```yaml
  service_name:
    network_mode: service:gluetun
    depends_on:
      gluetun:
        condition: service_healthy
```

Les ports des services derrière Gluetun doivent être **déclarés dans Gluetun**, pas dans le service lui-même.

## 4. Périphériques réseau secondaire

Pour exposer des ports sur une IP secondaire (ex: Tailscale `100.64.0.2`) :
```yaml
      - "100.64.0.2:8989:8989"
      - "127.0.0.1:8989:8989"
```
