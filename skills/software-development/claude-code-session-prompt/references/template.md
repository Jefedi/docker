# Gabarit — Prompt de session (11 sections)

Remplis chaque section. `[…]` = guidage à remplacer. Les blocs marqués **(CONSTANT)** se reprennent quasi verbatim depuis `conventions.md`.

---

```markdown
# [Nom du projet] — Prompt de [genèse | continuation] (session [N])

> [1-2 phrases : nature du projet, ce qu'il fait, hébergement, domaine, auth, utilisateur unique.]
>
> [GENÈSE uniquement] ⚠️ Ceci est la session de genèse. Le repo est vide. Les fichiers cités en §1 n'existent PAS encore : ta Phase 0 est de les créer.
>
> 🔧 Valeurs à confirmer avant de lancer (remplacer les <...>) : [domaine, slug/branche, repo GitHub, instances existantes…].

## 0. Identité et rôle
[(CONSTANT) Bloc rôle manager : "Tu n'es PAS un développeur solo, tu es le manager…" + workflow 8 étapes (spec → criticité → délègue → vérifie N sous-agents indépendants → collecte rapports → arbitre → commit/push branche → update CLAUDE.md) + "Je juge sur le résultat, pas le processus" + Auto Mode + déclencheurs d'intervention. Adapter seulement le nom du projet, le domaine, le node d'hébergement et le nom de branche.]

## 1. Lecture obligatoire au démarrage (DANS L'ORDRE)
[(CONSTANT, adapter la liste) CLAUDE.md → docs/architecture.md → docs/PROMPT_ARCHITECTURE.md → docs/decisions/ADR → spec courante. Préciser que les sous-agents doivent lire dans cet ordre + leur charter + la spec.]
[GENÈSE : préfixer "ces fichiers n'existent pas encore → la Phase 0 les crée ; dès la session 2, les lire avant toute action".]

## 2. Stack figée (NE PAS DÉVIER)
[Liste précise et opiniâtre, par couche. Versions, flags (ex. TS strict : noUncheckedIndexedAccess, verbatimModuleSyntax, zéro any), outils (gestionnaire de paquets, lint, tests, validation aux boundaries), DB, runtime backend, frontend, CI, conteneurisation, exposition réseau, sécurité transverse. Piocher les défauts d'infra dans conventions.md. Tout ce qui n'est pas figé = porte ouverte à la dérive.]

## 3. État actuel
[CONTINUATION : liste EXHAUSTIVE de ce qui est livré, regroupé par phase, avec "NE PAS REFAIRE". Inclure les patterns déjà établis et les stats (commits, tests passés, garde-fous accumulés). C'est le cœur anti-régression — ne pas abréger.]
[GENÈSE : "Repo vide. Rien livré." + liste précise du bootstrap à produire en Phase 0 (monorepo, Docker compose, Dockerfiles, CLAUDE.md, docs/architecture.md, ADR, charters agents/, scaffolding packages, CI squelette, première migration/schéma, spec phase-0).]

## 4. [Ce qui reste — phases prioritaires | Roadmap]
[Phases ordonnées. Chaque phase : objectif, livrables concrets, ET sa criticité (trivial/normal/critique). Marquer explicitement les forks "À arbitrer avec moi" (décisions structurantes où la direction au manager serait risquée). Une section "Backlog / plus tard" pour le hors-scope immédiat. Penser aux intégrations transverses de l'utilisateur (ex. notifs → HA notify_central).]

## 5. Patterns NON NÉGOCIABLES (à reproduire)
[Choisir dans la bibliothèque de garde-fous de conventions.md ceux qui s'appliquent, + spécifiques au domaine. Typiquement : gestion secrets (chiffrement au repos, jamais loggés, assertNoSecretsLeak), reshape allowlist-by-construction sur toute payload forwardée au client, chaîne de handler entièrement auditée, mutations destructives (confirmation armée + defaults safe + snapshot avant), optimistic UI + revert, polling visibilitychange-aware, idempotence des écritures, client d'API rate-limit aware, tests de non-régression critiques.]

## 6. Workflow de validation par criticité (ADR 0002)
[(CONSTANT) Table : Trivial = 1 constructeur / 1 vérificateur (qa-logic) ; Normal = 1 / 2 (qa-logic + domaine) ; Critique = 1 / 3 (qa-logic + security-reviewer + db-reviewer si DB). Exemples par niveau. + liste des charters sous-agents dans agents/ + mention du type natif general-purpose. Adapter les exemples au domaine du projet.]

## 7. Commandes utiles
[Bloc commandes réelles : dev (tout via Docker compose), typecheck/lint/test, migrations/typegen, build/CI spécifique (ex. iOS), git (status, log, push sur la branche). Adapter à la stack.]

## 8. Pièges récurrents (toujours vérifier)
[GENÈSE : amorcer avec les pièges connus de la stack choisie (ex. volume node_modules conteneur figé après ajout de dep, OIDC redirect URI exact, deep link OAuth mobile, minutes runner macOS coûteuses, IPA non signé pour SideStore, secrets en CI, junctions Windows + pnpm sur jTower…).]
[CONTINUATION : reprendre la liste de CLAUDE.md §8 et l'enrichir.]

## 9. Style de communication avec moi
[(CONSTANT) Direct, sans flatterie. Annoncer la direction avant de partir. Statut aux checkpoints (livraison sous-agent, validation, commit, push). Récap + checklist quand l'utilisateur teste live. "ça marche" → enchaîner ; "ça marche pas" → reproduire, isoler, fix ciblé, ne pas relancer le builder à l'aveugle. Pas de question si devinable ; question uniquement pour les forks structurants.]

## 10. Première action de cette session
[Action concrète et immédiate, pas une généralité.]
[GENÈSE : confirmer les <...> non résolus (sinon défauts + noter dans CLAUDE.md §10) → écrire docs/specs/phase-0.md → créer le scaffolding → lancer qa-logic → commit/push → marquer Phase 0 livrée → enchaîner Phase 1.]
[CONTINUATION : relire CLAUDE.md + spec courante → vérifier via git status si le builder en background a livré → si oui, lancer qa-logic + finaliser (commit/push/update CLAUDE.md) ; si non, patienter et le dire → puis demander la direction de la phase suivante et écrire la spec.]
```

---

## Notes de remplissage

- L'en-tête (titre + blockquote) donne le ton : nature, contraintes, et les `<...>` à remplir.
- Numérotation des ADR cohérente : `0001` stack, `0002` validation multi-agents, `0003` politique propre au domaine (ex. sync, MCP), `0004` Docker-first, `0005` secrets/crypto.
- Nom de branche : `claude/<slug>-<hash>` (hash court généré, ou `<À CONFIRMER>`).
- Garder l'ensemble dense et exécutable : chaque ligne doit soit contraindre, soit informer une action.
