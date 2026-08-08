# STT OpenAI-compatible (Dicter / serveur self-hosted)

## Objectif

Remplacer le STT cloud Mistral/Voxtral par un endpoint self-hosted compatible OpenAI, tout en gardant le bloc `stt.mistral` pour un retour manuel rapide.

## Configuration sûre

Secrets uniquement dans `$HERMES_HOME/.env` (permissions `0600`) :

```dotenv
VOICE_TOOLS_OPENAI_KEY=<bearer-token>
STT_OPENAI_BASE_URL=https://stt.example.net/v1
STT_OPENAI_MODEL=<model-id-exact>
```

Dans `config.yaml` :

```yaml
stt:
  enabled: true
  provider: openai
  openai:
    model: <model-id-exact>
  mistral:
    model: voxtral-mini-latest # conservé, inactif
```

Hermes utilise `VOICE_TOOLS_OPENAI_KEY` et l’override `STT_OPENAI_BASE_URL` pour son provider STT `openai`.

## Découverte et validation

1. Découvrir les IDs réels : `GET <base-url>/models` avec `Authorization: Bearer …`.
2. Choisir un modèle marqué disponible, en gardant l’ID exact retourné par l’API.
3. Tester réellement `POST <base-url>/audio/transcriptions` avec multipart : `file=@audio.wav` et `model=<id>`.
4. Vérifier un JSON contenant `text` : cela valide URL, bearer token, endpoint et modèle.
5. Le gateway doit être relancé pour recharger `.env` et `config.yaml`. Ne jamais le redémarrer sans accord explicite de l’utilisateur.

## Cas validé chez Jefe

- Base URL : `https://dicter.jefe.al/v1`
- Modèle disponible retenu : `Systran/faster-whisper-medium`
- Le test multipart de transcription a renvoyé avec succès un champ `text`.

Ne jamais stocker le token Dicter dans ce fichier, dans un skill ou dans la mémoire.
