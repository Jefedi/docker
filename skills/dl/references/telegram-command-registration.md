# Hermes Telegram Command Registration — Architecture

Comment Hermes enregistre et dispatch les commandes Telegram slash.

## Pipeline complet

```
User tape /dl <url> sur Telegram
  ↓
telegram.py reçoit Message avec entity_type="bot_command"
  ↓
gateway/run.py: _process_message() → détecte /command
  ↓
1. resolve_command(command) — COMMAND_REGISTRY (built-in Hermes commands)
   → /new, /help, /reload-skills, /restart, etc.
  ↓ si pas trouvé
2. Plugin commandes — get_plugin_commands()
   → PluginContext.register_command()
  ↓ si pas trouvé
3. Skill commandes — get_skill_commands() → resolve_skill_command_key()
   → scanne ~/.hermes/skills/<name>/SKILL.md
   → match sur name: du frontmatter → crée /<slug>
  ↓ si pas trouvé
4. Unrecognized → "Unknown command /X"
```

## Comment les commandes apparaissent dans le menu Telegram

Au **démarrage du gateway** uniquement, `telegram.py` appelle :

```python
from hermes_cli.commands import telegram_menu_commands
menu_commands, hidden_count = telegram_menu_commands(max_commands=100)
bot_commands = [BotCommand(name, desc) for name, desc in menu_commands]

# 3 scopes
for scope_cls in (BotCommandScopeDefault, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats):
    await bot.set_my_commands(bot_commands, scope=scope_cls())
```

`telegram_menu_commands()` combine (dans l'ordre) :
1. **Core CommandDef** de `COMMAND_REGISTRY` (toujours inclus)
2. **Plugin slash commands** (jamais rognés)
3. **Built-in skill commands** (rognés si > 100, par ordre alpha)

Les skills hub sont exclus. Les skills désactivés par platform sont exclus.

## Comment les skills deviennent des commandes

`get_skill_commands()` → `scan_skill_commands()` :

```python
# Pour chaque ~/.hermes/skills/*/SKILL.md:
content = skill_md.read_text()
frontmatter, body = _parse_frontmatter(content)
name = frontmatter.get('name', skill_md.parent.name)

# Normalisation:
cmd_name = name.lower().replace(' ', '-').replace('_', '-')
# Nettoie les caractères invalides
cmd_name = re.sub(r'[^a-z0-9-]', '', cmd_name)
# Comprime les doubles tirets
cmd_name = re.sub(r'-{2,}', '-', cmd_name).strip('-')

_skill_commands[f"/{cmd_name}"] = {
    "name": name,
    "description": description,
    "skill_md_path": str(skill_md),
    "skill_dir": str(skill_md.parent),
}
```

**Important** : Le `name:` du frontmatter est la source de vérité pour le nom de commande.

## Cache et mise à jour

- `_skill_commands` est un **cache global** dans `agent/skill_commands.py`
- Initialisé au premier appel de `get_skill_commands()` (au démarrage gateway)
- `/reload-skills` invoque `reload_skills()` qui `scan_skill_commands()` à nouveau → met à jour le cache
- **Le menu Telegram (set_my_commands) n'est PAS mis à jour** par `/reload-skills`. Il faut un restart gateway pour que le menu affiche les nouvelles commandes.
- MAIS le dispatch des commandes (quand l'user tape `/dl` dans le chat) utilise `get_skill_commands()` avec le cache **fraîchement rescanné** → `/reload-skills` suffit pour que la commande soit reconnue et dispatchée, même si le menu Telegram est pas à jour.

## Dispatch d'une skill commande

Dans `gateway/run.py`, vers ligne 7760 :

```python
from agent.skill_commands import (
    get_skill_commands,
    build_skill_invocation_message,
    resolve_skill_command_key,
)

skill_cmds = get_skill_commands()
cmd_key = resolve_skill_command_key(command)  # "dl" → "/dl"

if cmd_key:
    user_instruction = event.get_command_args().strip()
    msg = build_skill_invocation_message(cmd_key, user_instruction)
    if msg:
        event.text = msg
        # Fall through — le message est envoyé à l'agent
        # avec le contenu du skill comme instruction
```

`build_skill_invocation_message()` charge le SKILL.md, construit un message formaté avec le contenu du skill, et le définit comme `event.text`. L'agent reçoit ce message comme un message utilisateur normal.

## Underscore vs Hyphen (Telegram compat)

Telegram interdit les `-` dans les noms de commandes BotCommand. Quand une commande skill a un tiret (ex: `gif-search`), Telegram enregistre le `BotCommand` comme `gif_search`. Au dispatch, `resolve_skill_command_key("gif_search")` remplace `_` par `-` → `/gif-search` → match.

## setMyCommands override

Quand le gateway démarre, il appelle `set_my_commands()` pour TOUS les scopes. Ça **remplace** toute liste de commandes définie manuellement via l'API Telegram Bot. Donc définir des commandes via `setMyCommands` manuellement est inutile — Hermes les override au prochain démarrage.

## Résumé workflow pour ajouter une commande

1. Créer `~/.hermes/skills/<name>/SKILL.md` avec `name: <name>` dans le frontmatter
2. Le skill contient les instructions pour l'agent sur quoi faire quand /name est tapé
3. **Gateway restart** ou **`/reload-skills`** dans Telegram
4. `/reload-skills` suffit pour que la commande soit dispatchée, restart pour le menu
