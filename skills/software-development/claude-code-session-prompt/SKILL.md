---
name: claude-code-session-prompt
description: Génère un prompt de session structuré pour piloter un projet self-hosted via Claude Code en mode manager/sous-agents (rôle chef de projet qui délègue à des sous-agents, validation par criticité, garde-fous accumulés, journal de session). Couvre deux modes — genèse (nouveau projet, repo vide à bootstrapper) et continuation (reprise d'un projet en cours, session N+1, sans refaire l'existant). À utiliser dès que l'utilisateur demande un prompt de genèse, un prompt de continuation, un prompt de session, un prompt d'orchestration, un prompt pour reprendre/relancer/poursuivre un projet dans Claude Code, ou veut transformer un projet en prompt réutilisable façon "Central Control", même s'il n'emploie pas explicitement le mot skill ou prompt. Produit un fichier Markdown en français suivant le gabarit 11 sections.
---

# Claude Code — Prompt de session (genèse & continuation)

Ce skill produit **un prompt de session prêt à coller dans Claude Code** : le texte qui établit, en début de session, le rôle de l'agent comme **manager** d'un projet self-hosted, sa stack figée, son état, sa roadmap, ses garde-fous et sa façon de communiquer. Le format de référence est celui des prompts « Central Control » / « Trakii » de l'utilisateur — voir les exemples en `references/`.

Le prompt généré n'est PAS du code. C'est un document de pilotage que l'utilisateur sauvegarde (souvent comme `PROMPT.md` du projet) et recolle au démarrage de chaque session, et qui dit à l'agent de relire `CLAUDE.md` + les ADR + la spec courante avant d'agir.

## Principe directeur

Ces prompts sont efficaces parce qu'ils sont **brutalement spécifiques** et **anti-régression** : ils figent la stack pour empêcher la dérive, listent exhaustivement ce qui est déjà livré pour ne PAS le refaire, encodent les garde-fous appris à la dure, et imposent un workflow de validation proportionné au risque. Reproduis cette densité — un prompt vague ne sert à rien.

---

## Étape 1 — Déterminer le mode

|  | **Genèse** (session 1) | **Continuation** (session N+1) |
|---|---|---|
| Déclencheur | « nouveau projet », « on part de zéro », repo vide, « prompt de genèse » | « reprends », « continue », `CLAUDE.md` existe déjà, « session N+1 » |
| §3 État actuel | « rien livré » + liste du **bootstrap** à produire en Phase 0 | liste **exhaustive de ce qui est livré** (NE PAS REFAIRE) + stats |
| §10 Première action | créer scaffolding + ADR + charters + spec Phase 0, puis enchaîner | relire `CLAUDE.md` + spec, vérifier le builder en background, finaliser |
| §1 Lecture obligatoire | ces fichiers n'existent pas encore → Phase 0 les crée | les lire dans l'ordre AVANT toute action |
| Exemple de référence | `references/example-trakii-genese.md` | `references/example-central-control-continuation.md` |

Si le mode n'est pas explicite, déduis-le : présence d'un `CLAUDE.md` / d'un historique de sessions = continuation ; sinon genèse. En cas de doute réel, demande — c'est un fork structurant.

---

## Étape 2 — Rassembler le contexte (déduire d'abord, demander en dernier)

L'utilisateur communique terse et déteste les questions évitables (« pas de question si je peux deviner à partir du contexte »). Donc **déduis le maximum avant de demander** :

1. **Lis sa source de vérité Obsidian** (profil homelab) et, en continuation, le **`CLAUDE.md` du projet** + son journal §10. C'est là que vivent les conventions réelles (nodes, IPs Headscale, domaines, stack par défaut, garde-fous existants).
2. **Exploite la conversation** : si le projet vient d'être discuté (comme Trakii l'a été), extrais nom, stack, archi, décisions déjà prises.
3. **Applique les constantes** de `references/conventions.md` (rôle manager, table de criticité, style de comm, défauts d'infra) — elles sont quasi identiques d'un projet à l'autre.

Ne demande QUE les **forks structurants** où deviner serait risqué. Inputs typiquement nécessaires (à déduire ou, à défaut, à confirmer) :

- Nom/codename du projet + domaine (`xxx.jefe.al`)
- Mode (genèse / continuation)
- Hébergement (node : AX42 / VPS / jNas…), exposition (Pangolin), auth (Pocket-ID OIDC)
- Stack figée (langages, frameworks, runtime, DB, CI) — déduire du type de projet, voir défauts en `conventions.md`
- Branche Git (`claude/<slug>-<hash>`) + repo GitHub
- **Continuation** : ce qui est déjà livré (depuis `CLAUDE.md §3`) + garde-fous existants (`§6`)
- Roadmap / prochaines phases + **criticité de chacune**
- Patterns non négociables propres au domaine (secrets, anti-fuite, idempotence, optimistic UI, destructif…)

Si une valeur d'infra reste inconnue, laisse un `<À CONFIRMER>` explicite plutôt que d'inventer, et signale-le à la fin.

---

## Étape 3 — Remplir le gabarit

Lis `references/template.md` : c'est le squelette 11 sections à remplir. Règles de remplissage :

- **Réutilise verbatim** les blocs constants depuis `references/conventions.md` : §0 (rôle manager + workflow 8 étapes + Auto Mode), §6 (table de criticité + types de sous-agents), §9 (style de communication). On n'adapte que les détails de domaine.
- **§2 Stack figée** : sois précis et opiniâtre (versions, flags TS strict, contraintes). « NE PAS DÉVIER ». Pioche dans les défauts d'infra de `conventions.md`.
- **§3** : voir le tableau de l'Étape 1. En continuation, l'exhaustivité du « déjà livré » est le cœur de la valeur anti-régression — n'abrège pas.
- **§4 Roadmap** : phases ordonnées, chacune avec sa criticité. Marque clairement les **forks à arbitrer avec l'utilisateur** (« À arbitrer avec moi »).
- **§5 Patterns non négociables** : choisis dans la bibliothèque de garde-fous de `conventions.md` ceux qui s'appliquent au domaine, et ajoute les spécifiques (ex. tokens OAuth chiffrés AES-GCM, sync incrémental, reshape allowlist-by-construction).
- **§8 Pièges récurrents** : en genèse, amorce avec les pièges connus de la stack choisie (Docker volume figé, OIDC redirect, CI minutes, etc.). En continuation, reprends ceux de `CLAUDE.md §8`.
- **§10** : action concrète et immédiate, pas une généralité.

Écris en **français**, à l'**impératif**, dense. Pas de remplissage, pas de flatterie.

---

## Étape 4 — Sortie

Écris le prompt dans un fichier Markdown (ex. `<nom-projet>-prompt-<mode>.md`) et présente-le. Termine par une note courte : les `<À CONFIRMER>` restants et les forks laissés ouverts exprès. Pas de long laïus — l'utilisateur ouvre le fichier.

---

## Ce qui distingue un bon prompt (auto-contrôle avant de livrer)

- La stack est-elle assez précise pour bloquer la dérive (versions, flags, « NE PAS DÉVIER ») ?
- En continuation : l'agent saura-t-il exactement quoi NE PAS refaire ?
- Chaque phase a-t-elle une criticité ? Les actions destructives/prod sont-elles en critique (3 vérificateurs) ?
- Les garde-fous secrets/anti-fuite sont-ils présents si le projet manipule des credentials ?
- Le style de comm de l'utilisateur est-il repris tel quel (§9) ?
- La §10 est-elle une action concrète exécutable tout de suite ?

---

## Références

- `references/template.md` — le squelette 11 sections à remplir (avec guidage par section + différences genèse/continuation).
- `references/conventions.md` — les blocs constants et la bibliothèque de garde-fous réutilisables, + les défauts d'infra de l'utilisateur.
- `references/example-central-control-continuation.md` — exemple or, **mode continuation** (projet mûr, session N+1).
- `references/example-trakii-genese.md` — exemple or, **mode genèse** (projet neuf à bootstrapper).
