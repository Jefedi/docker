# Discord Channel Polish Guide

Visual standards for a clean, professional Discord server.
Learned from building Trakii.tv community server.

## Channel Naming Convention

Use emoji prefix + `・` (katakana middle dot U+30FB) + lowercase name:

| Pattern | Example |
|---------|---------|
| `🚀・start-here` | Onboarding |
| `📜・règles` | Rules |
| `🎭・roles` | Role selection |
| `📢・annonces` | Announcements |
| `👋・présentations` | Introductions |
| `💬・général` | General chat |
| `🔍・découvertes` | Discoveries |
| `📚・ressources` | Resources |
| `☕・blabla-hs` | Off-topic |
| `🎬・films` | Movies |
| `📺・séries` | TV shows |
| `⭐・recommandations` | Recommendations |
| `📝・critiques` | Reviews |
| `🍿・streaming` | Streaming discussion |
| `📅・events` | Events |
| `🎙️・event-chat` | Event live chat |
| `🔒・mod-chat` | Staff: mod discussion |
| `📋・mod-logs` | Staff: moderation logs |
| `🚨・incident-room` | Staff: incident management |
| `📌・staff-notes` | Staff: internal notes |

## Category Naming

Title Case, not ALL CAPS:
- `📌 Informations` ✅ not `📌 INFORMATIONS` ❌
- `💬 Communauté` ✅ not `💬 COMMUNAUTÉ` ❌
- `🎬 Ciné & Séries` ✅
- `📅 Events` ✅
- `🔒 Staff` ✅

## Topic Templates

Each channel should have a descriptive topic (max 1024 chars). Topics appear in the channel header.

### Info channels
```
start-here: "Bienvenue sur [Server] — ton premier arrêt pour comprendre le serveur"
règles: "Les règles à respecter — court et clair"
roles: "Choisis tes rôles : genres préférés, plateforme de streaming, et plus"
annonces: "Annonces officielles [Server] — nouveautés, mises à jour, événements"
```

### Community channels
```
présentations: "Présente-toi en 1-2 lignes : ton pseudo, tes goûts, ce que tu cherches ici"
général: "Discussion générale — tout ce qui tourne autour du sujet principal"
découvertes: "Tu viens de découvrir quelque chose ? Partage-le ici !"
ressources: "Sites, apps, newsletters, podcasts utiles"
blabla-hs: "Hors-sujet, détente — tout ce qui n'est pas le sujet principal"
```

### Content channels (adapt to server theme)
```
films: "Tout sur le cinéma — sorties, classiques, indé, blockbusters"
séries: "Tout sur les séries — en cours, finies, à découvrir"
recommandations: "Demande et donne des recommandations personnalisées"
critiques: "Poste tes critiques détaillées — note, analyse, avis"
streaming: "Où regarder quoi — Netflix, Prime, Apple TV+, Max, etc."
```

### Staff channels (private)
```
mod-chat: "Discussion staff — décisions, organisation"
mod-logs: "Logs automatiques — actions de modération"
incident-room: "Gestion des incidents — raid, spam, conflit"
staff-notes: "Notes internes — procédures, rappels"
```

## Slowmode Configuration

| Channel | Slowmode | Reason |
|---------|----------|--------|
| Off-topic / blabla | 5s | Prevent spam in casual chat |
| Event live chat | 3s | Manage flow during events |
| Announcements | 0s | Only staff posts anyway |
| General | 0s | Keep conversation flowing |

Set via `PATCH /channels/{id}` with `rate_limit_per_user: N` (seconds, 0-21600).

## Embed Message Patterns

### Welcome embed (start-here)
```json
{
  "embeds": [{
    "title": "🎬 Bienvenue sur [Server]",
    "description": "Description du serveur\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n**🚀 Par où commencer ?**\n\n**1.** 📜 Lis les règles\n**2.** 👋 Présente-toi dans <#ID>\n**3.** 🎭 Choisis tes rôles dans <#ID>\n**4.** 💬 Rejoins la discussion dans <#ID>\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n**🎯 Ce que tu peux faire ici :**\n\n• Point 1\n• Point 2\n• Point 3",
    "color": 0xFFD700,
    "footer": {"text": "[Server] — Tagline • Depuis 2026"},
    "timestamp": "2026-01-01T00:00:00.000+00:00"
  }]
}
```

### Rules embed
```json
{
  "embeds": [{
    "title": "📜 Règlement de [Server]",
    "description": "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n**1.** 🤝 **Respect mutuel**\nDescription\n\n**2.** 🚫 **Pas de spam**\nDescription\n\n...\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n**⚖️ Sanctions :**\nWarn → Timeout (10min-24h) → Ban (selon gravité)",
    "color": 0xFF4444,
    "footer": {"text": "En restant sur le serveur, tu acceptes ces règles"}
  }]
}
```

### Embed tips
- `color` is a hex int (not string): `0xFFD700` for gold, `0xFF4444` for red, `0x5865F2` for blurple
- Channel mentions in descriptions: `<#channel_id>` (resolve IDs before sending)
- Use `━━━━━━━━━━━━━━━━━━━━━━━━━━` (28 chars) as section separators
- `footer.text` for branding
- `timestamp` in ISO 8601 format
- Keep total embed under 6000 chars
- `thumbnail.url` for logo (if available)
- `content: null` when sending embed-only messages

## API call to rename + set topic + slowmode
```python
PATCH /channels/{channel_id}
{
  "name": "🚀・start-here",
  "topic": "Bienvenue sur [Server] — ton premier arrêt",
  "rate_limit_per_user": 0
}
```

## API call to rename a category
```python
PATCH /channels/{category_id}
{
  "name": "📌 Informations"
}
```