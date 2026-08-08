---
name: dl
description: "Télécharger des vidéos via /dl sur Telegram en utilisant le MCP MeTube"
version: 1.0.0
author: Hermes Agent
tags: [telegram, metube, youtube, download, command]
---

# DL — Commande `/dl` sur Telegram

Quand l'utilisateur envoie un message commençant par `/dl` suivi d'une URL,
utilise le MCP **metube** pour ajouter le téléchargement via MeTube (yt-dlp).

## Usage

```
/dl https://www.youtube.com/watch?v=xxx
/dl https://youtu.be/xxx
/dl https://vimeo.com/xxx
/dl https://www.tiktok.com/@user/video/xxx
```

## Comportement attendu

1. Détecte le pattern `/dl <url>` dans le message Telegram
2. Extrait l'URL (supprime le préfixe `/dl `)
3. Appelle `mcp_metube_add_download` avec `url` et `quality="best"`
4. Répond à l'utilisateur avec :
   - ✅ "Ajouté: [titre de la vidéo]" si succès
   - ⚠️ "Erreur: [message]" si échec

## Qualité par défaut

`best` — meilleure qualité vidéo disponible (peut être modifié via un second argument).
