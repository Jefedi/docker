# pyicloud — Accès iCloud natif depuis Linux

## Installation

```bash
pip install pyicloud
# Ou avec CLI :
pip install pyicloud[cli]
```

Repo principal : github.com/picklepete/pyicloud (2.8k ⭐)
Fork actif : github.com/timlaing/pyicloud — version 2.6.5 (juin 2026)

## Authentification

### 2FA obligatoire
Apple exige la double authentification. Au premier login :

```python
from pyicloud import PyiCloudService
api = PyiCloudService('user@apple.id', 'password')
if api.requires_2fa:
    code = input("Code 2FA : ")
    result = api.validate_2fa_code(code)
    # Le device doit être approuvé une fois
```

Le token de session persiste dans `~/.pyicloud/`. Apple peut demander une re-authentification périodiquement.

## Rappels — API Python

### Lister
```python
reminders = api.reminders
for lst in reminders.lists():
    print(f"Liste: {lst.title} (id: {lst.id})")
    for r in lst.reminders():
        print(f"  - {r.title} (completed: {r.completed})")
```

### Créer
```python
from datetime import datetime, timedelta, timezone

target_list = next(iter(reminders.lists()), None)
created = reminders.create(
    list_id=target_list.id,
    title="Payer la facture",
    desc="Facture électricité",
    due_date=datetime.now(timezone.utc) + timedelta(days=1),
    priority=1,
    flagged=True,
)
```

### Modifier / Marquer terminé
```python
created.desc = "2 percent organic"
created.completed = True
reminders.update(created)
```

### Supprimer
```python
fresh = reminders.get(created.id)
reminders.delete(fresh)
```

## Rappels — CLI

```bash
# Lister
icloud reminders list --username user@apple.id

# Créer
icloud reminders create --username user@apple.id --list-id INBOX --title "Buy milk"

# Modifier
icloud reminders update REMINDER_ID --username user@apple.id --title "Buy oat milk"

# Marquer terminé
icloud reminders set-status REMINDER_ID --username user@apple.id --completed

# Supprimer
icloud reminders delete REMINDER_ID --username user@apple.id
```

## Calendrier (lecture seule)

```python
from datetime import datetime
events = api.calendar.events(
    from_dt=datetime(2026, 7, 1),
    to_dt=datetime(2026, 7, 31)
)
for event in events:
    print(event.get('title'), event.get('startDate'))
```

⚠️ L'écriture d'events calendrier est en PR (pas encore mergé). Pour sync calendrier bidirectionnelle, utiliser Radicale (CalDAV).

## Limitations connues

1. **2FA** : validation initiale requise sur un device Apple
2. **Privacy** : données transitent par les serveurs Apple (pas self-hosted)
3. **Stabilité API** : Apple peut casser l'API sans prévenir — le fork timlaing corrige vite
4. **Notes** : accès partiel, pas d'écriture
5. **Calendrier écriture** : pas encore disponible en stable

## Intégration avec Hermes

Hermes peut utiliser pyicloud pour créer des rappels iCloud natifs :

```
Utilisateur : "Rappelle-moi de payer la facture demain"
    ↓
Hermes → pyicloud → reminders.create(title="Payer la facture", due_date=tomorrow)
    ↓
Rappel apparaît instantanément dans l'app Rappels sur iPhone/iPad/Mac (sync iCloud)
```

Aucun raccourci à créer, aucune app à installer côté iPhone. Le rappel se sync naturellement via iCloud.