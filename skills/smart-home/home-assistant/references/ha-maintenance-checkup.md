# HA Maintenance — vérification des mises à jour

Workflow pour vérifier toutes les mises à jour disponibles : HA (addons, core), système (APT), conteneurs Docker, Hermes Agent.

## 1. HA Updates (via MCP)

```json
{
    "name": "ha_get_updates",
    "arguments": {}
}
```

Retourne `updates[]` avec `title`, `installed_version`, `latest_version`, `can_install`.

Pour installer une mise à jour :

```json
{
    "name": "ha_call_service",
    "arguments": {
        "domain": "update",
        "service": "install",
        "entity_id": "update.ntfy_jefe_ovh_ntfy_version"
    }
}
```

**Piège** : certaines entités `update.*` sont des conteneurs Docker ou des services non gérés par HA supervisor. L'appel `update.install` échoue en 500 — l'entité est monitor-only. Vérifier avant avec `ha_get_state(entity_id="update.xxx")` → si `supported_features` ne contient pas le bit d'install, c'est read-only.

## 2. APT packages (système)

```bash
# Lister les mises à jour disponibles
apt list --upgradable 2>/dev/null | grep -v "^Listing..."

# Installer
apt update -qq && apt upgrade -y <paquet1> <paquet2>
```

**Piège** : `apt list --upgradable` sans `2>/dev/null` affiche un header "Listing..." qui pollue le parsing.

## 3. Docker images (hôte local)

```bash
# Lister les images qui ont un tag (versionné, pas <none>)
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

Pour les conteneurs gérés via Dockhand sur hôtes distants :

```json
mcp_dockhand_dockhand_list_containers(environment_id=N)
```

**Piège** : Dockhand peut être injoignable depuis le VM Hermes (connection refused) — dépend du réseau tailscale.

## 4. Hermes Agent (auto)

```bash
# Voir la version et si une mise à jour est dispo
hermes --version
# → Affiche "Up to date" ou "N commits behind — run 'hermes update'"

# Mettre à jour
hermes update
# → Pull les commits, met à jour les dépendances Python + Node, rebuild la WebUI
```

**Piège** : `hermes update` peut timeout si le build Vite de la WebUI est lent (>120s). Le paquet Python est déjà installé à ce stade — seul le build UI est incomplet. Relancer `hermes dashboard --skip-build` ou attendre le prochain démarrage.

## 5. Vérification finale

```bash
# APT
apt list --upgradable 2>/dev/null | grep -v "^Listing..." && echo "Aucune" || true

# Docker version
docker --version

# Hermes version
hermes --version 2>&1 | head -1
```
