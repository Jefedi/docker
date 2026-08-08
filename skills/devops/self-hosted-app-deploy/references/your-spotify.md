# YourSpotify Deployment (linuxserver image)

## Spotify Developer App Setup

1. Go to https://developer.spotify.com/dashboard → Create app
2. App name, description (real text, not gibberish — browser spellcheck red underline = validation error)
3. Website: `https://sp.jefe.al`
4. Redirect URI: `https://sp.jefe.al/api/oauth/spotify/callback`
   - ⚠️ linuxserver uses `/api/` prefix — upstream image uses `/oauth/spotify/callback` (no `/api/`)
5. Check Web Playback SDK
6. Accept ToS, Save
7. In Settings, copy Client ID → `SPOTIFY_PUBLIC`, Client Secret → `SPOTIFY_SECRET`

## docker-compose.yml

```yaml
services:
  your-spotify:
    image: linuxserver/your_spotify:latest
    restart: unless-stopped
    ports:
      - "8544:80/tcp"
    volumes:
      - /srv/lsio/your_spotify/config:/config
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Paris
      - APP_URL=https://sp.jefe.al
      - SPOTIFY_PUBLIC=<client_id>
      - SPOTIFY_SECRET=<client_secret>
      - SPOTIFY_API_DELAY_MS=2000
      - CORS=https://sp.jefe.al
      - MONGO_ENDPOINT=mongodb://mongo:27017/your_spotify

  mongo:
    image: mongo:8
    restart: unless-stopped
    volumes:
      - /srv/lsio/your_spotify/db:/data/db

networks:
  default:
    driver: bridge
    ipam:
      config:
        - subnet: 172.40.0.0/16
```

## Pangolin Config

Point `sp.jefe.al` → `http://<jTower_ip>:8544` (HTTP port, not 443).

## Key Differences: linuxserver vs upstream

| Feature | linuxserver | upstream (yooooomi) |
|---|---|---|
| Image | `linuxserver/your_spotify` | `yooooomi/your_spotify_server` + `yooooomi/your_spotify_client` |
| Redirect URI | `/api/oauth/spotify/callback` | `/oauth/spotify/callback` |
| Env: frontend URL | `APP_URL` (auto-derives API + client endpoints) | `API_ENDPOINT` + `CLIENT_ENDPOINT` (separate) |
| Containers | 1 (all-in-one with nginx) | 2 (server + web) + mongo |
| Ports | 80 (http) / 443 (https) | 8080 (server) / 3000 (web) |

## Common Issues

### 502 Bad Gateway after deploy
- Check logs: if "Failed to connect to database" → MongoDB service missing from compose
- Add `mongo` service (see compose above), redeploy

### Docker network pool exhaustion
Error: `all predefined address pools have been fully subnetted`
- Fix per-stack: add explicit `networks.default.ipam.config.subnet` with an unused /16
- Fix global: edit `/etc/docker/daemon.json` with `default-address-pools` (multiple /16s with size: 24), restart docker
- Clean up: `docker network prune`

### Subnet overlap
Error: `Pool overlaps with other one on this address space`
- The subnet in the compose is already used by another Docker network
- Change to a different /16 (e.g. 172.40 → 172.41 → 172.42)
- Check used subnets: `docker network inspect $(docker network ls -q) --format '{{.Name}} {{.IPAM.Config}}'`

### Spotify app description validation error
- The description field must contain real text. Random characters trigger browser spellcheck AND Spotify validation
- Use something like: `Self-hosted Spotify listening statistics dashboard`

### No history data on first launch
- Normal: YourSpotify only pulls last 24h initially
- For full history: request Extended Streaming Data from https://www.spotify.com/account/privacy/ (takes up to 30 days)
- Import via YourSpotify Settings → Extended streaming history → upload `Streaming_History_Audio_*.json` files

## User Management

After app creation, Spotify requires you to register users who can access the app:
- Spotify Dashboard → your app → User Management → add name + email (Spotify account email)
- The account that created the app doesn't need registration
- Alternatively: Request extension to avoid manual user registration