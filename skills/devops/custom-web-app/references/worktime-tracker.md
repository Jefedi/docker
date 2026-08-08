# WorkTime Tracker — Reference Implementation

Built on 2026-07-28. Located at `/opt/data/worktime-tracker/`.

## Use Case

User wanted a daily work time tracker with:
- Two day types: **À la boîte** (office) or **Déplacement** (field/remote)
- Office: work hours + ticket resto checkbox
- Déplacement: work hours + travel hours + detour hours + location + meal allowances (paniers)
- Stats: weekly, monthly, all-time totals + 30-day bar chart
- JSON API endpoint for future n8n integration

## Data Model

```sql
CREATE TABLE entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    jour_type TEXT NOT NULL DEFAULT 'boite',  -- 'boite' or 'deplacement'
    heure_debut TEXT,                          -- 'HH:MM'
    heure_fin TEXT,                            -- 'HH:MM'
    heures_travaillees REAL DEFAULT 0,         -- auto-calculated from debut/fin
    heures_route REAL DEFAULT 0,               -- travel hours (deplacement only)
    lieu_deplacement TEXT,                     -- location name
    nb_paniers INTEGER DEFAULT 0,              -- meal allowances count
    ticket_resto INTEGER DEFAULT 0,            -- boolean (boite only)
    detour_heures REAL DEFAULT 0,              -- extra travel hours (detour)
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);
```

## Key Implementation Details

### Dynamic form show/hide
JavaScript toggles form sections based on day type:
```javascript
function selectType(type) {
    document.getElementById('jour_type').value = type;
    document.getElementById('btn-boite').classList.toggle('active', type === 'boite');
    document.getElementById('btn-deplacement').classList.toggle('active', type === 'deplacement');
    document.getElementById('boite-fields').classList.toggle('hide', type !== 'boite');
    document.getElementById('deplacement-fields').classList.toggle('show', type === 'deplacement');
}
```

### Auto-calculated work hours
Hours computed from start/end times, handles midnight crossing:
```python
def calc_hours(h_debut, h_fin):
    if not h_debut or not h_fin:
        return 0.0
    d = datetime.strptime(h_debut, "%H:%M")
    f = datetime.strptime(h_fin, "%H:%M")
    delta = (f - d).total_seconds() / 3600
    if delta < 0:  # crossed midnight
        delta += 24
    return round(delta, 2)
```

### Week range (Monday-Sunday)
```python
def get_week_range(ref_date=None):
    if ref_date is None:
        ref_date = date.today()
    monday = ref_date - timedelta(days=ref_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()
```

### French day name Jinja filter
```python
DAYS_FR = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

@app.template_filter("day_name")
def day_name_filter(date_str):
    from datetime import date as _date
    d = _date.fromisoformat(date_str.split(" ")[0])
    return DAYS_FR[d.weekday()]
```

## Stats Queries

Weekly/monthly/all-time aggregates use SUM with CASE for type-specific counts:
```sql
SELECT 
    COUNT(*) as jours,
    SUM(heures_travaillees) as total_heures,
    SUM(heures_route) as total_route,
    SUM(detour_heures) as total_detour,
    SUM(nb_paniers) as total_paniers,
    SUM(ticket_resto) as total_tickets,
    SUM(CASE WHEN jour_type='deplacement' THEN 1 ELSE 0 END) as nb_deplacements
FROM entries WHERE date >= ? AND date <= ?
```

## Docker Config

- Port: 9847
- `docker-compose.yml`: binds `127.0.0.1:9847:9847`, mounts `./data:/data`, sets `DB_PATH=/data/worktime.db`
- `Dockerfile`: `python:3.12-slim`, gunicorn with 2 workers

## Testing Approach

1. Start Flask dev server locally: `.venv/bin/python app.py`
2. POST test data via curl (both day types)
3. Verify DB content via curl GET on pages
4. Check `/api/stats` JSON output
5. Verify all form fields present in HTML
6. Kill server, clean test DB

## Future Extensions

- Export CSV for accounting/payroll
- n8n integration via `/api/stats` endpoint
- Pangolin proxy for mobile access
- Custom rates per panier/ticket for monetary totals