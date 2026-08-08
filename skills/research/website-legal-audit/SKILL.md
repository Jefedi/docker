---
name: website-legal-audit
description: >
  Systematically audit a website's legal pages — Terms of Service, Privacy Policy,
  Cookie Policy — to understand data collection, storage, retention, third-party
  sharing, cookies, user rights, and jurisdictional protections. Output a structured
  summary for the user in their language.
triggers:
  - User asks: "check this site's terms/privacy/data practices"
  - User asks: "what does [site] do with my data"
  - User asks: "est-ce que [site] stocke/garde/réutilise les données"
  - Any request to audit a website's legal or privacy documentation
---

# Website Legal & Privacy Audit

## Workflow

### 1. Probe the homepage
Start with `web_extract(urls=["https://example.com"])` to get the main page and spot footer links (Terms, Privacy, Cookie Policy). Then navigate with the browser to trigger any cookie-consent popup.

### 2. Try common legal-page URLs (parallel)
Batch these in one call:
```
/terms         /privacy        /legal
/terms-of-service  /privacy-policy  /cookie-policy
/terms-conditions  /terms-of-use    /tos
```
When one returns content, note it — the Privacy Policy and Terms & Conditions are the two critical documents.

### 3. Handle cookie consent with the browser
- The browser triggers cookie popups automatically
- Click **Accept** or **Dismiss** first, then scroll to find footer links
- The cookie-policy link itself often leads to the full Cookie Policy page

### 4. Read large documents with read_file pagination
Legal docs are often 50k–100k+ chars. `web_extract` saves the full text to `/opt/data/cache/web/` and tells you the path and line numbers. Use:
```
read_file(path="...", offset=1, limit=200)
```
Then continue with `offset=201`, `offset=401`, etc. Key sections to find:

| Section | What to look for |
|---|---|
| **Information Collected** | Account data, search queries, OSINT data, technical data, cookies |
| **Data Storage & Retention** | How long each type is kept, auto-deletion policies, backups |
| **Data Usage / Sharing** | Profiling, model training, advertising, selling data, third-party sharing |
| **Cookies** | Third-party cookies, durations (watch for 10+ year cookies), opt-out links |
| **Opt-Out / Right to Erasure** | Opt-out URL, verification (OTP), suppression scope, DPO contact |
| **Governing Law** | Jurisdiction, arbitration clauses, class action waivers, statute of limitations |
| **Company Info** | Legal entity name, address (often Delaware for US-based services) |

### 5. Analyze cookie durations
Scan for abnormally long cookie lifetimes — `_cio` (Customer.io) at 20 years, persistent advertising cookies at 1 year+.

### 6. Compile a structured summary
Present findings in the user's language with clear sections:
- What data is collected
- How long it's stored
- Whether it's reused/sold/shared
- Cookie inventory (with durations)
- Opt-out / deletion options
- Jurisdiction and legal protections
- Red flags (extremely long cookies, no opt-out, Delaware-only arbitration, etc.)

Use tables for cookie data, bullet lists for summaries, and bold for critical findings (`⚠️` for warnings).

## Pitfalls

- **/terms and /privacy often 404** — try `/terms-conditions`, `/privacy-policy`, `/terms-of-service`. The Privacy Policy for one region (EU) may be at a different path from the general one.
- **Cookie popup blocks footer** — Accept/Reject it first before scrolling to the bottom.
- **Browser tool is slow** — use `web_extract` for static text pages; reserve the browser for cookie consent and interactive elements.
- **Large docs truncate in web_extract** — always check if the page was truncated (look for the "TRUNCATED" marker and the saved file path) and use `read_file` to page through the middle.
- **Privacy Policy may reference TOS and vice versa** — you need both documents to get the full picture; they incorporate each other by reference.
- **Cookie policy may be a separate page** not linked from the footer banner — check the cookie consent popup's "Learn more" link.
