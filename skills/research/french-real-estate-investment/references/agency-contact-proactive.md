# Proactive Agency Contact — Le Havre

Contacting real estate agencies directly by email with your search criteria.
Complements passive listing monitoring (rental-monitoring-le-havre.md).

## When to Use

- User wants to send a search criteria email to all agencies in a city
- User asks for "le mail de toutes les agences"
- User wants clickable mailto: links that open their mail client pre-filled

## Agency Email Harvesting Techniques

### Step 1: Find agencies via Google Maps

```
browser_navigate(url="https://www.google.com/maps/search/agences+immobilieres+Le+Havre")
```

- Accept cookie consent (click "Reject all" / "Hylkää kaikki")
- Snapshot lists ~9-10 agencies with name, address, phone, website URL
- Scroll for more results

### Step 2: Extract emails from agency websites

#### Method A: curl + grep for mailto: (works for non-protected sites)

```bash
curl -sL --max-time 15 \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0" \
  "https://www.agency-site.com/" | grep -ioE 'mailto:[^"]+' | head -5
```

#### Method B: curl + grep for raw email addresses

```bash
curl -sL --max-time 15 \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0" \
  "https://www.agency-site.com/contact" | \
  grep -ioE '[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]{2,}' | \
  grep -v '@[0-9]\|sentry\|google\|cloudflare\|facebook' | sort -u
```

#### Method C: Cloudflare email obfuscation decoding

Some sites (e.g. Orpi) obfuscate emails with Cloudflare's `data-cfemail` attribute:

```bash
# Find the obfuscated hex string
curl -sL "https://www.orpi.com/seineimmobilier/" | grep -oP 'data-cfemail="[^"]*"'
# Output: data-cfemail="1f6c7a76717a767272707d7673767a6d5f706d6f76317c7072"
```

```python
# Decode it
cf = "1f6c7a76717a767272707d7673767a6d5f706d6f76317c7072"
key = int(cf[:2], 16)
email = ""
for i in range(2, len(cf), 2):
    email += chr(int(cf[i:i+2], 16) ^ key)
print(email)  # seineimmobilier@orpi.com
```

#### Method D: Contact page URL patterns

Try these URL patterns when the homepage doesn't expose an email:
- `/contact`
- `/nous-contacter`
- `/fr/contact`
- `/contact,110` (Netty.immo platform — used by Cabinet Dero Renard)
- `/contact.html`

#### Sites that only have forms (no public email via curl)

These sites are Cloudflare-protected or use JS-rendered contact forms. However,
their emails CAN be found via Brave Search (see method above):

- ~~**Stéphane Plaza Immobilier** — Cloudflare protected, no email public.~~ → Found via Brave: `lehavre@stephaneplazaimmobilier.com`
- ~~**Laforêt** — No agency-specific email exposed.~~ → Found via Brave: `lehavrecentre@laforet.com`
- ~~**Foncia** — No direct email found.~~ → Found via Brave: `ft-normandielehavre@foncia.fr`
- ~~**Century 21** — No direct email found for Le Havre agency.~~ → Found via Brave: `lehavreaccore@century21.fr`
- **Guy Hoquet** — No agency found for Le Havre.

**Lesson**: Always try Brave Search before declaring an agency email as "not found".
Cloudflare-protected websites won't expose emails via curl, but the emails exist
and are indexed by Brave.

## Verified Agency Email Directory — Le Havre (August 2026)

| Agency | Email | Address | Phone |
|--------|-------|---------|-------|
| Cabinet MARIE | contact@cabinetmarie.com | 23 Pl. de l'Hôtel de Ville | 02 35 41 78 93 |
| LHL Associés | contact@lhl-associes.fr | 13 Rue Auguste Constant Guerrier | 02 79 49 15 69 |
| Cabinet Dero Renard | contact@derorenard.fr | 76 Bd Albert 1er | 02 35 48 59 19 |
| Agence du Palais (Orpi) | agencedupalais@orpi.com | 15 Pl. de l'Hôtel de Ville | 02 35 42 23 64 |
| Orpi Seine Immobilier | seineimmobilier@orpi.com | 57 Rue Paul Doumer | 02 35 22 26 66 |
| Lemaistre Immobilier | contact@lemaistre-immo.com | 91 Av. Foch | 02 35 22 44 44 |
| Citya La Salamandre | imorvanclipet@citya.com | 142 Bd de Strasbourg | 02 35 22 02 02 |
| Stéphane Plaza Immobilier | lehavre@stephaneplazaimmobilier.com | 94 Rue Voltaire | 02 32 85 01 71 |
| Laforêt Le Havre | lehavrecentre@laforet.com | 100 Rue Bernardin de Saint-Pierre | 02 35 30 40 50 |
| Century 21 Le Havre | lehavreaccore@century21.fr | Le Havre | — |
| Foncia Le Havre | ft-normandielehavre@foncia.fr | Le Havre | — |
| Square Habitat Le Havre | lehavre@squarehabitat.fr | Le Havre | — |
| Poulet Immobilier | contact@pouletimmobilier.fr | Le Havre 76600 | — |

⚠️ Emails should be re-verified before each use — agencies change emails or rebrand.

### Finding emails for network agencies (Stéphane Plaza, Laforêt, Century 21, etc.)

Network agencies don't expose emails on their websites (Cloudflare protection,
contact forms only). Use **Brave Search** to find the email pattern:

```bash
curl -sL --max-time 15 -H "User-Agent: Mozilla/5.0" \
  "https://search.brave.com/search?q=stephane+plaza+immobilier+le+havre+email" | \
  grep -oP '[a-z0-9._-]+@[a-z0-9._-]+\.[a-z]{2,}' | \
  grep -v 'brave\|google\|sentry\|@[0-9]*x[0-9]*' | sort -u
```

Common patterns discovered:
- Stéphane Plaza: `lehavre@stephaneplazaimmobilier.com`
- Laforêt: `lehavrecentre@laforet.com` (format: `<city><suffix>@laforet.com`)
- Century 21: `lehavreaccore@century21.fr` (format: `<city><agencyname>@century21.fr`)
- Foncia: `ft-normandielehavre@foncia.fr` (format: `ft-<region><city>@foncia.fr`)
- Square Habitat: `lehavre@squarehabitat.fr`

Brave Search is the most reliable search engine for email harvesting — DDG and Bing
frequently return empty results for email queries, while Brave exposes emails in
result snippets. Filter out image URL false positives with `grep -v '@[0-9]*x[0-9]*'`.

## mailto: Link Construction

Build clickable links that open the user's mail client with pre-filled subject + body.

### Python script to generate links

```python
import urllib.parse

subject = "Recherche appartement en location — Le Havre (T2, 35m² min, 500€ CC max)"

body = """Bonjour,

Je suis actuellement à la recherche d'un appartement en location au Havre...

[Critères détaillés ici]
"""

encoded_subject = urllib.parse.quote(subject)
encoded_body = urllib.parse.quote(body)

agencies = [
    ("Cabinet MARIE", "contact@cabinetmarie.com"),
    ("LHL Associés", "contact@lhl-associes.fr"),
    # ... etc
]

for name, email in agencies:
    link = f"mailto:{email}?subject={encoded_subject}&body={encoded_body}"
    print(f"[Envoyer le mail à {name}]({link})")
```

### Format for Telegram delivery — ⚠️ mailto: links DON'T work in Telegram

Telegram does NOT render `mailto:` links as clickable. Sending markdown links
like `[Envoyer le mail](mailto:...)` in a Telegram message produces plain text
that the user cannot tap.

**Workaround**: Generate an HTML file with clickable mailto: buttons and send
it as a file attachment. The user opens it in their mobile browser (Safari on
iOS) and taps each button — this opens iCloud Mail pre-filled.

```python
# Generate HTML file with mailto: buttons
html = """<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: -apple-system, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
.agence { background: #fff; border-radius: 12px; padding: 16px; margin: 12px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.btn { display: inline-block; background: #1a73e8; color: #fff !important; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; }
</style></head><body>
<h1>📨 Recherche appartement Le Havre</h1>
"""
for name, email, addr in agencies:
    link = f"mailto:{email}?subject={encoded_subject}&body={encoded_body}"
    html += f'<div class="agence"><h2>{name}</h2><p>{addr}</p>'
    html += f'<a class="btn" href="{link}">📧 Envoyer le mail</a></div>\n'
html += "</body></html>"

# Write and send as file
write_file(path="/opt/data/cache/recherche-appart-lehavre.html", content=html)
# Then include MEDIA:/opt/data/cache/recherche-appart-lehavre.html in response
```

The user opens the file on their iPhone → each button opens iCloud Mail
with everything pre-filled → they replace `[Ton prénom / nom]` and
`[Ton numéro de téléphone]` → hit send.

### Body template for rental search

Key sections to include:
1. **Surface et configuration** — minimum m², type (T2), chambre séparée, cuisine séparée (idéalement)
2. **Budget** — loyer maximum charges comprises
3. **Quartiers recherchés** — liste avec "non obligatoire" for optional ones
4. **Stationnement** — préciser "critère souhaitable, non obligatoire" + dimensions garage si pertinent
5. **Disponibilité** — "disponible pour des visites rapidement"
6. **Signature** — placeholders pour nom et téléphone

## Pitfalls

- **Cloudflare-protected sites** (Stéphane Plaza) block curl completely. But their emails are findable via Brave Search — don't give up just because curl can't scrape the site.
- **Telegram does NOT support mailto: links.** Sending `[Envoyer le mail](mailto:...)` in Telegram produces unclickable plain text. Generate an HTML file with clickable buttons and send it as a file attachment instead (see Format section above).
- **Some emails are personal** (e.g. `imorvanclipet@citya.com` is the agency director's name). Still works — they forward to the right person.
- **Firecrawl credits exhaustion** blocks web_extract. Use curl with browser User-Agent as fallback — local agency sites don't have bot protection.
- **Browser tab crashes** (410/500 errors) when navigating to Cloudflare-protected sites. Don't loop — switch to curl or Brave Search.
- **DuckDuckGo and Bing search** for emails rarely returns email addresses in snippets. **Brave Search** is the reliable alternative for email harvesting.
- **Google Maps** is the best source for finding agencies (name + address + phone + website). Use the snapshot, not the map.
- **Garage/parking is "non obligatoire"** for this user — always phrase it as a plus, not a requirement. Adding it as mandatory would limit options and increase rent.
- **Brave Search image false positives**: responsive image URLs contain `@` (e.g. `image@1280x720.jpg`). Filter with `grep -v '@[0-9]*x[0-9]*'`.
- **Vehicle dimensions for garage**: if the user provides vehicle dimensions, add ~15-20cm margin for each dimension (length, width, height) when specifying minimum garage dimensions. The user's vehicle (463×181×144 cm) → garage minimum 480×250×150 cm.