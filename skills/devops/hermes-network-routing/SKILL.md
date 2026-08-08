---
name: hermes-network-routing
description: Basculer entre Tailscale et routage direct (Pangolin/public) pour accéder aux services internes. Ce skill documente le mutex entre Tailscale et pangolin-cli.
version: 1.0.0
author: Jefe
platforms: [linux]
---

# Hermes Network Routing

Résout les problèmes d'accès aux services internes derrière Pangolin + Tailscale.
Le VPS Hermes a Tailscale **et** pangolin-cli mais ils sont mutuellement exclusifs.

## Contexte

- Tailscale donne accès direct aux IPs 100.64.0.x (homelab)
- Pangolin expose des domaines *.jefe.ovh via le client CLI
- **Mutex**: quand Tailscale est up, les domaines Pangolin ne routent pas correctement
  (retournent "Private Placeholder Screen" de Pangolin au lieu du service)
- Solution: down Tailscale → accès via domaine Pangolin
- Retour: down Tailscale + restart pangolin-cli → accès IP directe Tailscale

## Commandes

### Basculer vers Pangolin/public (down Tailscale)
```bash
tailscale down
# Attendre 2-3s que le DNS se propage
# Les domaines *.jefe.ovh sont maintenant accessibles
```

### Basculer vers Tailscale (up)
```bash
tailscale up --accept-dns=false --accept-routes --login-server=https://heand.jefe.ovh
# Les IPs 100.64.0.x sont maintenant accessibles
```

### Arrêt complet + restart pangolin-cli
```bash
# 1. Down Tailscale
tailscale down

# 2. Kill pangolin-cli (si besoin)
kill $(pgrep -f pangolin-cli) 2>/dev/null

# 3. Restart pangolin-cli Docker
docker restart pangolin-cli

# 4. Re-up Tailscale
tailscale up --accept-dns=false --accept-routes --login-server=https://heand.jefe.ovh
```

## Services connus

| Service | Domaine/public | IP Tailscale | Port |
|---|---|---|---|
| Profilarr | profilarr.jefe.ovh | 100.64.0.2 | 6868 |
| Radarr | via Arr stack | 100.64.0.2 | 7878 |
| Sonarr | via Arr stack | 100.64.0.2 | 8989 |
| Home Assistant | homeassistant.jefe.ovh | 100.64.0.8 | 8123 |

## Vérification

### Test si Tailscale est actif
```bash
tailscale status
```

### Test si un service répond
```bash
# Via domaine (Pangolin)
curl -s -o /dev/null -w "%{http_code}" https://profilarr.jefe.ovh/api/v1/health

# Via IP directe (Tailscale)
curl -s -o /dev/null -w "%{http_code}" http://100.64.0.2:6868/api/v1/health
```

## Pitfalls

- Ne pas oublier de remonter Tailscale après avoir fini avec Pangolin — les cron jobs et autres services peuvent en dépendre
- Quand Tailscale est down, les accès aux IPs 100.64.0.x ne marchent plus
- Le pangolin-cli tourne en Docker et se restart automatiquement après `tailscale down` et `kill`
