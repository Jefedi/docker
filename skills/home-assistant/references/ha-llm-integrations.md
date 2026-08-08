# Intégrations LLM dans Home Assistant

## Ollama Cloud → HA : le piège de l'API

### Problème

Ollama Cloud (`ollama.com`) expose uniquement un endpoint **OpenAI-compatible** (`/v1/`).
L'API native Ollama (`/api/tags`, `/api/chat`) n'est **pas disponible** sur ollama.com — elle retourne 404.

### Ce qui ne marche PAS

| Intégration HA | Pourquoi ça échoue |
|---|---|
| `ollama` (core) | Utilise l'API native Ollama (`/api/`). ollama.com n'expose pas cette API → 404 dans les logs HA. |
| `openai_conversation` (core) | Le dialog de config initiale demande uniquement une clé API, pas de base URL. Pointe par défaut vers `api.openai.com`. Pas de champ base URL au setup. |

Logs typiques :
```
Error response from Ollama server at https://ollama.com/api: status 404, detail: {"tags":[]}
```

### Solution : Extended OpenAI Conversation (HACS)

Le custom component **Extended OpenAI Conversation** (HACS) permet de configurer un **base URL custom** + clé API, ce qui permet de pointer vers `https://ollama.com/v1`.

**Workflow :**
1. Installer **Extended OpenAI Conversation** via HACS (category: integration)
2. Ajouter l'intégration : Settings → Devices & Services → Add → "Extended OpenAI Conversation"
3. Configurer :
   - **API Key** : clé Ollama Cloud (de https://ollama.com/settings)
   - **Base URL** : `https://ollama.com/v1`
   - **Model** : au choix (glm-5.2, deepseek-v4-pro, kimi-k2.7-code, etc.)
4. L'intégration apparaît sous le nom donné (ex: "Ollama Cloud"), state `loaded`

### Vérification

```python
# Via MCP HA
ha_get_integration(domain="extended_openai_conversation")
# → state: "loaded", title: "Ollama Cloud"
```

### Alternative : LiteLLM comme proxy

Si on veut garder l'intégration Ollama native de HA, on peut exposer un proxy LiteLLM local :
- LiteLLM écoute sur `localhost:4000` (OpenAI-compatible)
- HA pointe vers `http://<IP_TAILSCALE>:4000/v1` avec l'intégration OpenAI ou Extended OpenAI
- LiteLLM route vers Ollama Cloud en backend

### Résumé des endpoints Ollama Cloud

| Endpoint | URL | Usage |
|---|---|---|
| OpenAI-compatible | `https://ollama.com/v1/chat/completions` | ✅ Pour HA (Extended OpenAI Conversation) |
| OpenAI models list | `https://ollama.com/v1/models` | ✅ Liste des modèles disponibles |
| Native Ollama API | `https://ollama.com/api/tags` | ❌ 404 — n'existe pas sur ollama.com |

### Ollama local vs Ollama Cloud

- **Ollama local** (`http://<IP>:11434`) : expose l'API native `/api/` → compatible avec l'intégration `ollama` core de HA
- **Ollama Cloud** (`https://ollama.com`) : expose uniquement `/v1/` (OpenAI) → nécessite Extended OpenAI Conversation ou proxy