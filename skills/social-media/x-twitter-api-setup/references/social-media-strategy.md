# Social Media Content Strategy — New Account Growth

This reference covers content planning for growing a fresh X/Twitter account for a product or brand. Use it when setting up a publishing schedule alongside xurl.

## Core Requirements (user expectations from a real session)

1. **High posting frequency** — multiple tweets per day, not one
2. **Zero repetition** — every post must feel fresh and unique
3. **Always different content angles** — no two posts about the same thing, even within a day
4. **UTM tracking** — every link to the product should carry `utm_source=twitter&utm_medium=social&utm_campaign=...` for analytics

## Content Categories (12 angles, rotate through these)

| # | Category | Example | Frequency |
|---|----------|---------|-----------|
| 1 | **Feature demo** | A specific product feature explained | 1x/week |
| 2 | **Hot take / debate** | "VF ou VO ?" — spawn discussion | 2x/week |
| 3 | **Recommendation** | "Le dernier film qui m'a retourné" | 2x/week |
| 4 | **Stats / fun fact** | "Tu sais que l'utilisateur moyen garde…" | 1x/week |
| 5 | **Sondage / poll** | "Plutôt Letterboxd ou Trakt ?" | 1x/week |
| 6 | **Humour / relatable** | "Quand tu passes 30 min à choisir un film" | 1x/week |
| 7 | **Nostalgie** | "Un film qui a marqué ton enfance ?" | 1x/week |
| 8 | **Community CTA** | "C'est quoi votre watchlist ce soir ?" | 2x/week |
| 9 | **Behind the scenes** | How the product was built, design choices | 1x/week |
| 10 | **Testimonial / UGC** | Share a user's review (with permission) | 1x/week |
| 11 | **Comparison** | Product vs alternatives, why it's different | 1x/week |
| 12 | **Quick tip** | A small trick the user might not know | 1x/week |

## Tweet Structure

1. **Hook** (first 1-2 lines) — question, hot take, or relatable statement
2. **Body** — expand, add value, be specific
3. **Link / CTA** — if including a URL: at the very end. URL-free tweets are 13× cheaper ($0.015 vs $0.20) and feel less promotional
4. **Links to product**: Always append `?utm_source=twitter&utm_medium=social&utm_campaign=<campaign_name>` for analytics

## Budget Optimization

| Tweet type | Cost | Strategy |
|-----------|------|----------|
| Text only (no URL) | $0.015 | 80% of posts. Drive engagement, not clicks |
| With link to product | $0.20 | 20% of posts. High-intent CTA only |
| Delete a tweet | $0.01 | Almost never needed |

With $5 credits: ~250 text tweets + ~8 link tweets before recharge.

## Day Structure (12 tweets/day example)

| Time | Type | Purpose |
|------|------|---------|
| 08:00 | Question / poll | Engage morning audience |
| 10:00 | Hot take / debate | Drive replies & quote-posts |
| 12:00 | Feature tip | Soft product mention |
| 14:00 | Nostalgia / culture | Shareable, warm content |
| 16:00 | Recommendation | Value-add, no link |
| 18:00 | Humor / relatable | Prime-time shareability |
| 20:00 | Community CTA | "What are you watching?" |
| 22:00 | Quick stat / fun fact | Late-night scroll content |

## Avoiding Repetition

- Track the last 3 categories used — never repeat within a window of 5 posts
- Vary the emotional tone: opinion → fact → question → humor → recommendation
- Use a content bank spreadsheet or a rolling list of 20+ pre-written drafts
- Cycle through different movies/shows: never reference the same film twice in one week

## Cron Job Automation

When using xurl + cron for scheduled posting:

1. Prepare a content bank file (JSON array of tweet texts with categories)
2. Cron picks a random entry, removing it from the pool to avoid repeats
3. Cron posts via `xurl post "..."` (text-only, no URL for most)
4. Cron replenishes the bank when it runs low (the agent or user refills it)

⚠️ **Rate limit awareness**: X enforces per-endpoint rate limits. ~300 posts per 3-hour window for standard accounts. Stay under 50/day to be safe.
