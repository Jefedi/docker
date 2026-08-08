# Web App Pattern: SPA Served from n8n Webhook

Serve a complete single-page application from an n8n webhook, using Data Tables
for storage and multiple webhook routes for CRUD operations. No external app
server needed — everything runs in n8n.

## When to Use

- User wants a self-contained web tool (tracker, dashboard, form) without
  deploying a separate Flask/Node app
- Data should persist in n8n Data Tables
- User wants to access it from mobile/desktop without agent intervention

## Architecture

```
GET  /webhook/<app>        → Fetch all rows → Build HTML page → Respond HTML
POST /webhook/<app>/save   → Upsert row → Respond JSON
POST /webhook/<app>/delete → Delete row → Respond JSON
GET  /webhook/<app>/stats  → Fetch all → Compute stats → Respond JSON
```

One workflow, 4 webhook triggers, 4 independent chains. Each chain starts
from its own webhook trigger and ends with a `respondToWebhook` node.

## HTML Embedding (REQUIRED for pages > 50 lines)

**Do NOT inline large HTML in `jsCode` as template literals or string arrays.**
Use the file-based pattern:

1. Write the full HTML (with CSS, JS) to a separate file
2. In Python/SDK code: read the file, `JSON.stringify()` it to create a safe
   JS string literal
3. In the Code node's `jsCode`, reference the stringified HTML:
   ```javascript
   var html = "<...escaped HTML...>".replace("__DATA_PLACEHOLDER__", encoded);
   return [{json: {html: html}}];
   ```

### Data Injection

- Put `<script id="__data" type="application/json">__DATA_PLACEHOLDER__</script>`
  in the HTML
- At runtime, the Code node replaces `__DATA_PLACEHOLDER__` with base64-encoded
  JSON containing all Data Table rows + pre-computed stats
- Client-side: `JSON.parse(atob(document.getElementById('__data').textContent))`

### Why base64?

Avoids all HTML/JSON escaping issues. The HTML page is a static string with a
single token replacement — no template literals, no concatenation of user data
into HTML.

## Code Node: Build Page Pattern

```javascript
var rawEntries = $input.all().map(function(i){return i.json;});
var entries = rawEntries.filter(function(e){return e.date;}); // filter empty

// Compute stats server-side
var today = new Date();
// ... date range calculations ...
var stats = { week: calcStats(weekEntries), month: calcStats(monthEntries), total: calcStats(entries) };

var data = { entries: entries, stats: stats };
var encoded = Buffer.from(JSON.stringify(data)).toString("base64");
var html = "<!DOCTYPE html>...".replace("__DATA_PLACEHOLDER__", encoded);
return [{json: {html: html}}];
```

## Respond to Webhook Configuration

### HTML page response:
```javascript
respondWith: 'text',
responseBody: expr('{{ $json.html }}'),
options: {
  responseHeaders: {
    entries: [{ name: 'Content-Type', value: 'text/html; charset=utf-8' }]
  }
}
```

### JSON API response (save/delete/stats):
```javascript
// For computed JSON (stats):
respondWith: 'text',
responseBody: '={{ JSON.stringify($json) }}',
options: {
  responseHeaders: {
    entries: [{ name: 'Content-Type', value: 'application/json' }]
  }
}

// For simple success:
respondWith: 'text',
responseBody: '={{ JSON.stringify({ success: true }) }}',
options: {}
```

⚠️ **Do NOT use `respondWith: 'json'`** — it returns `{"myField":"value"}`
(placeholder). See `references/sdk-pitfalls.md` Pitfall 9.

## Client-Side JavaScript

The HTML page uses vanilla JS (no framework needed for small apps). Key patterns:

- `fetch('/webhook/<app>/save', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)})`
- After save, update the local `entries` array in-place (find by date, replace or push)
- History view: render entries sorted by date descending
- Stats view: use pre-computed stats from `__data` (no need to call the stats API)

## Data Table Schema

Create the Data Table first via `create_data_table` with all columns matching
the form fields. Use appropriate types (`string`, `number`, `boolean`, `date`).

## Validation Warnings (Expected)

When the upsert node maps `$json.body.*` fields from a webhook trigger, the
validator emits `INVALID_EXPRESSION_PATH` warnings. These are **harmless** —
the fields exist at runtime in the webhook body. See `references/sdk-pitfalls.md`
Pitfall 10.

## Testing

```bash
# Page HTML
curl -s http://localhost:5678/webhook/<app> | head -c 200

# Save
curl -s -X POST http://localhost:5678/webhook/<app>/save \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-07-28","jour_type":"deplacement",...}'

# Verify data injected in page
curl -s http://localhost:5678/webhook/<app> | python3 -c "
import sys, re, base64, json
html = sys.stdin.read()
m = re.search(r'id=\"__data\"[^>]*>([^<]+)', html)
if m:
    data = json.loads(base64.b64decode(m.group(1)))
    print('Entries:', len(data['entries']))
"

# Stats API
curl -s http://localhost:5678/webhook/<app>/stats
```

## Iterative Updates: Modifying the HTML After Deployment

When the user asks for changes to a deployed web app (new field, UI tweak,
date format change), you don't need to recreate the workflow. Instead:

1. **Fetch the current HTML** from the production webhook:
   ```bash
   curl -s http://localhost:5678/webhook/<app> > /opt/data/current.html
   ```

2. **⚠️ CRITICAL: Restore `__DATA_PLACEHOLDER__`** — the live page has the
   placeholder already replaced with actual base64 data. You MUST restore it
   before re-embedding, or the Code node will inject hardcoded stale data
   instead of fresh data on each page load:
   ```python
   import re
   html = re.sub(
       r'(type=\\"application/json\\">)[^<]+(</script>)',
       r'\1__DATA_PLACEHOLDER__\2',
       html
   )
   assert '__DATA_PLACEHOLDER__' in html, "Placeholder not restored!"
   ```

3. **Modify it** with Python (string replacements for targeted changes):
   ```python
   html = html.replace('old_text', 'new_text')
   ```

4. **Regenerate the jsCode**: `json.dumps(html)` produces a safe JS string
   literal. Prepend the stats/injection boilerplate, append the
   `__DATA_PLACEHOLDER__` replacement and return statement.

5. **Push via `updateNodeParameters`** (without `replace: true` — just
   updating `jsCode` and `mode` is enough for a Code node):
   ```
   update_workflow({
     operations: [{
       type: 'updateNodeParameters',
       nodeName: 'Build Page',
       replace: false,
       parameters: { mode: 'runOnceForAllItems', jsCode: newJsCode }
     }]
   })
   ```

6. **Publish and test.**

### Schema Evolution: Adding Columns After Creation

When the user needs a new field (e.g., `jour_ferie` checkbox):

1. **Add column to Data Table** via `add_data_table_column`:
   ```
   add_data_table_column({
     dataTableId: '...', projectId: '...',
     name: 'jour_ferie', type: 'boolean'
   })
   ```

2. **Update the upsert node** to include the new column in both `value`
   (with `={{ $json.body.new_field }}` expression) and `schema` array.

3. **Update the HTML** (iterative pattern above) to add the form field,
   loadDate/saveEntry/renderHistory/renderStats JS changes.

4. **Update the stats Code node** (both "Build Page" and "Compute Stats"
   if separate) to include the new field in `calcStats()`.

5. **Publish and test.**

## Example: WorkTime Tracker

Built 2026-07-28. Workflow ID: `SJK4U7fWFyufakNF`.

- Data Table: `worktime_entries` (12 columns: date, jour_type, heure_debut,
  heure_fin, heures_travaillees, heures_route, lieu_deplacement, nb_paniers,
  ticket_resto, detour_heures, notes, jour_ferie)
- 4 webhook routes: page HTML, save (upsert by date), delete (deleteRows by
  date), stats (computed JSON)
- Dark theme mobile-friendly SPA with 4 views: Saisie, Historique, Stats, Paye
- Dynamic form: shows different fields based on "À la boîte" vs "Déplacement"
- Stats computed server-side in Code node (week/month/total)
- Time inputs for route (HH:MM format, default 02:30), converted to decimal
  for storage via `timeToDecimal()` client-side
- `jour_ferie` checkbox added in a second iteration via schema evolution
- Dates displayed in JJ/MM/AAAA format (French) via `fmtDate()` helper
- **Paye view**: auto-calculates payroll by week from existing entries
  (heures normales ≤35h × 12.80€, heures supp >35h × 16.00€, prime 13e mois
  × 1.07€, heures de route × 16.00€, paniers × 8.00€). No new data entry —
  pure computation view grouping entries by ISO week (Monday-based).
- **Auto-fériés**: `jour_ferie` checkbox only appears on French public holidays,
  auto-checked. Uses client-side `getFeries(year)` computing 8 fixed dates
  (01-01, 05-01, 05-08, 07-14, 08-15, 11-01, 11-11, 12-25) + 3 variable
  dates from Easter algorithm (Pâques, Ascension +40d, Pentecôte +50d).
  No API call needed — pure JS calculation.

### French Public Holidays (pure JS, no API)

For apps that need to know French public holidays (e.g., auto-checking a
"jour férié" checkbox), compute them client-side with the Anonymous
Gregorian algorithm for Easter:

```javascript
function getFeries(year){
  var feries={};
  // 8 fixed dates
  var fixe=['01-01','05-01','05-08','07-14','08-15','11-01','11-11','12-25'];
  fixe.forEach(function(d){feries[year+'-'+d]=true;});
  // Easter (Anonymous Gregorian algorithm)
  var a=year%19,b=Math.floor(year/100),c=year%100;
  var d=Math.floor(b/4),e=b%4,f=Math.floor((b+8)/25),g=Math.floor((b-f+1)/3);
  var h=(19*a+b-d-g+15)%30,i=Math.floor(c/4),k=c%4;
  var l=(32+2*e+2*i-h-k)%7;
  var m=Math.floor((a+11*h+22*l)/451);
  var month=Math.floor((h+l-7*m+114)/31);
  var day=((h+l-7*m+114)%31)+1;
  var paques=new Date(year,month-1,day);
  // Ascension = Easter + 40 days (Thursday)
  var ascension=new Date(paques);ascension.setDate(paques.getDate()+40);
  feries[ferieKey(ascension)]=true;
  // Pentecost = Easter + 50 days (Monday)
  var pentecote=new Date(paques);pentecote.setDate(paques.getDate()+50);
  feries[ferieKey(pentecote)]=true;
  return feries;
}
function ferieKey(d){
  var m=(d.getMonth()+1<10?'0':'')+(d.getMonth()+1);
  var day=(d.getDate()<10?'0':'')+d.getDate();
  return d.getFullYear()+'-'+m+'-'+day;
}
function isFerie(dateStr){
  var d=new Date(dateStr);
  return getFeries(d.getFullYear())[ferieKey(d)]||false;
}
```

No external API call needed — works for any year. 11 holidays total
(8 fixed + Pâques Monday + Ascension Thursday + Pentecost Monday).

### Iteration history (4 iterations in one session)

1. **Initial creation**: Flask app → user corrected "tout sur n8n" → rebuilt
   as n8n workflow with Data Table + 4 webhooks
2. **Date format + route input**: dates → JJ/MM/AAAA, route input → HH:MM
   with default 02:30, `timeToDecimal()`/`decimalToTime()`/`fmtHours()` helpers
3. **Jour férié**: added `jour_ferie` boolean column + checkbox + stats counter
4. **Paye view + auto-fériés**: added payroll computation view (4th nav tab),
   made ferie checkbox conditional on actual French public holidays

Each iteration followed the fetch → restore placeholder → modify → push
jsCode → publish cycle. Total HTML grew from ~17KB to ~29KB across iterations.

## User Preference: "Tout sur n8n"

When the user asks for a web tool, tracker, or dashboard, they want it
**entirely on n8n** — no Flask app, no separate Docker container, no external
database. Build it as an n8n workflow with webhooks + Data Tables. This was
explicitly stated on 2026-07-28 after I built a Flask app first and the user
corrected me: "Tout doit se passer sur n8n."