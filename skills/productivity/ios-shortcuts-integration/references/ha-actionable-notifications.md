# Home Assistant Todo + iOS Push Notifications Actionnables

## Architecture

```
Hermes Agent → MCP HA → todo.add_item(entity_id="todo.rappel")
                                          ↓
                   Automation 🔔 Rappel - Nouvel item
                    (state trigger on todo.rappel)
                                          ↓
                   notify.mobile_app_iphone_du_zef
                    (push notification + actions array)
                                          ↓
                   Utilisateur iOS reçoit la notification
                    ┌─────────────────┬─────────────────┐
                    │ ✅ Terminé       │ ⏰ Pas encore   │
                    └─────────────────┴─────────────────┘
                                          ↓
                   Automation 🔔 Rappel - Boutons action
                    (event trigger: mobile_app_notification_action)
                    ┌ TERMINE → todo.update_item(status=completed)
                    └ PAS_ENCORE → delay 1h → re-notify
```

## Prérequis

- HA Companion App installée sur l'iPhone (créé le service `notify.mobile_app_iphone_du_zef`)
- L'iPhone doit être autorisé dans les notifications HA
- Todo list HA créée via l'UI (Shopping List → Ajouter une liste, par ex. « Rappels »)
- MCP HA accessible depuis Hermes (ha-mcp server configuré dans config.yaml)

## Création de la liste todo

Ne pas essayer de créer une entité todo via l'API MCP — les todo lists se créent via le config flow (UI HA uniquement) :

**Paramètres → Périphériques & Services → Shopping List → + → nommer la liste**

L'entité apparaît alors comme `todo.<nom>`.

## Automations YAML (format exact qui fonctionne)

### Automation notification push

```yaml
alias: 🔔 Rappel - Nouvel item
description: Notification push avec boutons Fait / Pas encore
triggers:
  - entity_id: todo.rappel
    trigger: state
actions:
  - action: todo.get_items
    response_variable: todo_data
    target:
      entity_id: todo.rappel
  - variables:
      item_name: "{{ todo_data['todo.rappel']['items'][0]['summary'] | default('') }}"
  - action: notify.mobile_app_iphone_du_zef
    data:
      data:
        actions:
          - action: TERMINE
            title: "✅ Fait"
          - action: PAS_ENCORE
            title: "⏰ Pas encore"
        tag: rappel
      message: "{{ item_name }}"
      title: "📋 Rappel"
mode: single
```

⚠️ **`response_variable: todo_data`** — NE PAS utiliser `items` comme nom (conflit Jinja2).
⚠️ **Les noms `TERMINE`/`PAS_ENCORE`** génèrent des warnings HA ("not found in service registry") — normaux, ce sont des chaînes libres.
⚠️ **`push.category`** peut bloquer l'affichage des boutons → le supprimer si les boutons n'apparaissent pas.

### Automation boutons d'action

```yaml
alias: 🔔 Rappel - Boutons action
description: Gère les boutons selon action
triggers:
  - event_type: mobile_app_notification_action
    trigger: event
actions:
  - alias: Choisir action
    choose:
      - conditions:
          - condition: template
            value_template: "{{ trigger.event.data.action == 'TERMINE' }}"
        sequence:
          - action: todo.get_items
            response_variable: todo_data
            target:
              entity_id: todo.rappel
          - variables:
              item_name: "{{ (todo_data['todo.rappel'].items | last).summary | default('') }}"
          - action: todo.update_item
            data:
              item: "{{ item_name }}"
              status: completed
            target:
              entity_id: todo.rappel
      - conditions:
          - condition: template
            value_template: "{{ trigger.event.data.action == 'PAS_ENCORE' }}"
        sequence:
          - action: todo.get_items
            response_variable: todo_data
            target:
              entity_id: todo.rappel
          - variables:
              item_name: "{{ (todo_data['todo.rappel'].items | last).summary | default('') }}"
          - delay:
              hours: 1
          - action: notify.mobile_app_iphone_du_zef
            data:
              data:
                actions:
                  - action: TERMINE
                    title: "✅ Fait"
                  - action: PAS_ENCORE
                    title: "⏰ Pas encore"
              message: "🔔 Rappel: {{ item_name }}"
              title: "📋 Rappel (relance)"
mode: single
```

## Exemples d'usage

| Ce que tu dis | Ce que je fais |
|--------------|---------------|
| « Rappelle-moi d'acheter du pain » | `todo.add_item(entity_id="todo.rappel", item="Acheter du pain")` |
| « Ajoute le lait aux courses » | `todo.add_item(entity_id="todo.liste_dachats", item="Lait")` |
| « Rappelle-moi de nettoyer le garage demain » | `todo.add_item(entity_id="todo.rappel", item="Nettoyer garage - demain")` |
| « Marque le pain comme fait » | `todo.update_item(item="Acheter du pain", status="completed")` |

## iOS 27+ — Alternative directe créant des Rappels iOS natifs

Depuis iOS 27 (juin 2026), l'app **Raccourcis** a un nouveau déclencheur : **Notification** (Automatisations). Il détecte les notifications d'une app spécifique et lance n'importe quel shortcut — y compris **Ajouter un rappel** (iOS Reminders natif).

### Configuration (iPhone)
1. Raccourcis → Automatisation → **+** → **Notification**
2. App : **Home Assistant**
3. (Optionnel) Filtre : Titre contient `📋 Rappel`
4. Ajouter action : **Ajouter un rappel** (Reminders natif iOS)
5. Variable « Message de la notification » → Titre du rappel

✅ **Avantage** : crée des vrais rappels iOS synchronisés iCloud, Apple Watch, Mac.
⚠️ Beta DB1 (juin 2026) : filtrage cassé → se déclenche sur toutes les notifs HA.
⚠️ iOS 27+ requis.

## Alternative : Pont Microsoft ToDo

Si l'utilisateur a un compte Microsoft (Outlook/Hotmail) :
1. HA : installer l'intégration O365 (HACS) → connecter Microsoft ToDo
2. iPhone : Réglages → Rappels → Comptes → Ajouter Microsoft Exchange/Outlook
3. Résultat : les tâches HA apparaissent dans les Rappels iOS natifs via sync Exchange

**Flux :** Hermes → HA O365 → Microsoft ToDo API → sync Exchange → Rappels iOS ✅

⚠️ Nécessite compte Microsoft. Sync pas instantanée (quelques minutes).

## Pièges et solutions

| Problème | Cause | Solution |
|----------|-------|----------|
| `builtin_function_or_method` error | `items` réservé Jinja2 (méthode `dict.items()`) | Utiliser `todo_data` comme `response_variable` |
| `list object has no element 0` | Liste vide (trigger sur remove) | Template `| default('')` + condition d'augmentation |
| Boutons pas visibles dans notif iOS | `push.category` bloque les inline actions | Supprimer `push.category` / tout le bloc `push` |
| Boutons pas visibles (toujours) | Emojis dans `title` des actions | Tester sans emoji : `"Fait"` au lieu de `"✅ Fait"` |
| Warnings HA validation | Noms arbitraires dans `actions[]` | Ignorer — c'est normal (chaînes libres iOS) |
| 500 API `above` incondition | Template dans `numeric_state.above` | Utiliser template condition séparée ou omettre le filtre |
| Pas de rappels iOS natifs | Apple a supprimé CalDAV Reminders depuis iOS 13 | Impossible. Use notifications HA actionnables ou iOS 27+ |

## Vérification

```bash
# Vérifier que les automatisations sont actives
ha_search(query="Rappel", domain_filter="automation")
# → state: "on" pour les 2 automatisations

# Vérifier une trace d'exécution
ha_get_automation_traces(automation_id="automation.rappel_nouvel_item")
# → execution: "finished" = notification envoyée

# Ajouter un item test
ha_call_service(domain="todo", service="add_item",
  entity_id="todo.rappel", data={"item": "Test notification"})
# → state passe de N à N+1
```
