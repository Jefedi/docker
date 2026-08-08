# LLM Provider Privacy & EU Sovereign Alternatives

## Context

Hermes route tout son trafic LLM via LiteLLM (port 4000) → Ollama Cloud (US). Cette page documente les risques de confidentialité identifiés et les alternatives EU souveraines.

## Ollama Cloud — Risques identifiés (juillet 2026)

### Politique officielle (ollama.com/privacy, mars 2026)

- Prompts/réponses cloud traités "transitoirement", non stockés au-delà de la requête
- Jamais utilisés pour l'entraînement
- Partenaires (NVIDIA Cloud Providers) soumis à "no logging, no training, zero data retention"
- Hébergement "primarily in the United States", routage possible vers Europe et Singapour

### ⚠️ Points non résolus (Reddit, HN, GitHub)

1. **Pas de SOC 2, pas d'audit tiers** — la promesse ZDR est une promesse éditeur, pas une certification vérifiable. 21 employés seulement.
2. **Cheval de Troie "local-first"** (HN thread très relayé) — `ollama run glm-5.2:cloud` utilise le même CLI/API que local, aucun warning. `OLLAMA_NOCLOUD=1` existe mais est opt-in (désactivé par défaut).
3. **Proxification vers providers d'origine ?** — Question ouverte : `glm-5.2:cloud` reste-t-il sur l'infra Ollama ou est forwardé vers Z.ai (ex-Zhipu AI, firme chinoise) ? Pas de réponse claire d'Ollama.
4. **Politique de confidentialité manquante au lancement** — ajoutée après les critiques communautaires.
5. **Juridiction US + CLOUD Act** — données transitent par les US → soumises au CLOUD Act et FISA 702. Pour un utilisateur EU : transferts transfrontaliers non contrats.

### CVE-2026-7482 "Bleeding Llama" (mai 2026)

- Heap out-of-bounds read dans le loader GGUF d'Ollama (CVSS 9.1-9.3 CRITICAL)
- ~300 000 serveurs Ollama exposés sur internet
- Non authentifié — 3 appels API suffisent (`/api/blobs` → `/api/create` → `/api/push`)
- **Ce qu'un attaquant peut voler** : prompts/messages en mémoire, variables d'environnement (clés API, tokens), code source, outputs d'outils agentic
- Patché dans Ollama 0.17.1
- Source : Cyera Research (cyera.com/blog/bleeding-llama)

### Niveau de risque par type de données

| Données | Risque | Recommandation |
|----------|--------|----------------|
| Chat général, automatisation HA, courses | 🟢 Faible | OK tel quel |
| Emails (contenu via prompts) | 🟡 Moyen | Préfiltrer avant d'envoyer |
| Documents Paperless (factures, admin) | 🟠 Élevé | Ne pas envoyer en cloud |
| Données financières / PII | 🔴 Critical | Jamais en cloud |
| Config infra (IPs, tokens dans context) | 🟠 Élevé | Sanitiser les prompts |

### Actions de hardening

1. Vérifier version Ollama sur jTower (≥ 0.17.1 pour la CVE)
2. S'assurer que le port 11434 n'est pas exposé sur internet
3. `OLLAMA_NOCLOUD=1` si on ne veut que du local sur jTower
4. Router les données sensibles vers un modèle local (gpt-oss-20b tourne déjà sur jTower)
5. Garder le cloud pour les tâches non-sensibles

## TensorX / EuroRouter (eurorouter.ai) — Alternative EU souveraine

### Identité

- Plateforme d'inférence européenne souveraine (datacenters en UE)
- Zero Data Retention by design
- GDPR compliant, ISO 27001 ready
- API OpenAI-compatible (`https://api.tensorx.ai/v1`)
- Membre NVIDIA Inception Program
- Claim 60%+ cost savings vs OpenAI/Anthropic

### Modèles disponibles — mêmes qu'Ollama Cloud

| Modèle TensorX | Équivalent Ollama Cloud | Context |
|----------------|------------------------|---------|
| `z-ai/glm-5.2` | `glm-5.2:cloud` | 1M |
| `minimax/minimax-m3` | `minimax-m3:cloud` | 1M |
| `deepseek/deepseek-v4-pro` | `deepseek-v4-pro:cloud` | 1M |
| `deepseek/deepseek-v4-flash` | `deepseek-v4-flash:cloud` | 1M |
| `moonshotai/kimi-k2.6` | `kimi-k2.6:cloud` | 256K |
| `moonshotai/kimi-k2.7-code` | `kimi-k2.7-code:cloud` | 256K |

### Comparaison Ollama Cloud vs TensorX

| Critère | Ollama Cloud | TensorX |
|---------|-------------|---------|
| Juridiction | 🇺🇸 US (+ EU/Singapour) | 🇪🇺 UE souveraine |
| Data retention | "Pas stocké" (promesse) | Zero by design |
| GDPR | ⚠️ Transferts US → CLOUD Act | ✅ Natif |
| ISO 27001 | ❌ Non | ✅ Ready |
| OpenAI-compat | Via Ollama API | ✅ Drop-in `/v1/chat/completions` |
| CLOUD Act | 🔴 Soumis | 🟢 Non (entité UE) |

### Migration (depuis LiteLLM)

Côté LiteLLM, c'est un changement de `base_url` + `api_key` :
- **Base URL** : `https://api.tensorx.ai/v1`
- **API key** : `tx-...`
- **Modèles** : mêmes noms avec préfixe provider (`z-ai/glm-5.2`, `minimax/minimax-m3`, etc.)

### ⚠️ Points d'attention TensorX

- Jeune structure, moins de track record qu'Ollama
- Pas de SOC 2 publié non plus
- Pricing non public — créer un compte pour vérifier
- Disponibilité/uptime à tester vs Ollama Cloud

## Autres alternatives EU identifiées

| Provider | Type | Particularité |
|----------|------|---------------|
| **Regolo.ai** | Inférence UE (Italie) | ZDR, OpenAI-compat, token-based pricing |
| **EUrouter** | Router UE | Drop-in OpenAI-compat, DPA GDPR |
| **Requesty EU** | Gateway UE (Frankfurt) | Route Claude/GPT/Gemini via EU, DPA |
| **Eden AI** | Gateway UE (France) | 500+ modèles, DPA, EU endpoint |
| **JuiceFactory** | Inférence UE (Suède) | Zero retention natif, DPA inclus |

## Stratégie recommandée pour Jefe

Architecture actuelle :
```
Hermes → LiteLLM (4000) → Ollama Cloud (US) → glm-5.2
```

Architecture recommandée (hybride) :
```
Hermes → LiteLLM (4000) → TensorX (UE) pour données sensibles
                       → Ollama Cloud (US) pour tâches non-sensibles
                       → gpt-oss-20b (local) pour données critiques
```

LiteLLM supporte le routing par modèle/tag — on peut définir un tag `sensitive` qui route vers TensorX et un tag `general` qui route vers Ollama Cloud.