#!/usr/bin/env bash
# Envoie un rappel Discord à léoytb pour le paiement serveur
# Exécuté le 1er de chaque mois par Hermes cron

TOKEN=$(cat /opt/data/scripts/.discord_token_rappel)
CHANNEL_ID="1510929495295791155"  # DM léoytb

curl -s -X POST \
  -H "Authorization: Bot $TOKEN" \
  -H "User-Agent: DiscordBot" \
  -H "Content-Type: application/json" \
  -d '{
  "embeds": [{
    "title": "📆 C'"'"'est bientôt l'"'"'échéance bg !",
    "description": "Hé **léoytb** ! 👋\n\nPetit rappel tranquille que le paiement pour le serveur tombe le **3 du mois** (de la part de Réfait).\n\nSi tu peux envoyer ça avant, c'"'"'est top — ça évite les coupures et tout roule 🌊\n\nMerci d'"'"'avance, à très vite ! 🤝",
    "color": 5793266,
    "footer": {
      "text": "Rappel auto — 1er du mois"
    }
  }]
}' https://discord.com/api/v10/channels/$CHANNEL_ID/messages
