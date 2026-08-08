# Multi-user Jellyfin — filtrer par user dans CrossWatch

CrossWatch se connecte à Jellyfin via un **token utilisateur**. Si le token est celui d'un **admin**, CrossWatch voit TOUS les utilisateurs de Jellyfin — leur historique, leur watchlist, leur progress. C'est pourquoi le sync pousse tout le monde vers les trackers (Trakt, SIMKL, etc.).

## Diagnostic rapide

**Symptôme :** l'utilisateur voit du contenu qu'il n'a pas regardé apparaître sur ses trackers.

**Vérification :**
- Lister les profils Jellyfin : `list_provider_instances(provider="JELLYFIN")`
- Vérifier dans l'UI CrossWatch → Settings → Jellyfin → **User ID** correspond bien à SON user, pas un admin
- Un admin Jellyfin a accès global aux données de tous les users du serveur
- Un token généré avec son propre username/password est scopé à son user uniquement

## Alternative A : Créer des profils Jellyfin dédiés par utilisateur

CrossWatch supporte les **provider instances** (profils). Chaque profil Jellyfin a son propre user/token.

### Étapes (dans l'UI CrossWatch)

1. **Settings → Connections → Authentication → Jellyfin**
2. Créer un **nouveau profil** (bouton "New" à côté du sélecteur "Profile")
   - Server URL : l'URL de ton serveur Jellyfin
   - Username : **Réfé** (ou l'user que tu veux sync)
   - Password : son mot de passe (CrossWatch génère un token, ne stocke pas le password)
3. **Sauvegarder** le profil
4. **Settings → Synchronization → Pairs**
5. Éditer chaque paire (JELLYFIN → TRAKT, JELLYFIN → SIMKL, etc.)
6. Dans le panneau source (Jellyfin), changer le **profil** de `default` vers le nouveau profil créé pour Réfé
7. **Sauvegarder** et **Run** la paire

## Alternative B : Créer un utilisateur Jellyfin dédié NON-admin (quand il n'y a qu'un seul compte)

**Cas typique** : l'utilisateur a un seul compte Jellyfin qui est **admin**. Même s'il n'y a qu'un seul user, le token admin donne accès aux API globales de Jellyfin, et CrossWatch peut récupérer des données au-delà du simple historique utilisateur (config serveur, stats globales, users list, etc.).

**Solution** : créer un **nouvel utilisateur Jellyfin non-admin** dédié à CrossWatch :

1. **Dashboard Jellyfin** → Users → **Add User** → créer un nouveau compte (ex: `janitorr` ou `crosswatch-bot`)
   - **Ne PAS** cocher "Admin"
   - Donner accès aux bibliothèques souhaitées
2. **CrossWatch → Settings → Connections → Authentication → Jellyfin**
   - Modifier le profil `default` (ou en créer un nouveau)
   - Mettre le nouveau **username** + **password** (non-admin)
   - Cliquer **Sign In** → Auto-Fetch le **User ID**
   - **Sauvegarder**
3. **Passer les paires en One-way** (recommandé pour éviter que le contenu des trackers ne revienne)

**Résultat** : le token non-admin est scopé à ce seul utilisateur → CrossWatch ne voit que son historique. Plus de contenu non-regardé qui apparaît sur les trackers.

**⚠️ Attention** : si tu changes le user Jellyfin du profil `default`, les données en cache sont encore celles de l'ancien compte admin. Faire **Clear State + Clear Cache** dans **Settings → Maintenance**, puis relancer un sync pour repartir propre.

### Résultat

- Seul l'historique de **Réfé** est lu sur Jellyfin
- Les trackers ne reçoivent que les données de Réfé
- Les autres users Jellyfin sont ignorés

## Backfill : copier l'historique des trackers vers le nouveau user Jellyfin

**Problème** : après avoir créé un nouveau user Jellyfin non-admin, son historique est **vide** (0 épisodes regardés). Les paires en one-way JELLYFIN → trackers n'ont rien à pousser.

**Solution** : créer une **paire temporaire** TRAKT → JELLYFIN (one-way, history only) pour copier l'historique des trackers dans le nouveau user Jellyfin.

### Workflow complet (API directe via httpx sur localhost:8787)

```python
import httpx
h = {"Content-Type": "application/json", "Cookie": "cw_auth=..."}
b = "http://localhost:8787"

# 1. Créer la paire temporaire TRAKT → JELLYFIN (history only, one-way)
pair_body = {
    "source": "TRAKT",
    "target": "JELLYFIN",
    "source_instance": "default",
    "target_instance": "default",
    "mode": "one-way",
    "enabled": True,
    "features": {
        "history": {"enable": True, "add": True, "remove": False}
    }
}
r = httpx.post(f"{b}/api/pairs", headers=h, json=pair_body, timeout=10)
# → {"ok": true, "id": "pair_..."}

# 2. Lister les paires pour trouver les IDs
pairs = httpx.get(f"{b}/api/pairs", headers=h, timeout=5).json()
for p in pairs:
    print(f"{p['id']}: {p['source']}({p.get('source_instance','default')}) "
          f"→ {p['target']}({p.get('target_instance','default')}) mode={p['mode']}")

# 3. Passer les paires JELLYFIN→tracker en one-way
pid_jftrakt = "pair_..."  # JELLYFIN → TRAKT
httpx.put(f"{b}/api/pairs/{pid_jftrakt}", headers=h, json={"mode": "one-way"}, timeout=5)

# 4. Clean state + cache
httpx.post(f"{b}/api/maintenance/clear-state", headers=h, timeout=10)
httpx.post(f"{b}/api/maintenance/clear-cache", headers=h, timeout=10)

# 5. Lancer le sync
httpx.post(f"{b}/api/run", headers=h, json={"label": "Backfill depuis Trakt"}, timeout=10)

# 6. Surveiller la progression
summary = httpx.get(f"{b}/api/run/summary", headers=h, timeout=5).json()
logs = httpx.get(f"{b}/api/logs/dump?channel=SYNC&n=5", headers=h, timeout=5).json()
```

### Ce qui se passe pendant le backfill

| Phase | Log | Signification |
|-------|-----|---------------|
| Snapshot | `snapshot:progress dst=TRAKT done=X/total` | Lit l'historique Trakt (X/3263 items) |
| Plan | `one:plan src=TRAKT dst=JELLYFIN adds=3173` | Calcule ce qu'il faut écrire (3173 items nouveaux) |
| Apply | `apply:add:progress dst=JELLYFIN done=X/total ok=true` | Écrit dans Jellyfin (X/3173 faits) |
| Apply | `apply:unresolved provider=JELLYFIN count=N` | Items dans Trakt mais absents de la biblio Jellyfin — normal |

### ⏱️ Temps et progression du backfill

Le backfill de ~3000 items prend **10-15 minutes** de phase apply. Points importants :

- **`_phase.apply.done` reste à 0** dans `summary` pendant toute la durée du sync — c'est normal. Vérifier la vraie progression dans les logs SYNC :
  ```python
  logs = httpx.get(f"{b}/api/logs/dump?channel=SYNC&n=5", headers=h, timeout=5).json()
  # Chercher "apply:add:progress done=X"
  ```
- **`provider_counts` (JELLYFIN) reste à 0** tant que le sync n'est pas terminé. Ne pas paniquer.
- **Ratio ~5 items/seconde** : 100 items par ~20s, c'est le rythme normal d'écriture Jellyfin.

### 🔄 Orchestrateur séquentiel

Le sync `orchestrator` traite **toutes les paires l'une après l'autre**, dans l'ordre où elles sont configurées :

1. **TRAKT → JELLYFIN** (backfill, 3173 history items) → 10-15 min
2. **JELLYFIN → TRAKT** (one-way, avec historique maintenant dans Janitorr)
3. **JELLYFIN → SIMKL** (idem)
4. **JELLYFIN → MDBLIST** (idem)
5. ...etc

**Conséquence** : après la fin de la 1ère paire, les paires JELLYFIN→tracker s'exécutent avec les données fraîchement écrites. C'est normal de voir plusieurs phases apply successives avec des totaux différents. **Tant que le sync tourne, ne pas relancer.**

### ✅ Post-backfill (sync terminé)

1. **Vérifier que c'est fini** : `summary.get('finished_at')` non null
2. **Vérifier les counts finaux** : `GET /api/sync/providers/counts?source=state` → JELLYFIN > 0
3. **Supprimer la paire temporaire** TRAKT → JELLYFIN :
   ```python
   httpx.delete(f"{b}/api/pairs/pair_...?purge_state=false", headers=h, timeout=5)
   ```
4. Le sync final aura : JELLYFIN (user non-admin, avec historique) → TRAKT/SIMKL/MDBLIST/ANILIST en **one-way**
5. Plus rien ne revient des trackers

## Alternative : Library Whitelisting

Si Réfé a ses **propres bibliothèques** dédiées sur Jellyfin (pas de librairies partagées), tu peux aussi :

1. **Settings → Connections → Authentication → Jellyfin**
2. Section **Whitelisting**
3. **Load Libraries** → sélectionner uniquement les librairies de Réfé
4. Sauvegarder

Ça filtre par bibliothèque, pas par user. Moins précis que des profils séparés si plusieurs users partagent les mêmes librairies.

## Vérification

- `list_provider_instances(provider="JELLYFIN")` → liste les profils disponibles
- `list_pairs()` → montre quels profils sont utilisés par chaque paire
- Les logs SYNC montrent `[JELLYFIN:user_id]` → confirme quel user est lu
