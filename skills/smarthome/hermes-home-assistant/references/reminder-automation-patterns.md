# HA Reminder / Notification Automation Patterns

Conception de rappels programmés dans Home Assistant, centralisés et sans duplication d'automatisations.

## Le problème

Un système naïf où chaque ajout à `todo.rappel` déclenche une notification **immédiate** via `trigger: state` ne permet pas de programmer un rappel pour une date/heure future (ex: « rappelle-moi de X demain à 8h »).

## Principe général : 1 automation centrale, N items avec date

**NE PAS** créer une automation par rappel — l'utilisateur ne veut pas 15 automations dans son interface.

Les items `todo` supportent nativement `due_datetime` (testé OK). Le champ `due` est retourné par `todo.get_items`.

## Approche A — Polling centralisé (mise en œuvre immédiate)

Une seule automation + un script, avec `time_pattern` toutes les minutes.

### Script de vérification (`script.verifier_rappels`)

```yaml
alias: "⏰ Vérificateur de rappels"
description: "Lit les items en attente dans todo.rappel, notifie ceux dont due correspond à maintenant"
mode: single
sequence:
  - action: todo.get_items
    target:
      entity_id: todo.rappel
    response_variable: todos
  - variables:
      items_avec_date: "{{ todos['todo.rappel'].items | selectattr('due', 'defined') | list }}"
  - repeat:
      for_each: "{{ items_avec_date }}"
      sequence:
        - variables:
            item_due: "{{ repeat.item.due | as_datetime }}"
            now_ts: "{{ now().timestamp() }}"
        - if:
            - condition: template
              value_template: >
                {{ item_due and item_due.timestamp() > now_ts - 60
                   and item_due.timestamp() < now_ts + 60 }}
          then:
            - action: notify.mobile_app_iphone_du_zef
              data:
                title: "⏰ Rappel programmé"
                message: "{{ repeat.item.summary }}"
                data:
                  actions:
                    - action: TERMINE
                      title: "✅ Fait"
                    - action: PAS_ENCORE
                      title: "⏰ Pas encore"
                  tag: "rappel_{{ repeat.item.uid }}"
                  persistent: true
            - action: todo.update_item
              target:
                entity_id: todo.rappel
              data:
                item: "{{ repeat.item.uid }}"
                status: completed
```

### Automation d'appel

```yaml
alias: "⏰ Vérificateur de rappels - Déclencheur"
description: "Déclenche la vérification des rappels toutes les minutes"
triggers:
  - trigger: time_pattern
    minutes: "/1"
actions:
  - action: script.verifier_rappels
```

### Mode opératoire

1. L'utilisateur dit « rappelle-moi de X [date/heure] »
2. J'ajoute l'item avec `due_datetime` (et aussi dans `todo.rappel` pour garder la trace)
3. L'automation centrale tourne toutes les minutes
4. Quand `due` match l'heure courante → notification push + marque `completed`

### Pour les rappels immédiats (sans date)

Garder l'automation existante sur `trigger: state` de `todo.rappel`, mais la modifier avec une condition qui **saute** si l'item a un `due_datetime` (sinon doublon avec le vérificateur).

## Approche B — Calendar Trigger (sans polling, setup préalable requis)

HA a un `trigger: calendar` natif qui se déclenche **exactement** au `start` d'un événement calendrier — zéro polling.

### Setup requis

1. Ajouter l'intégration **Local Calendar** dans HA (Settings → Devices & Services → Ajouter → Local Calendar, un clic)
2. Créer un calendrier `calendar.rappels`
3. Créer l'automation :

```yaml
alias: "🔔 Rappel calendrier"
description: "Se déclenche au début d'un événement dans le calendrier Rappels"
triggers:
  - trigger: calendar
    entity_id: calendar.rappels
    event: start
actions:
  - action: notify.mobile_app_iphone_du_zef
    data:
      title: "⏰ Rappel"
      message: "{{ trigger.calendar_event.summary }}"
      data:
        actions:
          - action: TERMINE
            title: "✅ Fait"
          - action: PAS_ENCORE
            title: "⏰ Pas encore"
        tag: "rappel_cal"
        persistent: true
```

4. Quand l'utilisateur demande un rappel, je crée un événement dans `calendar.rappels` avec :
   - `summary` = le texte du rappel
   - `start_date_time` = la date/heure choisie
   - `end_date_time` = 1 minute plus tard (événement très court)
   - Également ajouter à `todo.rappel` pour garder une trace écrite

### Avantages du Calendar Trigger
- **Zéro polling** — HA notifie uniquement quand un événement commence
- **Zéro création d'automations** — une seule automation à vie
- **Visuel** — les rappels apparaissent dans le calendrier HA

## Points clés validés techniquement

| Capacité | Statut |
|---|---|
| `todo.add_item` avec `due_datetime` | ✅ OK |
| `todo.get_items` retourne `due` | ✅ OK |
| `todo.update_item` avec `status: completed` | ✅ OK |
| `trigger: calendar` sur `event: start` | ✅ HA natif |
| `calendar.create_event` avec `start_date_time` | ✅ OK |

## Piège à éviter

**NE PAS** créer une automation de rappel par item. L'utilisateur a explicitement refusé cette approche (« si j'ai 15 rappels, on va se retrouver avec 15 automatisations »).
