# 📅 Calendrier CalDAV Unifié — Radicale + n8n + HA + iOS

## Architecture

```
┌─────────┐    CalDAV natif    ┌───────────┐
│  iOS    │ ←────────────────→ │  Radicale │
│ Calendar│    (calendrier)    │  (CalDAV) │
│ + Tasks │    (tâches VTODO)  │  port 5232│
└─────────┘                    └─────┬─────┘
                                     │
                              ┌──────┴──────┐
                              │   n8n sync  │
                              │  (5 min)    │
                              └──────┬──────┘
                                     │
┌─────────────────┐                  │
│ Home Assistant  │←─────────────────┘
│ calendar entity │  CalDAV integration (calendrier)
│ todo entities   │  API sync (tâches via n8n)
└─────────────────┘
```

## Étape 1: Déployer Radicale sur jTower

### 1.1 Créer les fichiers sur le jTower

```bash
ssh jefedi@jtower
mkdir -p ~/radicale/{data,config}
cd ~/radicale
```

### 1.2 docker-compose.yml

```yaml
version: "3.8"
services:
  radicale:
    image: tomsquest/docker-radicale:latest
    container_name: radicale
    restart: unless-stopped
    ports:
      - "5232:5232"
    volumes:
      - ./data:/data
      - ./config:/config:ro
    environment:
      - TZ=Europe/Paris
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5232"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 1.3 Config Radicale

Fichier `~/radicale/config/config`:

```ini
[server]
hosts = 0.0.0.0:5232
max_connections = 20
max_content_length = 10000000
timeout = 60
ssl = false

[auth]
type = htpasswd
htpasswd_filename = /config/users
htpasswd_encryption = bcrypt
auth_delay = 3s

[storage]
type = multifilesystem
filesystem_folder = /data/collections
max_sync_token_age = 2592000
filesystem_fsync = True

[rights]
type = authenticated

[logging]
level = info

[headers]
Access-Control-Allow-Origin = *
Access-Control-Allow-Methods = GET, POST, PUT, DELETE, OPTIONS, PROPFIND, REPORT
Access-Control-Allow-Headers = Authorization, Content-Type, Depth, If-Match, If-None-Match
```

### 1.4 Créer l'utilisateur

```bash
# Installer htpasswd si nécessaire
sudo apt install apache2-utils

# Créer le fichier users avec ton user
htpasswd -cB ~/radicale/config/users jefe
# (entrer le mot de passe)

chmod 644 ~/radicale/config/users
```

### 1.5 Démarrer

```bash
cd ~/radicale
docker compose up -d
docker compose logs -f
```

### 1.6 Créer les collections

Depuis un navigateur, aller sur `http://jtower:5232` (ou IP locale)
- Se connecter avec `jefe` + mot de passe
- Créer 2 collections:
  1. **calendar** → Type: Calendar (VCALENDAR/VEVENT)
  2. **tasks** → Type: Task List (VCALENDAR/VTODO)

## Étape 2: Exposer via Pangolin

Créer un target Pangolin pour exposer Radicale sur `cal.jefe.ovh`:

```bash
# Sur le jTower, si Pangolin agent déjà installé:
# Ajouter le target via le dashboard Pangolin
# 
# Target: radicale
# URL: http://localhost:5232
# Domaine: cal.jefe.ovh
```

Vérifier: `curl -u jefe https://cal.jefe.ovh`

## Étape 3: Configurer le workflow n8n

Le workflow **📅 Radicale CalDAV Sync** a été créé dans n8n:
→ https://n8n.jefe.ovh/workflow/WgmnvenaW2BYl87W

### 3.1 Créer les credentials dans n8n

1. **Radicale Basic Auth** (httpBasicAuth):
   - User: `jefe`
   - Password: (ton mot de passe Radicale)

2. **Home Assistant Bearer** (httpBearerAuth):
   - Token: (ton token HA long-lived)

### 3.2 Configurer les URLs dans les nodes

Remplacer les placeholders dans ces nodes:

| Node | URL |
|------|-----|
| Get HA Todos | `https://ha.jefe.ovh/api/states` |
| Get Radicale VTODOs | `https://cal.jefe.ovh/jefe/tasks/` |
| PUT VTODO to Radicale | `https://cal.jefe.ovh/jefe/tasks/{{ $json.uid }}.ics` |
| Add Todo to HA | `https://ha.jefe.ovh/api/services/todo/add_item` |
| PUT Event to Radicale | `https://cal.jefe.ovh/jefe/calendar/{{ $json.uid }}.ics` |

### 3.3 Activer le workflow

Cliquer sur **Active** en haut à droite.

## Étape 4: Connecter iOS

### 4.1 Calendrier (Calendar app)

1. iPhone → Réglages → Calendrier → Comptes → Ajouter un compte
2. Choisir **Autre** → **Ajouter un compte CalDAV**
3. Remplir:
   - Serveur: `cal.jefe.ovh`
   - Nom d'utilisateur: `jefe`
   - Mot de passe: (ton password Radicale)
   - Description: `Hermes Calendar`
4. Suivant → sélectionner la collection `calendar`

### 4.2 Tâches (VTODO)

iOS Calendar ne gère pas nativement les VTODOs. Options:

**Option A — App CalDAV Tasks (recommandé):**
- Installer **OpenTasks** (Android) ou **GoodTask** (iOS, payant)
- Ou **CalDAV Synchronizer** 
- Configurer avec les mêmes identifiants CalDAV
- Collection: `tasks`

**Option B — iOS Shortcuts + webhook n8n:**
- Créer un Shortcut qui POST sur `https://n8n.jefe.ovh/webhook/cal-add-event`
- Body: `{"summary": "Ma tâche", "start": "2026-01-01T10:00:00"}`
- Plus simple mais pas de sync bidirectionnelle des tâches

**Option C — GoodTask (iOS, gratuit avec apps Calendar):**
- GoodTask lit les reminders iOS mais peut sync CalDAV
- Configurer un compte CalDAV dans Réglages → GoodTask

## Étape 5: Connecter Home Assistant

### 5.1 Intégration CalDAV (calendrier)

1. HA → Paramètres → Devices & Services → Ajouter une intégration
2. Rechercher **CalDAV**
3. Configurer:
   - URL: `https://cal.jefe.ovh/jefe/calendar/`
   - Username: `jefe`
   - Password: (ton password)
4. Les events du calendrier apparaissent comme `calendar.hermes_calendar`

### 5.2 Todos (déjà géré par n8n)

Les todo entities HA (`todo.liste_dachats`, `todo.rappel`, etc.) sont automatiquement syncées par le workflow n8n toutes les 5 minutes vers Radicale.

### 5.3 Dashboard HA (optionnel)

Ajouter une card calendar dans le dashboard:

```yaml
type: calendar
entities:
  - calendar.hermes_calendar
```

## Étape 6: iOS Shortcut pour ajouter un event

Créer un Shortcut iOS:

1. **Receive any input** (texte ou dictée)
2. **Dictionary** → construire le JSON:
   ```json
   {
     "summary": "Shortcut Input",
     "start": "Date variable",
     "end": "Date variable + 1h",
     "description": ""
   }
   ```
3. **Get contents of URL**:
   - URL: `https://n8n.jefe.ovh/webhook/cal-add-event`
   - Method: POST
   - Headers: `Content-Type: application/json`
   - Body: le dictionary

Dire *"Siri, ajoute un event"* → dicter le titre → ça se retrouve dans Radicale → sync sur iOS Calendar + HA.

## Résumé des flux

| Source → Destination | Mécanisme | Fréquence |
|---------------------|-----------|-----------|
| iOS Calendar → Radicale | CalDAV natif | Temps réel |
| Radicale → iOS Calendar | CalDAV natif | Push |
| Radicale → HA Calendar | Intégration CalDAV HA | Polling HA |
| HA Calendar → Radicale | Intégration CalDAV HA | Polling HA |
| HA Todos → Radicale VTODOs | n8n workflow | 5 min |
| Radicale VTODOs → HA Todos | n8n workflow | 5 min |
| iOS Shortcut → Radicale | Webhook n8n | À la demande |