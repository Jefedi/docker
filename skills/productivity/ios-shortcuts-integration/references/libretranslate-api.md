# LibreTranslate API — Reference (confirmé août 2026)

## Instance

- **Conteneur Docker** : `libretranslate`, bind `127.0.0.1:5000`, healthy
- **Public** : `https://translate.jefe.ovh` (via reverse proxy)
- **API key** : `53e04e31-de93-4b49-a0e4-891b1806fc8d`

## Auth — CRITIQUE

La clé API se passe **dans le body JSON**, PAS dans les headers.

### ❌ Headers testés et rejetés (400 "Please contact the server operator")

| Header | Format testé | Résultat |
|--------|-------------|----------|
| `Authorization` | `Bearer <key>` | 400 |
| `X-API-Key` | `<key>` | 400 |
| `api_key` | `<key>` | 400 |

### ✅ Body field — fonctionne

```json
POST /translate
Content-Type: application/json

{
  "q": "hello",
  "source": "en",
  "target": "fr",
  "format": "text",
  "api_key": "53e04e31-..."
}
```

Réponse : `{"translatedText": "bonjour"}`

## Endpoints

### /translate — texte

```bash
curl -s http://127.0.0.1:5000/translate \
  -H "Content-Type: application/json" \
  -d '{"q":"hello","source":"en","target":"fr","format":"text","api_key":"53e04e31-..."}'
```

### /translate_file — fichiers

Supporte : `.txt`, `.odt`, `.odp`, `.docx`, `.pptx`, `.epub`, `.html`, `.srt`, `.pdf`

```bash
curl -s http://127.0.0.1:5000/translate_file \
  -F "file=@document.pdf" \
  -F "source=en" \
  -F "target=fr" \
  -F "api_key=53e04e31-..."
```

Réponse : `{"translatedFileUrl": "http://127.0.0.1:5000/download_file/<uuid>.<filename>_fr.<ext>"}`

### /download_file/<uuid>.<filename>_<lang>.<ext>

GET simple, pas d'auth. Retourne le fichier traduit.

## Format supportés

`format` param : `"text"` ou `"html"`

## Langues

`source` peut être `"auto"` pour auto-détection. Liste : fr, en, es, de, it, pt, nl, ru, ar, zh-Hans, ja, ko, etc.