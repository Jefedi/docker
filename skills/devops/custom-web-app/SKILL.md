---
name: custom-web-app
title: Custom Web App Builder
description: Build Flask+SQLite web apps when no off-the-shelf tool fits.
tags: [flask, sqlite, docker, self-hosted, web-app, homelab]
---

# Custom Web App Builder

Build small, self-hosted web apps from scratch when no existing tool fits the user's needs. Typical use cases: time trackers, custom forms, dashboards, data entry tools.

## Architecture Pattern

- **Backend**: Flask (Python) — lightweight, no framework overhead
- **Database**: SQLite — single file, no external DB service needed
- **Frontend**: Server-rendered Jinja2 templates with inline CSS/JS — no build step, no npm
- **Container**: Python slim image + gunicorn, docker-compose for deployment
- **Network**: Bind `127.0.0.1:<port>` only — never expose directly. External access via Pangolin reverse proxy.

## Workflow

### 1. Clarify requirements
Use `clarify` to nail down:
- What fields/data the user wants to track
- Whether fields are conditional (e.g. different form sections based on a type selector)
- What stats/summaries they want
- Any future integration needs (n8n, API access)

### 2. Create project structure
```
app-name/
├── app.py              # Flask app + routes + DB init
├── requirements.txt    # flask, gunicorn
├── Dockerfile          # python:3.x-slim + gunicorn
├── docker-compose.yml  # bind 127.0.0.1, volume for data
├── data/               # SQLite DB lives here (gitignored)
└── templates/
    ├── index.html      # Main form/saisie
    ├── history.html    # List view
    └── stats.html      # Dashboard/stats
```

### 3. Implement the app

**DB path pattern** (critical — see Pitfalls):
```python
import os
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "app.db"))
```
This makes it work both locally (without Docker) and in Docker (with `DB_PATH=/data/app.db` env var).

**Route pattern**: One route per page + POST route for save + DELETE route. Keep it RESTful-ish.

**Dynamic forms**: Use JavaScript to show/hide form sections based on a type selector. See `references/dynamic-form-pattern.md`.

**Stats endpoint**: Always include a `/api/stats` JSON endpoint for future n8n/integration use, even if the user doesn't ask for it yet.

### 4. Test locally before Docker
```bash
cd /path/to/app
python3 -m venv .venv
.venv/bin/pip install flask gunicorn
.venv/bin/python app.py
# Test with curl: POST to save, GET to verify, check /api/stats
```

### 5. Deploy via Docker
```bash
docker compose -f /path/to/docker-compose.yml up -d --build
```
Verify: `curl -s http://127.0.0.1:<port>/` returns HTML.

### 6. Pangolin proxy (if external access needed)
Create Pangolin resource pointing to `http://127.0.0.1:<port>`. Follow `new-service-onboarding` skill for Pangolin setup.

## UI Design Conventions

The user's homelab uses a consistent dark theme. Match it:
- Background: `#0f1117`, Cards: `#1a1d27`
- Accent blue: `#4f9eff`, Accent orange: `#f97316`
- Green: `#22c55e`, Red: `#ef4444`
- Font: system stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`)
- Mobile-first: `max-width: 600px` container, `viewport` meta tag
- Sticky bottom nav with 3 tabs (Saisie / Historique / Stats)
- Touch-friendly: large buttons (40px+), 16px input font size (prevents iOS zoom)

## Pitfalls

- **DB path `/data/` doesn't exist outside Docker**: If you hardcode `/data/app.db`, the app crashes with `sqlite3.OperationalError: unable to open database file` when running locally. Always use the relative path pattern with env var override (see step 3).
- **Terminal background-process guard**: `pip install`, `python3 -m venv`, and `docker compose up -d --build` may be blocked in foreground mode. Use `background=true` + `notify_on_complete=true` for installs/builds, then `process(action='wait')` to get the result.
- **No Docker socket on this host**: The agent runs without direct Docker socket access. Docker commands may fail with exit code 125. The user deploys via Portainer or runs docker commands themselves on AX42.
- **gunicorn in Docker**: Use `CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:<port>", "--timeout", "30", "app:app"]` — don't use Flask's dev server in production.
- **Port binding**: Always `127.0.0.1:<port>:<port>` in docker-compose, never `0.0.0.0` or bare `<port>`.
- **Jinja custom filters**: If you need custom filters (e.g. `day_name` for French day names), register them with `@app.template_filter('name')` before any template renders.

## Reference Implementations

- **WorkTime Tracker** (`references/worktime-tracker.md`): Time tracking app with conditional forms (boîte vs déplacement), stats dashboard, 30-day bar chart, JSON API.

## Templates

- **Flask app boilerplate** (`templates/flask-app-boilerplate.py`): Minimal Flask + SQLite app with CRUD, Docker-ready. Copy and adapt for new apps.