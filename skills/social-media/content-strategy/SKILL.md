### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---
name: content-strategy
title: Social Media Content Strategy & Growth
description: "Plan and execute a content strategy on X/Twitter — tweet categories, variety principles, frequency planning, cost optimization, UTM tracking, and audience building."
version: 1.0.1
tags: [twitter, x, content-strategy, social-media, growth, marketing]
### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---

# Content Strategy & Growth

Plan and execute a content strategy on X/Twitter for launching and growing a service account.

## When to Load This Skill

- User wants to promote a service/product on X/Twitter
- User wants to grow their account (more followers, engagement)
- User asks for a tweet schedule or content plan
- User needs help with varied, non-repetitive content

## Approval Process for Posts

This section is specifically added for users who require **manual approval before each tweet** (e.g., real‑time control, image validation, or data‑privacy). The workflow below captures the steps you should follow in the assistant.

1. **Generate a single tweet** (text only) using the AI/Template. Do not send multiple tweets in one response.
2. **Show the full, final tweet** to the user. Include any URL with full UTM before posting.
3. **If an image is part of the tweet, provide the image itself** (via inline attachment or `MEDIA: path`). Never ask “with or without image” without displaying the actual image.
4. **Ask for a clear yes/no decision** (`Tu valides ?`). If the user says **No**, request clarification, revise the text or image, and present the updated draft as a *new* proposal.
5. **Only when the user says Noe** do you use xurl or the equivalent to post.
6. **After posting**, immediately reply with the tweet URL (e.g., https://x.com/username/status/1234567890) as confirmation.
7. **Do NOT run a cron or auto‑post** without the user's explicit approval during the same session.

### Why This Matters
- Users often want a display of media before posting; the assistant must not automatically upload a screenshot that the user hasn't seen.
- The X API requires a media ID that expires in 24 h; posting before the user views confirms the media.
- Avoiding pre‑approved multi‑tweet groups respects the user’s desire for granular control.

## Core Principles

1. **Variety is mandatory** — never post the same angle twice in a row
2. **High frequency** builds algorithmic momentum (3-10+ tweets/day)
3. **Cost matters** — on X API Pay-Per-Use, text-only tweets are $0.015, tweets with URLs are $0.20
4. **UTM tracking** on every link so you can measure which channel drives traffic

## Tweet Category System

Rotate across categories — never use the same one twice in a row:

### Discovery (Feature Promotion)
- Feature spotlight: one specific feature per tweet
- Screenshot showcase: show the interface in action
- Comparison: subtle positioning against alternatives
- Testimonial angle
- CTA: direct invite with link

### Curation (Engagement Drivers)
- Hot take / debate: controversial opinion
- "What are you watching?" open question
- Polls: ratings, comparisons, preferences
- Top/list: "Top 3 [topic]"
- Throwback / nostalgia
- Seasonal content

### Community Building
- Reply to mentions
- Quote-reply to relevant posts
- Follow accounts in your niche
- Like and engage with others' content

### Culture / Humor
- Relatable memes about the niche
- Fun facts / trivia
- Behind-the-scenes of building the service

## Budget Planning (X API Pay-Per-Use)

With $5 of credits:
- Text-only tweets: ~333 tweets ($0.015 ea)
- Tweets with URL: ~25 tweets ($0.20 ea)

**Recommended mix:** 6-10 text-only + 1-2 with URL per day = ~$0.30-0.40/day → $5 lasts 12-16 days

## URL / Link Handling

Always use UTM parameters:
```
https://site.com/?utm_source=twitter&utm_medium=social&utm_campaign=launch
```

Convention:
- `utm_source`: platform (`twitter`)
- `utm_medium`: (`social`, `tweet`, `bio`)
- `utm_campaign`: campaign name (`launch`, `feature-x`)

X auto-shortens links to `t.co/...` — no external shortener needed.

## Avoiding Repetition

- Batch-write 15-20 tweets before starting
- Group by category, then shuffle
- Never use the same opening phrase twice in the same week
- Vary media: image, no image, poll
- Mix personal voice (Je regardais…) with community voice (Vous matez quoi ?)

## Scheduling Template (First Week)

| Day | Tweet 1 | Tweet 2 | Tweet 3 | Tweet 4 | Tweet 5 |
|### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

-----|### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---|### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---|### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---|### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---|### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---### Using the Hermes API in n8n

Add a small section to the skill explaining how to set up an HTTP request to the Hermes API server exposed on your host. The base URL is `http://host.docker.internal:8642/v1` and the API key is `hermes-ios-shortcut-a80ac18a29ed5d62`.

In a workflow, use an OpenAI node or an HTTP Request node:

```json
{
  "model": "hermes‑agent",
  "messages": [{"role": "user", "content": "Suggest an engaging tweet about our new feature."}],
  "stream": false
}
```

The node should pass the request as a POST to `/v1/chat/completions`. This is faster and keeps all data on‑premises.

---|
| Mon | Launch/CTA (URL) | Feature: import | Poll | Hot take | Reco |
| Tue | Feature: journal | "What're you watching?" | Meme | Testimonial | CTA (URL) |
| Wed | Comparison | Series reco | Poll | Feature: ratings | Culture |
| Thu | Throwback | Feature: reviews | Debate | CTA (URL) | Fun fact |
| Fri | Weekend watchlist | Feature: stats | Poll | Meme | CTA (URL) |
| Sat | Chill reco | Community question | Feature | Culture | — |
| Sun | Recap thread | Open question | CTA (URL) | Feature | — |

## Per-Tweet Execution Workflow (Manual Approval)

When the user wants you to post tweets on their behalf — one at a time, no auto-posting:

### The Approval Loop
1. **Propose ONE tweet at a time.** Never list multiple tweets and ask "which ones do you want?" — handle them sequentially.
2. **Show the EXACT tweet text** as it will appear, including the full URL (not just the domain).
3. **If an image is included, SHOW the image to the user.** Send the actual image file (MEDIA: path on Telegram, inline image on other platforms). Never ask "with or without image?" without the user having seen the image first. 
4. **Ask a clear binary question:** "Tu valides ?" / "Je poste ?"
5. **If yes:** upload media via xurl, post with `--media-id`, then reply with the tweet URL as confirmation.
6. **If no:** ask what to change, revise, then show the updated version in a fresh proposal.
7. **Only move to the next tweet** once the current one is either posted or cancelled.

### Critical Rules
- **No auto-posting cron without explicit sign-off.** The user said: "au moment venu tu me demandes en me affichant précisément quelle post tu veux faire est je valide ou pas à ce moment là."
- **A text-only description of an image is not enough.** The user said: "Quelle image aussi si je vois pas je vais pas dire oui ?" — they must see the actual visual to decide.
- **After posting**, always include the post URL (https://x.com/username/status/ID) as confirmation.
- **Track media upload status.** xurl returns a media ID — use it immediately in the same session before the 24h expiration.

### Technical Pitfalls

#### xurl Not in PATH (Containerized Environments)

In Docker/s6 environments, xurl may not be on $PATH. The binary lives at ~/.local/bin/xurl. Use this pattern for every xurl call:

```bash
HOME=/opt/data/home PATH=/opt/data/home/.local/bin:$PATH xurl auth status
HOME=/opt/data/home PATH=/opt/data/home/.local/bin:$PATH xurl post "text" --media-id ID
```

#### 403 Posting Error — Credits Needed

xurl post returning 403 usually means the X API has no credits. Diagnosis:

```bash
HOME=/opt/data/home PATH=/opt/data/home/.local/bin:$PATH xurl whoami
# subscription_type: "None" → Free tier, can't post
```

Fix: user adds $5 minimum credits on **console.x.com → Settings → Billing → Credits**.

#### Media: Screenshot Fallback When Image Generation Unavailable

When image_generate is unavailable (no FAL_KEY), use a browser screenshot as tweet media:

1. browser_navigate(url) → load the page
2. browser_vision(question="Full page") → capture screenshot
3. Note screenshot_path from the response
4. Upload: xurl media upload --media-type image/png --category tweet_image /path/screenshot.png
5. Post: xurl post "text" --media-id MEDIA_ID