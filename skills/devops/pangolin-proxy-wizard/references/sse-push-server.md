# SSE Push Server — Full Implementation

Complete Python server that serves a real-time HTML dashboard and pushes updates via Server-Sent Events (SSE). Built for the Hermes Insights dashboard but reusable for any SQLite-backed analytics.

## Design

- Single `asyncio.start_server` on one port handles both HTTP and SSE
- No external dependencies (stdlib only — `asyncio`, `sqlite3`, `json`, `hashlib`)
- SSE (`/api/live`) streams data on change detection — browser uses native `EventSource` API
- `/api/insights` endpoint provides the same data as JSON for fallback polling
- Change detection: hashes `(COUNT(*), SUM(message_count))` every 5 seconds; only pushes on change

## Server Structure

```python
import asyncio, json, sqlite3, datetime, hashlib, os

DB = os.path.expanduser("~/.hermes/state.db")
DAYS = 30
HOST = "127.0.0.1"
PORT = 8999

# ── DB helpers ──────────────────────────────

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def cutoff():
    return (datetime.datetime.now() - datetime.timedelta(days=DAYS)).timestamp()

# ⚠️ started_at is in FLOAT SECONDS, not milliseconds
# Correct: datetime.fromtimestamp(started_at)
# Wrong:   datetime.fromtimestamp(started_at / 1000)

def get_all():
    # Returns a dict with overview, models, platforms, tools, activity, peaks, notable
    c = cutoff()
    conn = db()

    # Overview
    r = conn.execute("SELECT COUNT(*) AS sessions, "
        "COALESCE(SUM(message_count),0) AS messages, "
        "COALESCE(SUM(tool_call_count),0) AS tool_calls, "
        "COALESCE(SUM(input_tokens),0) AS input_tokens, "
        "COALESCE(SUM(output_tokens),0) AS output_tokens, "
        "COALESCE(SUM(input_tokens+output_tokens+cache_read_tokens+cache_write_tokens),0) AS total_tokens, "
        "COALESCE(SUM(ended_at - started_at),0) AS total_secs, "
        "CAST(AVG(message_count) AS INTEGER) AS avg_msgs "
        "FROM sessions WHERE started_at >= ?", (c,)).fetchone()

    total_s = r["total_secs"] or 0
    overview = {"sessions": r["sessions"], "messages": r["messages"],
        "inputTokens": fmt(r["input_tokens"]), "outputTokens": fmt(r["output_tokens"]),
        "totalTokens": fmt(r["total_tokens"]), "activeHours": round(total_s/3600,1),
        "avgSessionHours": round(total_s/3600/max(r["sessions"],1),1),
        "avgMsgsPerSession": r["avg_msgs"]}

    # Models
    rows = conn.execute("SELECT model,COUNT(*)s,"
        "COALESCE(SUM(input_tokens+output_tokens+cache_read_tokens+cache_write_tokens),0)t "
        "FROM sessions WHERE started_at>=? AND model IS NOT NULL "
        "GROUP BY model ORDER BY t DESC", (c,)).fetchall()
    max_t = max((r["t"] for r in rows), default=1)
    models = [{"name":r["model"],"sessions":r["s"],"tokens":r["t"],
               "pct":round(r["t"]/max_t*100,1)} for r in rows]

    # Platforms
    rows = conn.execute("SELECT source,COUNT(*)s,"
        "COALESCE(SUM(message_count),0)m,"
        "COALESCE(SUM(input_tokens+output_tokens+cache_read_tokens+cache_write_tokens),0)t "
        "FROM sessions WHERE started_at>=? GROUP BY source ORDER BY t DESC", (c,)).fetchall()
    colors = {"telegram":"#60a5fa","cron":"#2dd4bf","tui":"#34d399",
              "cli":"#fb923c","discord":"#a78bfa"}
    max_t = max((r["t"] for r in rows), default=1)
    platforms = [{"name":(r["source"] or "unknown").capitalize(),"sessions":r["s"],
        "msgs":r["m"],"tokens":r["t"],"color":colors.get(r["source"] or "","#818cf8"),
        "pct":round(r["t"]/max_t*100,1)} for r in rows]

    # Tools
    rows = conn.execute("SELECT tool_name,COUNT(*)c FROM messages "
        "WHERE session_id IN(SELECT id FROM sessions WHERE started_at>=?)"
        "AND role='tool'AND tool_name IS NOT NULL "
        "GROUP BY tool_name ORDER BY c DESC LIMIT 20", (c,)).fetchall()
    max_c = max((r["c"] for r in rows), default=1)
    tools = [{"name":r["tool_name"],"calls":r["c"],
              "pct":round(r["c"]/max_c*100,1)} for r in rows]

    # Activity by day of week
    rows = conn.execute("SELECT CAST(started_at AS INTEGER)ts "
        "FROM sessions WHERE started_at>=?", (c,)).fetchall()
    days = {0:"Lun",1:"Mar",2:"Mer",3:"Jeu",4:"Ven",5:"Sam",6:"Dim"}
    counts = {d:0 for d in range(7)}
    for r in rows:
        counts[datetime.datetime.fromtimestamp(r["ts"]).weekday()] += 1
    max_c = max(counts.values(), default=1)
    activity = [{"day":days[d],"count":c,"max":max_c} for d,c in counts.items()]

    # Peak hours
    hours = {}
    for r in rows:
        hours[datetime.datetime.fromtimestamp(r["ts"]).hour] = \
            hours.get(datetime.datetime.fromtimestamp(r["ts"]).hour, 0) + 1
    peaks = [{"h":f"{h:02d}:00","c":c}
             for h,c in sorted(hours.items(),key=lambda x:-x[1])[:5]]

    conn.close()

    return {
        "ts": datetime.datetime.now().isoformat(),
        "overview": overview, "models": models, "platforms": platforms,
        "tools": tools, "activity": activity, "peaks": peaks,
        "notable": get_notable()  # see full source for this helper
    }

def fmt(n):
    if n >= 1e6: return str(round(n/1e6,1))+"M"
    if n >= 1e3: return str(round(n/1e3,1))+"k"
    return str(n)
```

## Change Detection

```python
_last_hash = None

def data_changed():
    global _last_hash
    c = cutoff()
    conn = db()
    r = conn.execute("SELECT COUNT(*),COALESCE(SUM(message_count),0) "
                     "FROM sessions WHERE started_at>=?", (c,)).fetchone()
    conn.close()
    h = hashlib.md5(f"{r[0]}-{r[1]}".encode()).hexdigest()[:12]
    if h != _last_hash:
        _last_hash = h
        return True
    return False
```

## Connection Handler (HTTP + SSE on same port)

```python
async def handle(reader, writer):
    try:
        data = await asyncio.wait_for(reader.read(65536), timeout=10)
    except:
        writer.close(); return
    if not data:
        writer.close(); return

    header_end = data.find(b"\r\n\r\n")
    if header_end < 0:
        writer.close(); return
    head = data[:header_end].decode("utf-8", errors="replace")
    lines = head.split("\r\n")
    if not lines or len(lines[0].split()) < 2:
        writer.close(); return
    method, path = lines[0].split()[0], lines[0].split()[1]

    if method == "GET" and path == "/":
        # Serve HTML page
        body = HTML.encode("utf-8")
        writer.write(
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Cache-Control: no-cache\r\n"
            f"Connection: close\r\n\r\n".encode() + body)
        await writer.drain()
        writer.close()

    elif method == "GET" and path == "/api/insights":
        # JSON endpoint (fallback for initial load / debugging)
        data = json.dumps(get_all()).encode()
        writer.write(
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(data)}\r\n"
            f"Access-Control-Allow-Origin: *\r\n"
            f"Cache-Control: no-cache\r\n"
            f"Connection: close\r\n\r\n".encode() + data)
        await writer.drain()
        writer.close()

    elif method == "GET" and path == "/api/live":
        # SSE endpoint — keep connection open
        writer.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/event-stream\r\n"
            b"Cache-Control: no-cache\r\n"
            b"Connection: keep-alive\r\n"
            b"Access-Control-Allow-Origin: *\r\n\r\n")
        await writer.drain()

        # Push initial data
        try:
            writer.write(f"data: {json.dumps(get_all())}\n\n".encode())
            await writer.drain()
        except:
            writer.close(); return

        # Stream changes
        while True:
            try:
                await asyncio.sleep(5)
                if data_changed():
                    writer.write(f"data: {json.dumps(get_all())}\n\n".encode())
                    await writer.drain()
            except:
                break
        writer.close()

    else:
        writer.write(
            b"HTTP/1.1 404 Not Found\r\n"
            b"Content-Length: 0\r\nConnection: close\r\n\r\n")
        await writer.drain()
        writer.close()
```

## Main

```python
async def main():
    srv = await asyncio.start_server(handle, HOST, PORT)
    print(f"Serving on http://{HOST}:{PORT}/")
    async with srv:
        await srv.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
```

## Multi-Page Routing (Dashboard + Sub Pages)

When serving multiple tools under one domain (e.g. `hermes.jefe.al/insights`, `hermes.jefe.al/stats`), use a page registry pattern:

```python
PAGES = {}

def page(name, title, icon, desc, render_fn):
    PAGES[name] = {"title": title, "icon": icon, "desc": desc, "render": render_fn}

# Register pages
page("",         "Hermes Dashboard", "🏠", "Accueil", lambda: PAGE_DASH)
page("insights", "Hermes Insights", "📊", "Statistiques", lambda: PAGE_INSIGHTS)
page("status",   "Hermes Status", "🟢", "état des services", lambda: PAGE_STATUS)
# Add more as needed
```

### Request Routing in `handle()`

```python
path = data[:header_end].split("\\r\\n")[0].split()[1].rstrip("/") or ""
page_key = path.lstrip("/")  # "" → dashboard, "insights" → insights page

if path.startswith("/api/live"):
    # SSE endpoint (stays the same for all pages)
    ...
elif path.startswith("/api/"):
    # JSON API
    ...
elif page_key in PAGES and page_key != "":
    body = PAGES[page_key]["render"]().encode("utf-8")
elif page_key == "":
    body = PAGES[""]["render"]().encode("utf-8")  # dashboard
else:
    body = render_404(page_key).encode("utf-8")
```

### Dashboard Template (Card Layout)

```python
def render_dashboard():
    cards = "".join(f'''
    <a href="/{name}" class="dash-card" style="text-decoration:none">
      <div class="dash-icon">{p["icon"]}</div>
      <div class="dash-info">
        <div class="dash-name">{p["title"]}</div>
        <div class="dash-desc">{p["desc"]}</div>
      </div>
      <div class="dash-arrow">→</div>
    </a>''' for name, p in PAGES.items() if name)

    return f'''<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>🏠 Hermes Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#0a0e17;--surface:#111827;--border:#1e293b;--text:#e2e8f0;--text-dim:#64748b;--accent:#818cf8}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;padding:16px}}
.container{{max-width:800px;margin:0 auto}}
.header{{padding:24px 0;border-bottom:1px solid var(--border);margin-bottom:24px}}
.header h1{{font-size:24px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text}}
.dash-card{{display:flex;align-items:center;gap:14px;background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px;margin-bottom:12px;transition:transform .15s}}
.dash-card:hover{{transform:translateY(-2px);border-color:var(--accent)}}
.dash-icon{{font-size:32px;width:48px;text-align:center}}
.dash-info{{flex:1}}
.dash-name{{font-size:16px;font-weight:600}}
.dash-desc{{font-size:13px;color:var(--text-dim)}}
.dash-arrow{{font-size:20px;color:var(--text-dim);opacity:.5}}
@media(max-width:480px){{.dash-card{{padding:14px}};.dash-icon{{font-size:26px}};.dash-name{{font-size:14px}}}}
</style></head><body>
<div class="container">
<div class="header"><h1>Hermes Dashboard</h1><div style="color:var(--text-dim);font-size:13px">Sélectionne une commande</div></div>
{cards}</div></body></html>'''
```

### Sub-page Template (with Back Button)

Each sub-page should include a "← Dashboard" link and use its own SSE stream:

```html
<a href="/" class="back" style="display:inline-flex;align-items:center;gap:6px;color:var(--text-dim);
  text-decoration:none;font-size:13px;background:var(--surface2);border:1px solid var(--border);
  padding:4px 10px;border-radius:8px;margin-bottom:12px">← Dashboard</a>
```

### 404 Page

```python
def render_404(name):
    return f'''<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><meta name="viewport"
content="width=device-width,initial-scale=1.0"><title>404</title><style>...</style></head><body>
<div class="card"><h1>404</h1><p>La page "<strong>/{name}</strong>" n'existe pas encore</p>
<a href="/">← Retour au dashboard</a></div></body></html>'''
```

### Pangolin Setup

When you switch from dedicated subdomains (e.g. `insights.jefe.al`) to sub-pages (e.g. `hermes.jefe.al/insights`):

1. **Delete** the old site resource (`mcp_pangolin_delete_site_resource_by_siteResourceId`)
2. **Create** a new site resource for the parent domain (`hermes.jefe.al`) on the same site (Hetzner=6 if the server runs on the VPS)
3. The server handles path-based routing internally — Pangolin just sees one backend

### Adding a New Command Page

1. Define `PAGE_NEW = r"""..."""` as a raw string constant (HTML)
2. Register: `page("command-name", "Title", "🔧", "Description", lambda: PAGE_NEW)`
3. Restart the server
4. The dashboard auto-lists it

The SSE endpoint `/api/live` is shared across all pages — each page's `EventSource` connects independently to the same stream.

### Native SPA Proxy on the Same Server

When you need to serve BOTH custom pages AND proxy to a native SPA (Hermes Dashboard port 9119) on the same port, add a catch-all route at the end of `handle()`:

```python
async def handle(reader, writer):
    # ... parse request ...
    path = path.rstrip("/") or ""

    # 1. Custom pages
    if path == "":
        body = render_dashboard().encode("utf-8")
        writer.write(...); await writer.drain(); writer.close(); return
    if path == "insights":
        body = PAGE_INSIGHTS.encode("utf-8")
        writer.write(...); await writer.drain(); writer.close(); return

    # 2. API endpoints
    if path.startswith("/api/stream"):  # SSE
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n...")
        # ... stream loop ...
        return
    if path.startswith("/api/"):  # JSON
        data = json.dumps(get_all()).encode()
        writer.write(...); await writer.drain(); writer.close(); return

    # 3. Everything else → proxy to native SPA
    await proxy_to_native(writer, path)

async def proxy_to_native(writer, path=""):
    native_url = f"http://127.0.0.1:9119{path}"
    try:
        req = urllib.request.Request(native_url, headers={"Host": "127.0.0.1:9119"})
        resp = await asyncio.to_thread(urllib.request.urlopen, req)
        body = resp.read()
        ct = resp.headers.get("Content-Type", "text/html; charset=utf-8")
        writer.write(
            f"HTTP/1.1 {resp.status} OK\r\n".encode()
            + f"Content-Type: {ct}\r\n".encode()
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"Cache-Control: no-cache\r\nConnection: close\r\n\r\n" + body)
        await writer.drain()
    except urllib.error.HTTPError as e:
        body = e.read()
        ct = e.headers.get("Content-Type", "text/html; charset=utf-8")
        writer.write(f"HTTP/1.1 {e.code} Error\r\n".encode()
            + f"Content-Type: {ct}\r\n".encode()
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"Connection: close\r\n\r\n" + body)
        await writer.drain()
    except Exception:
        body = FALLBACK_HTML.encode()
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"Connection: close\r\n\r\n" + body)
        await writer.drain()
    writer.close()
```

This handles `/dashboard`, `/assets/*`, `/favicon.ico`, and any other SPA path by forwarding to the native dashboard server. The native dashboard (port 9119) remains accessible only through the proxy — never directly exposed.

**Key detail**: The `asyncio.to_thread()` wrapper is essential because `urllib.request.urlopen()` is blocking. Without it, every proxy call stalls the asyncio event loop, freezing all SSE connections.

## HTML Side (Browser)

```javascript
// SSE — auto-reconnects on disconnect (built into EventSource)
const evt = new EventSource('/api/live');
evt.onmessage = function(e) {
  try { render(JSON.parse(e.data)); } catch(err) {}
};
evt.onerror = function() {
  document.getElementById('status').textContent = '⏳ Reconnexion...';
  // Browser will auto-reconnect — no manual code needed
};

// Optional: initial load via HTTP as fallback
fetch('/api/insights').then(r => r.json()).then(render);
```

## Pangolin Deployment

```bash
# 1. Create directory
mkdir -p /var/www/insights
cp server.py /var/www/insights/

# 2. Run server (loopback-only, secure behind Pangolin)
cd /var/www/insights && python3 server.py &
# Keep process: nohup, tmux, or supervisor

# 3. Create Pangolin site resource
# MCP: mcp_pangolin_create_org_by_orgId_site_resource
#   - orgId: "jorganisation"
#   - name: "Service Name"
#   - mode: "http"
#   - destination: "127.0.0.1"
#   - destinationPort: 8999
#   - subdomain: "your-subdomain"
#   - domainId: "ykx3vzina5zahuf" (jefe.al)
#   - scheme: "http"
#   - ssl: true
#   - siteId: 28 (Hermes VPN)
#   - userIds: ["<admin-user-id>"]
#   - roleIds: [1]
#   - clientIds: []

# 4. Verify
curl -sI https://your-subdomain.jefe.al
# Should return 200
```

## Pitfalls

- **NEVER serve from /root/ or $HOME** — creates a directory listing of all Hermes config files
  - Always use `/var/www/<service>/` or `/srv/www/<service>/`
- **Pangolin `mode: "http"` CANNOT pass WebSocket** — SSE is the only real-time option through Pangolin proxy
- **Keep process alive** — `python3 -m http.server` exits when the terminal session ends; use `nohup`, `tmux`, `screen`, or a supervisor
- **`started_at` is in float seconds**, not milliseconds — all timestamp math must use seconds
