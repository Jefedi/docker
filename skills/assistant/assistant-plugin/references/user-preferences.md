## Préférences d'utilisation

- **Concise, sans emoji** : tous les messages de configuration ou de diagnostic seront courts ; aucun emoji (ex : 🤫) ne sera inclus.
- **Pas de verbosité** : le mode `verbose` reste désactivé (`false`) par défaut. Pour plus de détails, l'utilisateur doit activer explicitement ce mode ou définir `HERMES_VERBOSE=1`.

## Format des commandes sur Telegram (CRITIQUE)

L'utilisateur interagit principalement via Telegram sur mobile. La copie de commandes formatées (backticks, code blocks) est **cassée** : Telegram ajoute/retire des caractères ou copie mal le contenu.

**Règles obligatoires pour envoyer une commande à exécuter :**

1. **Un message = une commande, rien d'autre.** Pas de texte avant ou après, pas d'explication, pas de contexte.
2. **Pas de backticks, pas de code blocks.** La commande en texte brut uniquement.
3. **Explication dans un message séparé** (si nécessaire).
4. L'utilisateur fait long-press → copier le message entier → ça marche.

Exemple correct — Message 1 :
```
sudo chown -R jefe:jefe /srv/docker/radicale
```
Message 2 (séparé) :
```
C'est noté. Dis-moi quand c'est fait.
```

Exemple **INTERDIT** (tout dans un message, avec backticks) :
```
Voici la commande :
`sudo chown -R jefe:jefe /srv/docker/radicale`
Dis-moi quand c'est fait.
```

Ces préférences seront automatiquement appliquées dans les futures sessions Hermes.

## Explications techniques : pas de jargon sans définition

L'utilisateur est power user mais **ne connaît pas le réseau profond** (DNS autoritatif, RPZ, AXFR, etc.). Quand un sujet technique implique du jargon spécialisé :

- **Ne jamais balancer des termes techniques sans les expliquer**. Si tu utilises "DNSSEC", "RPZ", "zone transfer", "DoH", "forwarder conditionnel" — donne une définition simple en français + un exemple concret basé sur son infra (jefe.al, x42, Pangolin, iPhone).
- **L'utilisateur l'a dit explicitement** : "la moitié des termes que tu as utilisés, pas la moindre idée de ce que ça fait". C'est un signal clair : il veut comprendre, pas juste recevoir un tableau de comparaisons avec des mots qu'il ne peut pas interpréter.
- **Format suggéré** : terme → définition simple en 1-2 phrases → exemple concret avec son setup. Pas de paragraphe académique.
- **Si l'utilisateur demande une vocale TTS** pour une explication longue, utiliser `text_to_speech` avec `provider='mistral'` (voix française configurée).

## Research & reconnaissance : filtrer au niveau de l'utilisateur

L'utilisateur est un **power user** (Docker-in-Docker, LiteLLM multi-provider routing, MCP servers, n8n, Home Assistant, Pangolin, profils multiples). Quand il demande de la recherche sur un sujet technique (comment les autres font X, quel outil pour Y) :

- **Filtrer immédiatement** le contenu beginner/intermediate. Ne pas retranscrire ce que les forums disent à un niveau de base.
- **Highlighter uniquement les deltas** vs le setup actuel de l'utilisateur : qu'est-ce qui est différent, meilleur, ou nouveau par rapport à ce qu'il a déjà ?
- **Max 3-5 points actionables**, pas un panorama complet. Si le contenu n'apporte rien de nouveau, le dire directement dès le début.
- **Pas de tableau récapitulatif** du paysage complet si l'utilisateur connaît déjà 90% du sujet. Aller droit aux 10% qu'il ne connaît pas.

Le user a explicitement dit "tu m'apporte rien la" après un dump complet de recherche Reddit sur la config Hermes — il fallait extraire uniquement les 2-3 trucs qu'il n'avait pas (AGENTS.md, skill hygiene cron, Signal E2E) et skipper le reste.

## Multi-line files via Telegram (base64 technique)

Les heredocs (`cat > file << 'EOF'`) et commandes `python3 -c` multi-lignes se cassent quand on les copie depuis Telegram (sauts de ligne perdus, caractères mélangés).

**Solution : base64 encoding.** Encode le contenu du fichier en base64, envoie une seule commande single-line :

```
echo '<base64 string>' | base64 -d > /path/to/file
```

L'utilisateur copie cette ligne unique → le fichier est créé parfaitement, sans aucun caractère manquant ou ajouté.

Pour générer le base64 côté agent (avant d'envoyer) :
```python
import base64
content = """services:
  radicale:
    image: tomsquest/docker-radicale:latest
    ..."""
print(base64.b64encode(content.encode()).decode())
```