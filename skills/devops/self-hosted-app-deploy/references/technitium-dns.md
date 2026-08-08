# Technitium DNS Server — Deployment Notes

## Contexte déploiement Jefe

- **Hôte** : x42 (serveur distant, autre pays que la maison)
- **Accès** : tout via Pangolin (VPS reverse proxy), pas d'accès LAN direct
- **Binding** : `127.0.0.1` sur tous les ports (convention Docker de Jefe)
- **Forwarder** : NextDNS (abonnement payé jusqu'à fin d'abonnement, puis RPZ ou NextDNS gratuit 300k req/mois)
- **DoH** : endpoint `https://dns.jefe.al/dns-query` via Pangolin → x42:53443
- **Clients** : iPhone (4G/wifi), appareils maison (DoH uniquement — pas de DNS simple UDP possible via Pangolin qui ne proxy que TCP)

## Docker Compose (déployé sur x42)

```yaml
services:
  technitium-dns:
    image: technitium/dns-server:latest
    container_name: technitium-dns
    restart: unless-stopped
    ports:
      - "127.0.0.1:53:53/tcp"
      - "127.0.0.1:53:53/udp"
      - "127.0.0.1:53443:53443/tcp"   # DoH + interface web HTTPS
    volumes:
      - ./config:/etc/dns
    environment:
      - DNS_SERVER_DOMAIN=dns.jefe.al
```

**Note** : Le port 53 UDP est bindé en 127.0.0.1 mais inutile dans ce setup — aucun appareil externe ne peut l'atteindre (x42 est dans un autre pays, Pangolin ne proxy pas UDP). Tout passe en DoH sur le 53443.

## Configuration post-déploiement

### 1. Setup wizard
Au premier lancement, Technitium demande de créer un compte admin via l'interface web sur `http://127.0.0.1:53443`.

### 2. NextDNS comme forwarder
Settings → Proxy & Forwarders :
- Forwarder DoH : `https://dns1.nextdns.io/TON_NEXTDNS_ID` (chiffré entre Technitium et NextDNS)
- Ou IP plain : `45.90.92.0` (NextDNS IPv4 primaire) + `45.90.28.0` (secondaire)

### 3. Zones locales
Zones → créer `jefe.al` → ajouter enregistrements A pour les sous-domaines (crm, dns, etc.)

### 4. Pangolin resource
Créer une ressource Pangolin :
- Domaine : `dns.jefe.al`
- Target : `127.0.0.1:53443` (sur le site Newt de x42)
- Protocol : TCP/HTTPS
- SSL : true (Pangolin termine le TLS)

### 5. Profil DNS iOS
Créer un profil DNS sur l'iPhone pointant vers `https://dns.jefe.al/dns-query`.

## Limitations du setup

- **Appareils non-DoH** (TV, IoT) : ne peuvent pas utiliser Technitium. Restent sur DNS du routeur ou NextDNS direct.
- **Port 53 UDP inutile** : bindé en 127.0.0.1 mais inaccessible depuis l'extérieur. Pangolin ne proxy que TCP.
- **RAM** : ~80-110 MB (vs ~15 MB pour AdGuard Home). x42 a les ressources, pas un problème.
- **Latence DNS** : chaque requête fait un aller-retour vers x42 (autre pays) puis vers NextDNS. Le cache local de Technitium compense après le premier hit.

## Version actuelle (août 2026)
- v15.4 (11 juillet 2026)
- .NET 10 runtime
- GPL v3
- SSO OIDC supporté (v15+) — peut s'intégrer avec Pocket ID
- Clustering natif depuis 2025

## Avantages vs AdGuard Home / Pi-hole (pour ce setup)
1. **DNS autoritatif** : héberger `jefe.al` directement (AdGuard/Pi-hole ne le font pas)
2. **DoH server natif** : Pas besoin de reverse proxy supplémentaire pour chiffrer
3. **Clustering natif** : si HA nécessaire plus tard
4. **SSO OIDC** : intégration Pocket ID possible
5. **Tout-en-un** : remplace DNS autoritatif + récursif + filtering + DoH dans un seul conteneur

## Inconvénients vs AdGuard Home / Pi-hole
- 5-7x plus de RAM (~80-110 MB vs ~15 MB)
- Plus lent en QPS (32k vs 48k warm cache)
- Image Docker plus grosse (~200 MB vs ~20 MB)
- Communauté plus petite